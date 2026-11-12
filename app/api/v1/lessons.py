import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.dependencies import CurrentUser, DBSession
from app.db.models.course import Course
from app.db.models.lesson import Lesson
from app.db.models.module import Module
from app.db.models.user import UserRole
from app.schemas.lesson import LessonCreate, LessonResponse

router = APIRouter(prefix="/modules/{module_id}/lessons", tags=["Lessons"])


@router.post(
    "/",
    response_model=LessonResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_lesson(
    module_id: uuid.UUID,
    payload: LessonCreate,
    db: DBSession,
    current_user: CurrentUser,
) -> LessonResponse:
    result = await db.execute(
        select(Module, Course)
        .join(Course, Module.course_id == Course.id)
        .where(Module.id == module_id)
    )
    row = result.one_or_none()

    if row is None:
        raise HTTPException(status_code=404, detail="Module not found")

    __module, course = row

    if current_user.role != UserRole.ADMIN and course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    lesson = Lesson(
        module_id=module_id,
        title=payload.title,
        content=payload.content,
        position=payload.position,
    )

    db.add(lesson)
    await db.commit()
    await db.refresh(lesson)

    return LessonResponse.model_validate(lesson)


@router.get("/", response_model=list[LessonResponse])
async def list_lessons(
    module_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> list[LessonResponse]:
    result = await db.execute(
        select(Module, Course)
        .join(Course, Module.course_id == Course.id)
        .where(Module.id == module_id)
    )
    row = result.one_or_none()

    if row is None:
        raise HTTPException(status_code=404, detail="Module not found")

    _, course = row

    if current_user.role == UserRole.STUDENT and not course.is_published:
        raise HTTPException(status_code=404, detail="Module not found")

    if current_user.role == UserRole.TEACHER and course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    lessons = await db.execute(
        select(Lesson).where(Lesson.module_id == module_id).order_by(Lesson.position)
    )

    return [LessonResponse.model_validate(lesson) for lesson in lessons.scalars().all()]
