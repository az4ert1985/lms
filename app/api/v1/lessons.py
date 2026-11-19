import uuid

from fastapi import APIRouter, status

from app.api.dependencies import CurrentUser, DBSession, build_lesson_service
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
    lesson = await build_lesson_service(db).create_lesson(
        module_id,
        payload,
        current_user,
    )
    return LessonResponse.model_validate(lesson)


@router.get("/", response_model=list[LessonResponse])
async def list_lessons(
    module_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> list[LessonResponse]:
    lessons = await build_lesson_service(db).list_lessons(
        module_id,
        current_user,
    )
    return [LessonResponse.model_validate(lesson) for lesson in lessons]
