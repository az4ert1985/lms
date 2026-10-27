from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.lesson import LessonRead


class CourseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None


class CourseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    is_published: bool | None = None


class CourseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    is_published: bool
    owner_id: int
    created_at: datetime


class CourseDetail(CourseRead):
    lessons: list[LessonRead] = []
