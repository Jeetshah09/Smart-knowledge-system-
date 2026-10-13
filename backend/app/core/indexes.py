"""Create MongoDB indexes. Called once at app startup."""
from pymongo.errors import PyMongoError

from app.core.database import (
    activity_logs_collection,
    conversations_collection,
    generated_content_collection,
    messages_collection,
    notebooks_collection,
    prompts_collection,
    resources_collection,
    user_settings_collection,
    users_collection,
)


def create_indexes() -> None:
    users_collection().create_index("email", unique=True)

    notebooks_collection().create_index("user_id")
    notebooks_collection().create_index([("user_id", 1), ("created_at", -1)])

    resources_collection().create_index("user_id")
    resources_collection().create_index("notebook_id")
    resources_collection().create_index([("notebook_id", 1), ("created_at", -1)])

    conversations_collection().create_index("user_id")
    conversations_collection().create_index("notebook_id")

    messages_collection().create_index("conversation_id")
    messages_collection().create_index([("conversation_id", 1), ("created_at", 1)])

    generated_content_collection().create_index("user_id")
    generated_content_collection().create_index("notebook_id")
    generated_content_collection().create_index([("notebook_id", 1), ("created_at", -1)])

    prompts_collection().create_index("user_id")

    user_settings_collection().create_index("user_id", unique=True)

    activity_logs_collection().create_index([("user_id", 1), ("created_at", -1)])
