from pydantic import BaseModel, Field


class PromptCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    prompt: str = Field(min_length=1, max_length=8000)
    model: str = "fast"  # provider-neutral alias resolved server-side
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_output_tokens: int = Field(default=1000, ge=64, le=8192)


class PromptExecuteRequest(BaseModel):
    """Optional overrides when executing a saved prompt."""
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_output_tokens: int | None = Field(default=None, ge=64, le=8192)


class PromptResponse(BaseModel):
    id: str
    title: str
    prompt: str
    model: str
    temperature: float
    max_output_tokens: int
    response: str | None = None
    created_at: str | None = None
