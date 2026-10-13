"""Notebook CRUD endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.config import utc_now
from app.core.database import notebooks_collection, resources_collection
from app.dependencies.auth import get_current_user_id, parse_object_id_or_400
from app.schemas.notebook import NotebookCreate, NotebookUpdate
from app.services.activity_service import log_activity
from app.utils.mongo_utils import serialize_doc, serialize_docs

router = APIRouter(prefix="/api/notebooks", tags=["Notebooks"])


def _enrich(doc: dict) -> dict:
    data = serialize_doc(doc)
    data["resource_count"] = resources_collection().count_documents(
        {"notebook_id": doc["_id"]}
    )
    return data


@router.post("")
def create_notebook(payload: NotebookCreate, user_id: str = Depends(get_current_user_id)):
    now = utc_now()
    doc = {
        "user_id": parse_object_id_or_400(user_id, "user"),
        "title": payload.title.strip(),
        "description": payload.description.strip(),
        "is_pinned": False,
        "created_at": now,
        "updated_at": now,
    }
    result = notebooks_collection().insert_one(doc)
    saved = notebooks_collection().find_one({"_id": result.inserted_id})
    log_activity(user_id, "created_notebook", f"Created notebook '{payload.title}'")
    return {
        "success": True,
        "message": "Notebook created",
        "data": {"notebook": _enrich(saved)},
    }


@router.get("/search")
def search_notebooks(q: str = Query(min_length=1), user_id: str = Depends(get_current_user_id)):
    import re as _re

    regex = _re.compile(_re.escape(q), _re.IGNORECASE)
    docs = list(
        notebooks_collection()
        .find({"user_id": parse_object_id_or_400(user_id, "user"),
               "$or": [{"title": regex}, {"description": regex}]})
        .sort("updated_at", -1)
    )
    return {"success": True, "message": "Search results", "data": {"notebooks": serialize_docs(docs)}}


@router.get("")
def list_notebooks(user_id: str = Depends(get_current_user_id)):
    docs = list(
        notebooks_collection()
        .find({"user_id": parse_object_id_or_400(user_id, "user")})
        .sort([("is_pinned", -1), ("updated_at", -1)])
    )
    return {
        "success": True,
        "message": "Notebooks fetched",
        "data": {"notebooks": [_enrich(d) for d in docs]},
    }


def _get_owned_notebook(notebook_id: str, user_id: str) -> dict:
    oid = parse_object_id_or_400(notebook_id, "notebook")
    doc = notebooks_collection().find_one({"_id": oid, "user_id": parse_object_id_or_400(user_id, "user")})
    if not doc:
        raise HTTPException(status_code=404, detail="Notebook not found.")
    return doc


@router.get("/{notebook_id}")
def get_notebook(notebook_id: str, user_id: str = Depends(get_current_user_id)):
    doc = _get_owned_notebook(notebook_id, user_id)
    return {"success": True, "message": "Notebook fetched", "data": {"notebook": _enrich(doc)}}


@router.put("/{notebook_id}")
def update_notebook(notebook_id: str, payload: NotebookUpdate, user_id: str = Depends(get_current_user_id)):
    doc = _get_owned_notebook(notebook_id, user_id)
    updates = {"updated_at": utc_now()}
    if payload.title is not None:
        updates["title"] = payload.title.strip()
    if payload.description is not None:
        updates["description"] = payload.description.strip()
    notebooks_collection().update_one({"_id": doc["_id"]}, {"$set": updates})
    saved = notebooks_collection().find_one({"_id": doc["_id"]})
    log_activity(user_id, "updated_notebook", f"Updated notebook '{saved['title']}'")
    return {"success": True, "message": "Notebook updated", "data": {"notebook": _enrich(saved)}}


@router.patch("/{notebook_id}/pin")
def toggle_pin(notebook_id: str, user_id: str = Depends(get_current_user_id)):
    doc = _get_owned_notebook(notebook_id, user_id)
    new_value = not doc.get("is_pinned", False)
    notebooks_collection().update_one({"_id": doc["_id"]}, {"$set": {"is_pinned": new_value}})
    return {"success": True, "message": "Pin toggled", "data": {"is_pinned": new_value}}


@router.delete("/{notebook_id}")
def delete_notebook(notebook_id: str, user_id: str = Depends(get_current_user_id)):
    from app.core.database import conversations_collection, generated_content_collection, messages_collection

    doc = _get_owned_notebook(notebook_id, user_id)
    oid = doc["_id"]

    conversation_ids = [c["_id"] for c in conversations_collection().find({"notebook_id": oid}, {"_id": 1})]
    if conversation_ids:
        messages_collection().delete_many({"conversation_id": {"$in": conversation_ids}})
    conversations_collection().delete_many({"notebook_id": oid})
    generated_content_collection().delete_many({"notebook_id": oid})
    resources_collection().delete_many({"notebook_id": oid})
    notebooks_collection().delete_one({"_id": oid})

    log_activity(user_id, "deleted_notebook", f"Deleted notebook '{doc['title']}'")
    return {"success": True, "message": "Notebook deleted", "data": None}
