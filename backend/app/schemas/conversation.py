from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    notebook_id: str
    title: str = Field(default="New conversation", max_length=160)


class ConversationRename(BaseModel):
    title: str = Field(min_length=1, max_length=160)


class ConversationResponse(BaseModel):
    id: str
    notebook_id: str
    title: str
    message_count: int = 0
    last_message: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: str | None = None
