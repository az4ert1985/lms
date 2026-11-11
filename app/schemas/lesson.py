import uuid

from pydantic import BaseModel, ConfigDict, Field


class LessonCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str | None = None
    position: int = Field(default=0, ge=0)


class LessonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    module_id: uuid.UUID
    title: str
    content: str | None
    position: int
