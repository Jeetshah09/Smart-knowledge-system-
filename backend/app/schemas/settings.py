from pydantic import BaseModel, Field


class UserSettingsUpdate(BaseModel):
    theme: str | None = Field(default=None, pattern="^(light|dark|system)$")
    notifications: bool | None = None
    default_model: str | None = Field(default=None, pattern="^(fast|balanced|advanced|turbo)$")
    response_style: str | None = Field(default=None, pattern="^(concise|balanced|detailed)$")


class UserSettingsResponse(BaseModel):
    theme: str = "system"
    notifications: bool = True
    default_model: str = "balanced"
    response_style: str = "balanced"
