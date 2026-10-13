from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    notebook_id: str
    message: str = Field(min_length=1, max_length=8000)
    resource_ids: list[str] = Field(default_factory=list)
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    response: str
    resources_used: int
