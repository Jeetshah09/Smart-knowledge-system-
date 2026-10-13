"""Resource endpoints: file uploads, YouTube URLs, listing, preview, delete."""
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.core.config import settings, utc_now
from app.core.database import notebooks_collection, resources_collection
from app.dependencies.auth import get_current_user_id, parse_object_id_or_400
from app.schemas.resource import YouTubeAddRequest
from app.services import file_service
from app.services.activity_service import log_activity
from app.services.storage_service import save_upload, validate_upload_file
from app.services.youtube_service import extract_transcript, extract_video_id, is_valid_youtube_url
from app.utils.mongo_utils import serialize_doc, serialize_docs

router = APIRouter(prefix="/api", tags=["Resources"])


def _get_owned_notebook(notebook_id: str, user_id: str) -> dict:
    oid = parse_object_id_or_400(notebook_id, "notebook")
    doc = notebooks_collection().find_one(
        {"_id": oid, "user_id": parse_object_id_or_400(user_id, "user")}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Notebook not found.")
    return doc


def _get_owned_resource(resource_id: str, user_id: str) -> dict:
    oid = parse_object_id_or_400(resource_id, "resource")
    doc = resources_collection().find_one(
        {"_id": oid, "user_id": parse_object_id_or_400(user_id, "user")}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Resource not found.")
    return doc


def _public(doc: dict) -> dict:
    """Resource without the heavy content field (for lists/cards)."""
    data = serialize_doc(doc)
    content = data.get("content") or ""
    data["has_content"] = bool(content)
    data["content_preview"] = content[:280]
    data.pop("content", None)
    return data


@router.post("/resources/upload")
async def upload_resource(
    notebook_id: str,
    file: UploadFile,
    user_id: str = Depends(get_current_user_id),
):
    notebook = _get_owned_notebook(notebook_id, user_id)

    try:
        resource_type, _filename = validate_upload_file(file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    file_path, file_size = save_upload(file, resource_type)

    # Extract text synchronously (simple, viva-friendly workflow).
    processing_status = "completed"
    content = ""
    try:
        if resource_type == "pdf":
            content = file_service.extract_pdf_text(file_path)
        elif resource_type == "docx":
            content = file_service.extract_docx_text(file_path)
        elif resource_type == "txt":
            content = file_service.extract_txt_text(file_path)
        # images: content stays empty; Gemini can use the image later on request.
        if resource_type in ("pdf", "docx", "txt") and not content.strip():
            processing_status = "failed"
    except Exception:
        processing_status = "failed"

    doc = {
        "user_id": parse_object_id_or_400(user_id, "user"),
        "notebook_id": notebook["_id"],
        "name": Path(file.filename or "file").name,
        "type": resource_type,
        "file_path": file_path,
        "youtube_url": None,
        "file_size": file_size,
        "mime_type": file.content_type,
        "content": content,
        "processing_status": processing_status,
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }
    result = resources_collection().insert_one(doc)
    saved = resources_collection().find_one({"_id": result.inserted_id})

    log_activity(user_id, "uploaded_resource", f"Uploaded {resource_type.upper()} '{doc['name']}'")
    message = "Resource uploaded and processed" if processing_status == "completed" else \
        "Resource uploaded, but no readable text could be extracted"
    return {"success": True, "message": message, "data": {"resource": _public(saved)}}


@router.post("/resources/youtube")
def add_youtube_resource(payload: YouTubeAddRequest, user_id: str = Depends(get_current_user_id)):
    notebook = _get_owned_notebook(payload.notebook_id, user_id)

    if not is_valid_youtube_url(payload.url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL.")

    video_id = extract_video_id(payload.url)
    content = extract_transcript(video_id) or ""
    status = "completed" if content else "failed"

    doc = {
        "user_id": parse_object_id_or_400(user_id, "user"),
        "notebook_id": notebook["_id"],
        "name": f"YouTube video ({video_id})",
        "type": "youtube",
        "file_path": None,
        "youtube_url": payload.url,
        "file_size": None,
        "mime_type": None,
        "content": content,
        "processing_status": status,
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }
    result = resources_collection().insert_one(doc)
    saved = resources_collection().find_one({"_id": result.inserted_id})

    message = "YouTube video added with transcript" if content else (
        "YouTube video added, but no transcript was available for this video. "
        "You can still chat about it by asking general questions."
    )
    log_activity(user_id, "uploaded_resource", f"Added YouTube resource {video_id}")
    return {"success": True, "message": message, "data": {"resource": _public(saved)}}


@router.get("/notebooks/{notebook_id}/resources")
def list_resources(notebook_id: str, user_id: str = Depends(get_current_user_id)):
    notebook = _get_owned_notebook(notebook_id, user_id)
    docs = list(
        resources_collection()
        .find({"notebook_id": notebook["_id"], "user_id": notebook["user_id"]})
        .sort("created_at", -1)
    )
    return {"success": True, "message": "Resources fetched", "data": {"resources": [_public(d) for d in docs]}}


@router.get("/resources/{resource_id}")
def get_resource(resource_id: str, user_id: str = Depends(get_current_user_id)):
    doc = _get_owned_resource(resource_id, user_id)
    return {"success": True, "message": "Resource fetched", "data": {"resource": serialize_doc(doc)}}


@router.get("/resources/{resource_id}/download")
def download_resource(resource_id: str, user_id: str = Depends(get_current_user_id)):
    doc = _get_owned_resource(resource_id, user_id)
    if not doc.get("file_path") or not Path(doc["file_path"]).exists():
        raise HTTPException(status_code=404, detail="File not found on server.")
    return FileResponse(doc["file_path"], filename=doc["name"])


@router.delete("/resources/{resource_id}")
def delete_resource(resource_id: str, user_id: str = Depends(get_current_user_id)):
    doc = _get_owned_resource(resource_id, user_id)
    if doc.get("file_path"):
        try:
            Path(doc["file_path"]).unlink(missing_ok=True)
        except OSError:
            pass
    resources_collection().delete_one({"_id": doc["_id"]})
    log_activity(user_id, "deleted_resource", f"Deleted resource '{doc['name']}'")
    return {"success": True, "message": "Resource deleted", "data": None}
