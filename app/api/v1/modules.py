import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.dependencies import CurrentUser, DBSession
from app.db.models.course import Course
from app.db.models.module import Module
from app.db.models.user import UserRole
from app.schemas.module import ModuleCreate, ModuleResponse

router = APIRouter(prefix="/courses/{course_id}/modules", tags=["Modules"])


@router.post(
    "/",
    response_model=ModuleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_module(
    course_id: uuid.UUID,
    payload: ModuleCreate,
    db: DBSession,
    current_user: CurrentUser,
) -> ModuleResponse:
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()

    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")

    if current_user.role != UserRole.ADMIN and course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    module = Module(
        course_id=course_id,
        title=payload.title,
        position=payload.position,
    )

    db.add(module)
    await db.commit()
    await db.refresh(module)

    return ModuleResponse.model_validate(module)


@router.get("/", response_model=list[ModuleResponse])
async def list_modules(
    course_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> list[ModuleResponse]:
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()

    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")

    if current_user.role == UserRole.STUDENT and not course.is_published:
        raise HTTPException(status_code=404, detail="Course not found")

    if current_user.role == UserRole.TEACHER and course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    modules = await db.execute(
        select(Module).where(Module.course_id == course_id).order_by(Module.position)
    )

    return [ModuleResponse.model_validate(module) for module in modules.scalars().all()]
