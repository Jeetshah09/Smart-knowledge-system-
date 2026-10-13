"""User settings endpoints."""
import bson

from fastapi import APIRouter, Depends

from app.core.config import utc_now
from app.core.database import user_settings_collection
from app.dependencies.auth import get_current_user_id
from app.schemas.settings import UserSettingsUpdate
from app.services.gemini_service import alias_for_model
from app.utils.mongo_utils import serialize_doc

router = APIRouter(prefix="/api/settings", tags=["Settings"])

DEFAULTS = {
    "theme": "system",
    "notifications": True,
    "default_model": "balanced",
    "response_style": "balanced",
}


@router.get("")
def get_settings(user_id: str = Depends(get_current_user_id)):
    oid = bson.ObjectId(user_id)
    doc = user_settings_collection().find_one({"user_id": oid})
    if not doc:
        user_settings_collection().update_one(
            {"user_id": oid},
            {"$setOnInsert": {**DEFAULTS, "user_id": oid, "created_at": utc_now(), "updated_at": utc_now()}},
            upsert=True,
        )
        doc = user_settings_collection().find_one({"user_id": oid})
    data = serialize_doc(doc)
    data.update({k: v for k, v in DEFAULTS.items() if k not in data})
    return {"success": True, "message": "Settings fetched", "data": {"settings": data}}


@router.put("")
def update_settings(payload: UserSettingsUpdate, user_id: str = Depends(get_current_user_id)):
    oid = bson.ObjectId(user_id)
    updates = {"updated_at": utc_now()}
    for field in ("theme", "notifications", "default_model", "response_style"):
        value = getattr(payload, field)
        if value is not None:
            # Normalize any legacy/raw model value to its provider-neutral alias.
            if field == "default_model":
                value = alias_for_model(value)
            updates[field] = value

    user_settings_collection().update_one(
        {"user_id": oid}, {"$set": updates, "$setOnInsert": {"created_at": utc_now()}}, upsert=True
    )
    doc = user_settings_collection().find_one({"user_id": oid})
    data = serialize_doc(doc)
    data.update({k: v for k, v in DEFAULTS.items() if k not in data})
    return {"success": True, "message": "Settings updated", "data": {"settings": data}}
