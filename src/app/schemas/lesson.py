from pydantic import BaseModel, ConfigDict, Field


class LessonCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = ""
    position: int = Field(default=1, ge=1)


class LessonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    position: int
    course_id: int


class LessonUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = None
    position: int | None = Field(default=None, ge=1)