from pydantic import BaseModel, Field


class YouTubeAddRequest(BaseModel):
    notebook_id: str
    url: str


class ResourceResponse(BaseModel):
    id: str
    notebook_id: str
    name: str
    type: str
    file_path: str | None = None
    youtube_url: str | None = None
    file_size: int | None = None
    mime_type: str | None = None
    content: str = ""
    processing_status: str
    created_at: str | None = None
    updated_at: str | None = None


class ResourceContentResponse(BaseModel):
    """Resource with content included (for previews / AI context)."""
    id: str
    notebook_id: str
    name: str
    type: str
    content: str = ""
    processing_status: str
    youtube_url: str | None = None
