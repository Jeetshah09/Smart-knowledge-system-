from pymongo import MongoClient
from pymongo.errors import PyMongoError

from app.core.config import settings


class DatabaseNotConnected(Exception):
    """Raised when MongoDB cannot be reached."""


_client: MongoClient | None = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
    return _client


def get_database():
    try:
        client = get_client()
        client.admin.command("ping")
    except PyMongoError as exc:
        raise DatabaseNotConnected(
            "Could not connect to MongoDB. Check MONGODB_URL in backend/.env "
            "(or start MongoDB locally / use MongoDB Atlas)."
        ) from exc
    return client[settings.DATABASE_NAME]


# Collection accessors resolved lazily so the app can boot even if
# MongoDB is briefly unavailable (routers then return a clear 503 error).
def users_collection():
    return get_database()["users"]


def notebooks_collection():
    return get_database()["notebooks"]


def resources_collection():
    return get_database()["resources"]


def conversations_collection():
    return get_database()["conversations"]


def messages_collection():
    return get_database()["messages"]


def generated_content_collection():
    return get_database()["generated_content"]


def prompts_collection():
    return get_database()["prompts"]


def user_settings_collection():
    return get_database()["user_settings"]


def activity_logs_collection():
    return get_database()["activity_logs"]
