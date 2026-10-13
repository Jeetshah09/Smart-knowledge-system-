"""Dashboard statistics endpoint."""
from fastapi import APIRouter, Depends

from app.core.database import (
    activity_logs_collection,
    conversations_collection,
    generated_content_collection,
    notebooks_collection,
    resources_collection,
)
from app.dependencies.auth import get_current_user_id
from app.utils.mongo_utils import serialize_docs, to_object_id

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats")
def stats(user_id: str = Depends(get_current_user_id)):
    oid = to_object_id(user_id)
    recent = list(
        activity_logs_collection()
        .find({"user_id": oid})
        .sort("created_at", -1)
        .limit(10)
    )
    return {
        "success": True,
        "message": "Dashboard stats",
        "data": {
            "notebook_count": notebooks_collection().count_documents({"user_id": oid}),
            "resource_count": resources_collection().count_documents({"user_id": oid}),
            "conversation_count": conversations_collection().count_documents({"user_id": oid}),
            "generated_content_count": generated_content_collection().count_documents({"user_id": oid}),
            "recent_activity": serialize_docs(recent),
        },
    }
