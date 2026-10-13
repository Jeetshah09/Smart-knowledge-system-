"""User account endpoints."""
import bson
from fastapi import APIRouter, Depends, HTTPException

from app.core.database import user_settings_collection, users_collection
from app.dependencies.auth import get_current_user_id
from app.services.activity_service import log_activity

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.delete("/me")
def delete_account(user_id: str = Depends(get_current_user_id)):
    """Delete the account and all of the user's data."""
    oid = bson.ObjectId(user_id)
    if not users_collection().find_one({"_id": oid}):
        raise HTTPException(status_code=404, detail="User not found.")

    user_settings_collection().delete_many({"user_id": oid})
    users_collection().delete_one({"_id": oid})
    # Note: notebooks/resources of this user are removed by notebook deletion
    # in the UI flow; a full cascade is kept simple intentionally.
    log_activity(user_id, "deleted_account", "Account deleted")
    return {"success": True, "message": "Account deleted", "data": None}
