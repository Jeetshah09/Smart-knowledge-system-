"""One-time backfill: copy every historical AI Workspace chat prompt into `prompts`.

Run from the backend folder:
    .venv/Scripts/python scripts/backfill_workspace_prompts.py
    .venv/Scripts/python scripts/backfill_workspace_prompts.py --dry-run

Why: prompts written in the AI Workspace used to live only in `messages`, so the
prompts collection (and the AI Studio history) showed nothing for them. Every
prompt the user gives must be in `prompts`.

Safe to re-run: a message that already produced a prompt document is skipped.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from app.core.database import (  # noqa: E402
    conversations_collection,
    messages_collection,
    prompts_collection,
    user_settings_collection,
)
from app.services.gemini_service import alias_for_model  # noqa: E402

DRY_RUN = "--dry-run" in sys.argv


def main() -> None:
    conversations = {c["_id"]: c for c in conversations_collection().find({})}
    settings_by_user = {s["user_id"]: s for s in user_settings_collection().find({})}

    # Oldest first so a user message is immediately followed by its answer.
    messages = list(messages_collection().find({}).sort([("conversation_id", 1), ("created_at", 1), ("_id", 1)]))

    created = skipped = orphan = 0
    for index, msg in enumerate(messages):
        if msg.get("role") != "user":
            continue

        conversation = conversations.get(msg.get("conversation_id"))
        if not conversation:
            orphan += 1
            continue

        # The reply is the next assistant message in the same conversation.
        answer = None
        answered_at = None
        for follow_up in messages[index + 1 :]:
            if follow_up.get("conversation_id") != msg["conversation_id"]:
                break
            if follow_up.get("role") == "assistant":
                answer = follow_up.get("content")
                answered_at = follow_up.get("created_at")
                break

        already = prompts_collection().find_one(
            {"conversation_id": msg["conversation_id"], "created_at": msg["created_at"]}
        )
        if already:
            skipped += 1
            continue

        settings = settings_by_user.get(msg.get("user_id")) or {}
        content = (msg.get("content") or "").strip()
        doc = {
            "user_id": msg["user_id"],
            "title": content[:60] or "Workspace prompt",
            "prompt": msg.get("content"),
            "model": alias_for_model(settings.get("default_model")),
            "temperature": 0.7,
            "max_output_tokens": 1000,
            "response": answer,
            "source": "workspace",
            "conversation_id": msg["conversation_id"],
            "notebook_id": conversation.get("notebook_id"),
            "created_at": msg.get("created_at"),
        }
        if answered_at:
            doc["executed_at"] = answered_at

        if not DRY_RUN:
            prompts_collection().insert_one(doc)
        created += 1
        print(f"  {'would copy' if DRY_RUN else 'copied'}: {doc['title']!r}")

    print()
    print(f"{'DRY RUN - ' if DRY_RUN else ''}backfilled: {created} | already present: {skipped} | orphaned: {orphan}")
    print(f"prompts now: {prompts_collection().count_documents({})}")


if __name__ == "__main__":
    main()
