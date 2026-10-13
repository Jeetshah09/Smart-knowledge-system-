"""Shared file-validation helpers."""
import os

ALLOWED_EXTENSIONS = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".txt": "txt",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".webp": "image",
}

ALLOWED_MIME_PREFIXES = ("image/",)

PDF_MIMES = {"application/pdf"}
DOCX_MIMES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def detect_type(filename: str, mime_type: str | None) -> str | None:
    """Return the resource type for a file, or None if unsupported."""
    ext = os.path.splitext(filename)[1].lower()
    resource_type = ALLOWED_EXTENSIONS.get(ext)
    if resource_type is None:
        return None
    if resource_type == "pdf" and mime_type and mime_type not in PDF_MIMES and mime_type != "application/octet-stream":
        return None
    if resource_type == "docx" and mime_type and mime_type not in DOCX_MIMES and mime_type != "application/octet-stream":
        return None
    return resource_type
