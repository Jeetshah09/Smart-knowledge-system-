from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId


def is_valid_object_id(value: str) -> bool:
    try:
        ObjectId(value)
        return True
    except (InvalidId, TypeError):
        return False


def to_object_id(value: str) -> ObjectId:
    """Convert string to ObjectId. Raises ValueError with a clean message if invalid."""
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        raise ValueError(f"Invalid id format: {value}")


def _serialize_value(value):
    """JSON-safe a single value, recursing into dicts and lists."""
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_serialize_value(v) for v in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def serialize_doc(doc: dict | None, id_field: str = "_id") -> dict | None:
    """Convert a MongoDB document into a JSON-safe dict (ObjectId -> str, datetime -> ISO).

    Mongo stores naive UTC datetimes (pymongo drops tzinfo by default), so they
    are re-tagged as UTC before serialization. Without this, browsers treat the
    timestamp as local time and every "time ago" label is shifted by the
    timezone offset (e.g. everything showing "5h ago" in UTC+5:30).

    Nested values (lists of ObjectIds, embedded docs, ...) are handled too.
    """
    if doc is None:
        return None
    data = {key: _serialize_value(value) for key, value in doc.items()}
    if id_field in data:
        data["id"] = data.pop(id_field)
    return data


def serialize_docs(docs: list[dict]) -> list[dict]:
    return [serialize_doc(d) for d in docs if d is not None]
