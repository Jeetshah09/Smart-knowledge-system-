"""One-time data migration for existing MongoDB rows.

Run from the backend folder:
    .venv/Scripts/python scripts/migrate_model_aliases.py

What it fixes:
1. user_settings.default_model: legacy/raw values ('gemini', 'gemini-2.0-flash',
   'gemini-flash-latest', ...) -> provider-neutral aliases ('balanced', ...).
2. prompts.model: legacy raw model IDs -> provider-neutral aliases.
3. generated_content.resource_ids: string ids -> real ObjectIds so the field
   is consistent with every other reference stored in the database.

Safe to re-run: already-migrated rows are left untouched.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from bson import ObjectId  # noqa: E402
from bson.errors import InvalidId  # noqa: E402

from app.core.database import (  # noqa: E402
    generated_content_collection,
    prompts_collection,
    user_settings_collection,
)
from app.services.gemini_service import MODEL_ALIASES, alias_for_model  # noqa: E402

# Extra legacy values seen in the wild that should map to a sane alias.
LEGACY_EXTRAS = {
    "gemini": "balanced",
    "gemini-2.0-flash": "balanced",
    "gemini-2.0-flash-lite": "fast",
}


def migrate_settings() -> int:
    changed = 0
    for doc in user_settings_collection().find({}):
        value = doc.get("default_model")
        key = (value or "").strip().lower()
        # Already a valid alias -> nothing to do.
        if key in MODEL_ALIASES:
            continue
        new_value = LEGACY_EXTRAS.get(key) or (
            alias_for_model(value) if value else "balanced"
        )
        user_settings_collection().update_one(
            {"_id": doc["_id"]},
            {"$set": {"default_model": new_value, "updated_at": doc.get("updated_at")}},
        )
        print(f"  user_settings {doc['_id']}: {value!r} -> {new_value!r}")
        changed += 1
    return changed


def migrate_prompts() -> int:
    changed = 0
    for doc in prompts_collection().find({}):
        value = doc.get("model")
        key = (value or "").strip().lower()
        if key in MODEL_ALIASES:
            continue
        new_value = LEGACY_EXTRAS.get(key) or alias_for_model(value)
        prompts_collection().update_one(
            {"_id": doc["_id"]}, {"$set": {"model": new_value}}
        )
        print(f"  prompts {doc['_id']}: {value!r} -> {new_value!r}")
        changed += 1
    return changed


def migrate_generated_content() -> int:
    changed = 0
    for doc in generated_content_collection().find({}):
        ids = doc.get("resource_ids") or []
        if not ids or all(isinstance(r, ObjectId) for r in ids):
            continue  # already ObjectIds (or empty) -> nothing to do
        oids = []
        for rid in ids:
            if isinstance(rid, ObjectId):
                oids.append(rid)
                continue
            try:
                oids.append(ObjectId(str(rid)))
            except (InvalidId, TypeError):
                continue  # drop malformed ids
        generated_content_collection().update_one(
            {"_id": doc["_id"]}, {"$set": {"resource_ids": oids}}
        )
        print(f"  generated_content {doc['_id']}: {len(ids)} string ids -> ObjectIds")
        changed += 1
    return changed


def main() -> None:
    print("Migrating user_settings.default_model ...")
    n1 = migrate_settings()
    print("Migrating prompts.model ...")
    n2 = migrate_prompts()
    print("Migrating generated_content.resource_ids ...")
    n3 = migrate_generated_content()
    print(f"\nDone. {n1} settings, {n2} prompts, {n3} generated_content rows updated.")


if __name__ == "__main__":
    main()
