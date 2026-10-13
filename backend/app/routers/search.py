"""Global search across notebooks, resources, conversations and prompts."""
import re

from fastapi import APIRouter, Depends, Query

from app.core.database import (
    conversations_collection,
    notebooks_collection,
    prompts_collection,
    resources_collection,
)
from app.dependencies.auth import get_current_user_id
from app.utils.mongo_utils import serialize_docs, to_object_id

router = APIRouter(prefix="/api/search", tags=["Search"])


@router.get("")
def global_search(q: str = Query(min_length=1), user_id: str = Depends(get_current_user_id)):
    user_oid = to_object_id(user_id)
    regex = re.compile(re.escape(q), re.IGNORECASE)

    notebooks = list(
        notebooks_collection().find(
            {"user_id": user_oid, "$or": [{"title": regex}, {"description": regex}]}
        ).limit(10)
    )
    resources = list(
        resources_collection().find(
            {"user_id": user_oid, "$or": [{"name": regex}, {"content": regex}]}
        ).limit(10)
    )
    conversations = list(
        conversations_collection().find(
            {"user_id": user_oid, "title": regex}
        ).limit(10)
    )
    prompts = list(
        prompts_collection().find(
            {"user_id": user_oid, "$or": [{"title": regex}, {"prompt": regex}]}
        ).limit(10)
    )

    return {
        "success": True,
        "message": "Search completed",
        "data": {
            "notebooks": serialize_docs(notebooks),
            "resources": [
                {**d, "content": (d.get("content") or "")[:200]}
                for d in serialize_docs(resources)
            ],
            "conversations": serialize_docs(conversations),
            "prompts": serialize_docs(prompts),
        },
    }
