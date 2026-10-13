from pydantic import BaseModel, Field


class SummaryRequest(BaseModel):
    notebook_id: str
    resource_ids: list[str] = Field(min_length=1)


class QuizRequest(BaseModel):
    notebook_id: str
    resource_ids: list[str] = Field(min_length=1)
    number_of_questions: int = Field(default=10, ge=1, le=20)


class FlashcardsRequest(BaseModel):
    notebook_id: str
    resource_ids: list[str] = Field(min_length=1)
    number_of_cards: int = Field(default=10, ge=1, le=30)


class FaqRequest(BaseModel):
    notebook_id: str
    resource_ids: list[str] = Field(min_length=1)


class StudyNotesRequest(BaseModel):
    notebook_id: str
    resource_ids: list[str] = Field(min_length=1)


class GeneratedContentResponse(BaseModel):
    id: str
    notebook_id: str
    resource_ids: list[str] = []
    type: str
    title: str
    content: dict
    created_at: str | None = None
