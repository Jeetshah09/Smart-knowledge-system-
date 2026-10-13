"""Shared service helpers for resources."""
import re
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings
from app.utils.validators import detect_type

TYPE_TO_FOLDER = {
    "pdf": "pdf",
    "docx": "documents",
    "txt": "documents",
    "image": "images",
}


def validate_upload_file(file: UploadFile) -> tuple[str, str]:
    """Validate an uploaded file. Returns (resource_type, safe_filename).

    Raises ValueError with a user-friendly message when the file is not allowed.
    """
    filename = Path(file.filename or "upload").name
    if not filename:
        raise ValueError("File has no name.")

    resource_type = detect_type(filename, file.content_type)
    if resource_type is None:
        raise ValueError(
            "Unsupported file type. Allowed: PDF, DOCX, TXT, PNG, JPG, JPEG, WEBP."
        )

    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if size > max_bytes:
        raise ValueError(f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE_MB} MB.")
    if size == 0:
        raise ValueError("File is empty.")

    return resource_type, filename


def save_upload(file: UploadFile, resource_type: str) -> tuple[str, int]:
    """Persist the upload under uploads/<type>/ with a unique name.

    Returns (relative_file_path, file_size).
    """
    folder = Path(settings.UPLOAD_DIR) / TYPE_TO_FOLDER[resource_type]
    folder.mkdir(parents=True, exist_ok=True)

    safe_name = re.sub(r"[^\w.\- ]", "_", Path(file.filename or "file").name)
    unique_name = f"{uuid.uuid4().hex[:12]}_{safe_name}"
    target = folder / unique_name

    size = 0
    with open(target, "wb") as out:
        while chunk := file.file.read(1024 * 1024):
            out.write(chunk)
            size += len(chunk)

    return target.as_posix(), size
