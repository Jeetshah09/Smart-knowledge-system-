from pydantic import BaseModel, Field


class NotebookCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=2000)


class NotebookUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)


class NotebookResponse(BaseModel):
    id: str
    title: str
    description: str = ""
    is_pinned: bool = False
    resource_count: int = 0
    created_at: str | None = None
    updated_at: str | None = None
