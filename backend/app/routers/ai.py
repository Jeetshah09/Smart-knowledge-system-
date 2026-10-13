"""AI learning-content generation endpoints."""
from fastapi import APIRouter, Depends, HTTPException

from app.core.config import utc_now
from app.core.database import (
    generated_content_collection,
    notebooks_collection,
    resources_collection,
)
from app.dependencies.auth import get_current_user_id, parse_object_id_or_400
from app.schemas.generated_content import (
    FaqRequest,
    FlashcardsRequest,
    QuizRequest,
    StudyNotesRequest,
    SummaryRequest,
)
from app.services import gemini_service
from app.services.gemini_service import GeminiError
from app.services.activity_service import log_activity
from app.utils.mongo_utils import serialize_doc, to_object_id

router = APIRouter(prefix="/api/ai", tags=["AI Generation"])


def _material(notebook_id: str, resource_ids: list[str], user_id: str) -> str:
    """Verify ownership then concatenate selected resource contents."""
    notebook_oid = parse_object_id_or_400(notebook_id, "notebook")
    user_oid = parse_object_id_or_400(user_id, "user")
    notebook = notebooks_collection().find_one({"_id": notebook_oid, "user_id": user_oid})
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found.")

    oids = []
    for rid in resource_ids:
        try:
            oids.append(parse_object_id_or_400(rid, "resource"))
        except HTTPException:
            continue
    if not oids:
        raise HTTPException(status_code=400, detail="Select at least one valid resource.")

    docs = list(
        resources_collection().find({"_id": {"$in": oids}, "user_id": user_oid, "notebook_id": notebook_oid})
    )
    if not docs:
        raise HTTPException(status_code=404, detail="Selected resources were not found in this notebook.")

    sections = []
    for doc in docs:
        body = (doc.get("content") or "").strip()
        if not body:
            body = "[No extracted text is available for this resource.]"
        sections.append(f"=== Resource: {doc['name']} ===\n{body}")
    return "\n\n".join(sections)


def _as_object_ids(resource_ids: list[str]) -> list:
    """Convert resource id strings to ObjectIds, skipping invalid ones."""
    oids = []
    for rid in resource_ids:
        try:
            oids.append(to_object_id(rid))
        except ValueError:
            continue
    return oids


def _store(user_id: str, notebook_id: str, resource_ids: list[str], type_: str, title: str, content: dict) -> dict:
    doc = {
        "user_id": parse_object_id_or_400(user_id, "user"),
        "notebook_id": parse_object_id_or_400(notebook_id, "notebook"),
        # Store real ObjectIds so references are consistent with every other collection.
        "resource_ids": _as_object_ids(resource_ids),
        "type": type_,
        "title": title,
        "content": content,
        "created_at": utc_now(),
    }
    result = generated_content_collection().insert_one(doc)
    saved = generated_content_collection().find_one({"_id": result.inserted_id})
    return serialize_doc(saved)


@router.post("/summary")
def summary(payload: SummaryRequest, user_id: str = Depends(get_current_user_id)):
    material = _material(payload.notebook_id, payload.resource_ids, user_id)
    try:
        data = gemini_service.generate_summary(material)
    except GeminiError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    saved = _store(user_id, payload.notebook_id, payload.resource_ids, "summary", "Summary", data)
    log_activity(user_id, "generated_summary", "Generated a summary")
    return {"success": True, "message": "Summary generated", "data": {"generated_content": saved}}


@router.post("/quiz")
def quiz(payload: QuizRequest, user_id: str = Depends(get_current_user_id)):
    material = _material(payload.notebook_id, payload.resource_ids, user_id)
    try:
        data = gemini_service.generate_quiz(material, payload.number_of_questions)
    except GeminiError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    saved = _store(user_id, payload.notebook_id, payload.resource_ids, "quiz", "Quiz", data)
    log_activity(user_id, "generated_quiz", "Generated a quiz")
    return {"success": True, "message": "Quiz generated", "data": {"generated_content": saved}}


@router.post("/flashcards")
def flashcards(payload: FlashcardsRequest, user_id: str = Depends(get_current_user_id)):
    material = _material(payload.notebook_id, payload.resource_ids, user_id)
    try:
        data = gemini_service.generate_flashcards(material, payload.number_of_cards)
    except GeminiError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    saved = _store(user_id, payload.notebook_id, payload.resource_ids, "flashcards", "Flashcards", data)
    log_activity(user_id, "generated_flashcards", "Generated flashcards")
    return {"success": True, "message": "Flashcards generated", "data": {"generated_content": saved}}


@router.post("/faq")
def faq(payload: FaqRequest, user_id: str = Depends(get_current_user_id)):
    material = _material(payload.notebook_id, payload.resource_ids, user_id)
    try:
        data = gemini_service.generate_faq(material)
    except GeminiError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    saved = _store(user_id, payload.notebook_id, payload.resource_ids, "faq", "FAQ", data)
    log_activity(user_id, "generated_faq", "Generated FAQ")
    return {"success": True, "message": "FAQ generated", "data": {"generated_content": saved}}


@router.post("/study-notes")
def study_notes(payload: StudyNotesRequest, user_id: str = Depends(get_current_user_id)):
    material = _material(payload.notebook_id, payload.resource_ids, user_id)
    try:
        data = gemini_service.generate_study_notes(material)
    except GeminiError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    saved = _store(user_id, payload.notebook_id, payload.resource_ids, "study_notes", "Study Notes", data)
    log_activity(user_id, "generated_study_notes", "Generated study notes")
    return {"success": True, "message": "Study notes generated", "data": {"generated_content": saved}}


@router.get("/notebook/{notebook_id}")
def list_generated(notebook_id: str, user_id: str = Depends(get_current_user_id)):
    """List previously generated content for a notebook."""
    docs = list(
        generated_content_collection()
        .find({
            "notebook_id": parse_object_id_or_400(notebook_id, "notebook"),
            "user_id": parse_object_id_or_400(user_id, "user"),
        })
        .sort("created_at", -1)
    )
    return {"success": True, "message": "Generated content fetched", "data": {"items": [serialize_doc(d) for d in docs]}}
