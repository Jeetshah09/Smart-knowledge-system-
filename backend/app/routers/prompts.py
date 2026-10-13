"""Prompt Studio (AI Studio) endpoints."""
import logging

from fastapi import APIRouter, Depends, HTTPException
from pymongo.errors import PyMongoError

from app.core.database import prompts_collection
from app.dependencies.auth import get_current_user_id, parse_object_id_or_400
from app.schemas.prompt import PromptCreate, PromptExecuteRequest, PromptResponse
from app.services import gemini_service
from app.services.gemini_service import GeminiError
from app.services.activity_service import log_activity
from app.utils.mongo_utils import serialize_doc, serialize_docs

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/prompts", tags=["Prompts"])


def _owned(prompt_id: str, user_id: str) -> dict:
    oid = parse_object_id_or_400(prompt_id, "prompt")
    doc = prompts_collection().find_one({"_id": oid, "user_id": parse_object_id_or_400(user_id, "user")})
    if not doc:
        raise HTTPException(status_code=404, detail="Prompt not found.")
    return doc


@router.post("")
def create_prompt(payload: PromptCreate, user_id: str = Depends(get_current_user_id)):
    from app.core.config import utc_now

    doc = {
        "user_id": parse_object_id_or_400(user_id, "user"),
        "title": payload.title.strip(),
        "prompt": payload.prompt,
        # Store the provider-neutral alias; resolved to a real model on execute.
        "model": gemini_service.alias_for_model(payload.model),
        "temperature": payload.temperature,
        "max_output_tokens": payload.max_output_tokens,
        "response": None,
        "source": "studio",
        "created_at": utc_now(),
    }
    try:
        result = prompts_collection().insert_one(doc)
        saved = prompts_collection().find_one({"_id": result.inserted_id})
    except PyMongoError:
        # Log the real cause server-side and return 503, instead of letting the
        # generic 500 handler mask a database problem as an app bug.
        logger.exception("Failed to save prompt to MongoDB")
        raise HTTPException(status_code=503, detail="Could not save the prompt. Check the MongoDB connection and try again.")
    return {"success": True, "message": "Prompt saved", "data": {"prompt": serialize_doc(saved)}}


@router.get("")
def list_prompts(user_id: str = Depends(get_current_user_id)):
    docs = list(
        prompts_collection()
        .find({"user_id": parse_object_id_or_400(user_id, "user")})
        .sort("created_at", -1)
    )
    return {"success": True, "message": "Prompts fetched", "data": {"prompts": serialize_docs(docs)}}


@router.get("/{prompt_id}")
def get_prompt(prompt_id: str, user_id: str = Depends(get_current_user_id)):
    doc = _owned(prompt_id, user_id)
    return {"success": True, "message": "Prompt fetched", "data": {"prompt": serialize_doc(doc)}}


@router.delete("/{prompt_id}")
def delete_prompt(prompt_id: str, user_id: str = Depends(get_current_user_id)):
    doc = _owned(prompt_id, user_id)
    prompts_collection().delete_one({"_id": doc["_id"]})
    return {"success": True, "message": "Prompt deleted", "data": None}


@router.post("/{prompt_id}/execute")
def execute_prompt(prompt_id: str, payload: PromptExecuteRequest, user_id: str = Depends(get_current_user_id)):
    from app.core.config import utc_now

    doc = _owned(prompt_id, user_id)
    temperature = payload.temperature if payload.temperature is not None else doc.get("temperature", 0.7)
    max_tokens = payload.max_output_tokens if payload.max_output_tokens is not None else doc.get("max_output_tokens", 1000)

    raw_model = doc.get("model")
    try:
        response = gemini_service.generate_prompt_response(
            prompt=doc["prompt"],
            model=gemini_service.resolve_model(raw_model) if raw_model else None,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
    except GeminiError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    # CHANGED: Instead of update_one modifying the template document, 
    # we insert a brand new document representing the prompt execution history.
    history_entry = {
        "user_id": parse_object_id_or_400(user_id, "user"),
        "title": f"Run: {doc['title']}",
        "prompt": doc["prompt"],
        "model": raw_model,
        "temperature": temperature,
        "max_output_tokens": max_tokens,
        "response": response,
        "source": "studio",
        "created_at": utc_now(),
        "executed_at": utc_now()
    }
    
    try:
        result = prompts_collection().insert_one(history_entry)
        saved = prompts_collection().find_one({"_id": result.inserted_id})
    except PyMongoError:
        logger.exception("Failed to insert prompt execution into MongoDB")
        raise HTTPException(status_code=503, detail="Could not log prompt history.")

    log_activity(user_id, "executed_prompt", f"Executed prompt '{doc['title']}'")
    return {"success": True, "message": "Prompt executed and history logged", "data": {"prompt": serialize_doc(saved)}}
