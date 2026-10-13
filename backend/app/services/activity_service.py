"""Reusable activity logging."""
from app.core.config import utc_now
from app.core.database import activity_logs_collection
from app.utils.mongo_utils import to_object_id


def log_activity(user_id: str, action: str, description: str = "", metadata: dict | None = None) -> None:
    """Best-effort activity logging - never breaks the main request flow."""
    try:
        activity_logs_collection().insert_one(
            {
                "user_id": to_object_id(user_id),
                "action": action,
                "description": description,
                "metadata": metadata or {},
                "created_at": utc_now(),
            }
        )
    except Exception:
        pass
