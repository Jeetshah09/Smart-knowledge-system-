"""Chat endpoint - the core AI workflow."""
import logging

from fastapi import APIRouter, Depends, HTTPException
from pymongo.errors import PyMongoError

from app.core.config import utc_now
from app.core.database import (
    conversations_collection,
    messages_collection,
    notebooks_collection,
    prompts_collection,
    resources_collection,
    user_settings_collection,
)
from app.dependencies.auth import get_current_user_id, parse_object_id_or_400
from app.schemas.chat import ChatRequest
from app.services import gemini_service
from app.services.gemini_service import GeminiError
from app.utils.mongo_utils import to_object_id
from app.utils.text_utils import truncate_for_prompt

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Chat"])


def _collect_resource_content(notebook_oid, user_oid, resource_ids: list[str]) -> tuple[str, int]:
    """Gather selected (or all) resource contents for the prompt."""
    query: dict = {"notebook_id": notebook_oid, "user_id": user_oid}
    if resource_ids:
        valid_ids = []
        for rid in resource_ids:
            try:
                valid_ids.append(to_object_id(rid))
            except ValueError:
                continue
        if not valid_ids:
            raise HTTPException(status_code=400, detail="No valid resource ids were provided.")
        query["_id"] = {"$in": valid_ids}

    docs = list(resources_collection().find(query).sort("created_at", 1))
    if not docs:
        return "", 0

    sections = []
    for doc in docs:
        body = (doc.get("content") or "").strip()
        if not body:
            body = "[No extracted text is available for this resource.]"
        sections.append(f"=== Resource: {doc['name']} (type: {doc['type']}) ===\n{body}")
    return "\n\n".join(sections), len(docs)


@router.post("/chat")
def chat(payload: ChatRequest, user_id: str = Depends(get_current_user_id)):
    user_oid = parse_object_id_or_400(user_id, "user")
    notebook_oid = parse_object_id_or_400(payload.notebook_id, "notebook")

    notebook = notebooks_collection().find_one({"_id": notebook_oid, "user_id": user_oid})
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found.")

    # 1. Conversation: reuse or create.
    if payload.conversation_id:
        conv_oid = parse_object_id_or_400(payload.conversation_id, "conversation")
        conversation = conversations_collection().find_one(
            {"_id": conv_oid, "user_id": user_oid, "notebook_id": notebook_oid}
        )
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found.")
    else:
        now = utc_now()
        title = payload.message.strip()[:60] or "New conversation"
        conv_doc = {
            "user_id": user_oid,
            "notebook_id": notebook_oid,
            "title": title,
            "created_at": now,
            "updated_at": now,
        }
        conv_result = conversations_collection().insert_one(conv_doc)
        conv_oid = conv_result.inserted_id

    # 2. Persist the prompt the user gave us - before anything that can fail
    #    (missing sources, AI error, timeout). Every prompt must land in the
    #    `prompts` collection, even when we cannot produce an answer.
    #    A MongoDB failure aborts the request before we spend tokens on Gemini.
    settings_doc = user_settings_collection().find_one({"user_id": user_oid})
    try:
        prompt_result = prompts_collection().insert_one(
            {
                "user_id": user_oid,
                "title": payload.message.strip()[:60] or "Workspace prompt",
                "prompt": payload.message,
                # Keep a valid provider-neutral alias so db_health stays happy;
                # chat itself uses the server-configured Gemini model.
                "model": gemini_service.alias_for_model(
                    (settings_doc or {}).get("default_model")
                ),
                "temperature": 0.7,
                "max_output_tokens": 1000,
                "response": None,
                "source": "workspace",
                "conversation_id": conv_oid,
                "notebook_id": notebook_oid,
                "created_at": utc_now(),
            }
        )
    except PyMongoError:
        logger.exception("Failed to store workspace prompt in MongoDB")
        raise HTTPException(
            status_code=503,
            detail="Could not store your prompt. Check the MongoDB connection and try again.",
        )

    # 3. Resource content.
    material, resources_used = _collect_resource_content(
        notebook_oid, user_oid, payload.resource_ids
    )
    if resources_used == 0:
        # The prompt above is already stored - the user's words are never lost,
        # even though we cannot answer without sources.
        raise HTTPException(
            status_code=400,
            detail="No resources with content selected. Upload a resource or select one first.",
        )

    # 4. Recent history (last 8 messages) for context.
    history = list(
        messages_collection()
        .find({"conversation_id": conv_oid})
        .sort("created_at", -1)
        .limit(8)
    )
    history = list(reversed(history))

    # 5. Response style from user settings.
    response_style = (settings_doc or {}).get("response_style", "balanced")

    # 6. Call Gemini.
    try:
        answer = gemini_service.generate_chat_response(
            resource_content=material,
            user_message=payload.message,
            history=history,
            response_style=response_style,
        )
    except GeminiError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    # 7. Persist both messages.
    now = utc_now()
    messages_collection().insert_many(
        [
            {
                "conversation_id": conv_oid,
                "user_id": user_oid,
                "role": "user",
                "content": payload.message,
                "created_at": now,
            },
            {
                "conversation_id": conv_oid,
                "user_id": user_oid,
                "role": "assistant",
                "content": answer,
                "created_at": now,
            },
        ]
    )
    conversations_collection().update_one(
        {"_id": conv_oid}, {"$set": {"updated_at": now}}
    )

    # Attach the AI answer to the stored prompt. The prompt itself is already
    # safe in the database, so a failure here is only logged.
    try:
        prompts_collection().update_one(
            {"_id": prompt_result.inserted_id},
            {"$set": {"response": answer, "executed_at": now}},
        )
    except PyMongoError:
        logger.exception("Failed to attach the response to the stored prompt")

    return {
        "success": True,
        "message": "Response generated",
        "data": {
            "conversation_id": str(conv_oid),
            "response": answer,
            "resources_used": resources_used,
        },
    }
