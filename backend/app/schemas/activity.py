from pydantic import BaseModel


class ActivityLogResponse(BaseModel):
    id: str
    action: str
    description: str = ""
    metadata: dict = {}
    created_at: str | None = None
