"""Conversation and message endpoints."""
from fastapi import APIRouter, Depends, HTTPException

from app.core.database import conversations_collection, messages_collection
from app.dependencies.auth import get_current_user_id, parse_object_id_or_400
from app.schemas.conversation import ConversationCreate, ConversationRename
from app.utils.mongo_utils import serialize_doc, serialize_docs

router = APIRouter(prefix="/api/conversations", tags=["Conversations"])


def _owned(conversation_id: str, user_id: str) -> dict:
    oid = parse_object_id_or_400(conversation_id, "conversation")
    doc = conversations_collection().find_one(
        {"_id": oid, "user_id": parse_object_id_or_400(user_id, "user")}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return doc


def _with_meta(doc: dict) -> dict:
    data = serialize_doc(doc)
    count = messages_collection().count_documents({"conversation_id": doc["_id"]})
    data["message_count"] = count
    last = messages_collection().find_one(
        {"conversation_id": doc["_id"]}, sort=[("created_at", -1)]
    )
    data["last_message"] = (last or {}).get("content", "")[:160] if last else None
    return data


@router.post("")
def create_conversation(payload: ConversationCreate, user_id: str = Depends(get_current_user_id)):
    from app.core.database import notebooks_collection

    notebook_oid = parse_object_id_or_400(payload.notebook_id, "notebook")
    user_oid = parse_object_id_or_400(user_id, "user")
    notebook = notebooks_collection().find_one({"_id": notebook_oid, "user_id": user_oid})
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found.")

    from app.core.config import utc_now

    now = utc_now()
    doc = {
        "user_id": user_oid,
        "notebook_id": notebook_oid,
        "title": payload.title.strip() or "New conversation",
        "created_at": now,
        "updated_at": now,
    }
    result = conversations_collection().insert_one(doc)
    saved = conversations_collection().find_one({"_id": result.inserted_id})
    return {"success": True, "message": "Conversation created", "data": {"conversation": _with_meta(saved)}}


@router.get("")
def list_conversations(notebook_id: str | None = None, user_id: str = Depends(get_current_user_id)):
    query: dict = {"user_id": parse_object_id_or_400(user_id, "user")}
    if notebook_id:
        query["notebook_id"] = parse_object_id_or_400(notebook_id, "notebook")
    docs = list(conversations_collection().find(query).sort("updated_at", -1))
    return {
        "success": True,
        "message": "Conversations fetched",
        "data": {"conversations": [_with_meta(d) for d in docs]},
    }


@router.get("/{conversation_id}")
def get_conversation(conversation_id: str, user_id: str = Depends(get_current_user_id)):
    doc = _owned(conversation_id, user_id)
    return {"success": True, "message": "Conversation fetched", "data": {"conversation": _with_meta(doc)}}


@router.patch("/{conversation_id}")
def rename_conversation(conversation_id: str, payload: ConversationRename, user_id: str = Depends(get_current_user_id)):
    from app.core.config import utc_now

    doc = _owned(conversation_id, user_id)
    conversations_collection().update_one(
        {"_id": doc["_id"]},
        {"$set": {"title": payload.title.strip(), "updated_at": utc_now()}},
    )
    saved = conversations_collection().find_one({"_id": doc["_id"]})
    return {"success": True, "message": "Conversation renamed", "data": {"conversation": _with_meta(saved)}}


@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: str, user_id: str = Depends(get_current_user_id)):
    doc = _owned(conversation_id, user_id)
    messages_collection().delete_many({"conversation_id": doc["_id"]})
    conversations_collection().delete_one({"_id": doc["_id"]})
    return {"success": True, "message": "Conversation deleted", "data": None}


@router.get("/{conversation_id}/messages")
def get_messages(conversation_id: str, user_id: str = Depends(get_current_user_id)):
    doc = _owned(conversation_id, user_id)
    docs = list(
        messages_collection()
        .find({"conversation_id": doc["_id"]})
        .sort("created_at", 1)
    )
    return {"success": True, "message": "Messages fetched", "data": {"messages": serialize_docs(docs)}}
