"""MongoDB health checker - verify every collection is storing data.

Run from the backend folder:
    .venv/Scripts/python scripts/db_health.py

Checks, for all collections:
  1. existence + document count
  2. latest document age (is fresh data arriving?)
  3. required fields present on the newest document
  4. orphaned references (child rows pointing at missing parents)
  5. data-type consistency for key fields (ObjectIds, model aliases)

Exit code 0 = healthy, 1 = problems found.
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from bson import ObjectId  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.database import get_client  # noqa: E402
from app.services.gemini_service import MODEL_ALIASES  # noqa: E402

# Per-collection expectations: required fields on every document.
REQUIRED_FIELDS = {
    "users": ["name", "email", "password_hash", "created_at"],
    "user_settings": ["user_id", "theme", "notifications", "default_model"],
    "notebooks": ["user_id", "title", "created_at", "updated_at"],
    "resources": ["user_id", "notebook_id", "name", "type", "content", "processing_status", "created_at"],
    "conversations": ["user_id", "notebook_id", "title", "created_at"],
    "messages": ["conversation_id", "user_id", "role", "content", "created_at"],
    "generated_content": ["user_id", "notebook_id", "type", "title", "content", "created_at"],
    "prompts": ["user_id", "title", "prompt", "model", "temperature", "created_at"],
    "activity_logs": ["user_id", "action", "created_at"],
}

# Child collection -> (parent collection, child field)
REFERENCES = {
    "user_settings": ("users", "user_id"),
    "notebooks": ("users", "user_id"),
    "resources": ("notebooks", "notebook_id"),
    "conversations": ("notebooks", "notebook_id"),
    "messages": ("conversations", "conversation_id"),
    "generated_content": ("notebooks", "notebook_id"),
    "prompts": ("users", "user_id"),
    "activity_logs": ("users", "user_id"),
}

problems: list[str] = []


def fail(msg: str) -> None:
    problems.append(msg)
    print(f"    [FAIL] {msg}")


def main() -> None:
    client = get_client()
    try:
        client.admin.command("ping")
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] MongoDB not reachable: {exc}")
        sys.exit(1)

    db = client[settings.DATABASE_NAME]
    print(f"Database: {settings.DATABASE_NAME}\n")

    parent_ids: dict[str, set] = {}

    for col, required in REQUIRED_FIELDS.items():
        print(f"[{col}]")
        collection = db[col]
        total = collection.count_documents({})
        if total == 0:
            print("    empty (no documents yet)")
            parent_ids[col] = set()
            continue

        latest = collection.find_one(sort=[("created_at", -1)])
        age_hours = None
        if latest and latest.get("created_at"):
            created = latest["created_at"]
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            age_hours = (datetime.now(timezone.utc) - created).total_seconds() / 3600
            print(f"    docs: {total} | latest: {created.isoformat()} ({age_hours:.1f}h ago)")
        else:
            print(f"    docs: {total} | latest: [no created_at field!]")
            fail(f"{col}: newest document has no created_at")

        # Required fields on the newest doc.
        if latest:
            missing = [f for f in required if f not in latest]
            if missing:
                fail(f"{col}: newest document missing fields {missing}")
            else:
                print("    newest document has all required fields")

        # Orphaned references.
        if col in REFERENCES:
            parent_col, field = REFERENCES[col]
            parents = parent_ids.setdefault(
                parent_col, {d["_id"] for d in db[parent_col].find({}, {"_id": 1})}
            )
            orphans = sum(
                1 for d in collection.find({}, {field: 1}) if d.get(field) not in parents
            )
            if orphans:
                fail(f"{col}: {orphans} document(s) reference missing {parent_col}")
            else:
                print(f"    references -> {parent_col}: OK")

        # Type consistency.
        if col == "generated_content":
            bad = sum(
                1
                for d in collection.find({}, {"resource_ids": 1})
                for r in d.get("resource_ids", [])
                if not isinstance(r, ObjectId)
            )
            if bad:
                fail(f"generated_content: {bad} resource_ids are not ObjectIds")
            else:
                print("    resource_ids are ObjectIds: OK")
        if col == "prompts":
            bad = sum(
                1
                for d in collection.find({}, {"model": 1})
                if d.get("model") not in MODEL_ALIASES
            )
            if bad:
                fail(f"prompts: {bad} document(s) with non-alias model value")
            else:
                print("    model aliases: OK")
        if col == "user_settings":
            bad = sum(
                1
                for d in collection.find({}, {"default_model": 1})
                if d.get("default_model") not in MODEL_ALIASES
            )
            if bad:
                fail(f"user_settings: {bad} document(s) with invalid default_model")
            else:
                print("    default_model aliases: OK")
        print()

    print("=" * 50)
    if problems:
        print(f"RESULT: {len(problems)} problem(s) found")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)
    print("RESULT: all collections healthy")


if __name__ == "__main__":
    main()
