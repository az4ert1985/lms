import uuid

from fastapi import APIRouter, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser, DBSession, build_course_service
from app.db.models.course import Course
from app.db.models.user import User
from app.schemas.course import CourseCreate, CourseResponse, CourseUpdate

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("/", response_model=list[CourseResponse])
async def list_courses(
    db: DBSession,
    current_user: CurrentUser,
) -> list[CourseResponse]:
    courses = await build_course_service(db).list_courses(current_user)
    return [CourseResponse.model_validate(course) for course in courses]


@router.post(
    "/",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_course(
    payload: CourseCreate,
    db: DBSession,
    current_user: CurrentUser,
) -> CourseResponse:
    course = await build_course_service(db).create_course(
        payload,
        current_user,
    )
    return CourseResponse.model_validate(course)


async def get_accessible_course(
    course_id: uuid.UUID,
    db: AsyncSession,
    current_user: User,
) -> Course:
    return await build_course_service(db).get_accessible_course(
        course_id,
        current_user,
    )


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> CourseResponse:
    course = await build_course_service(db).get_course(
        course_id,
        current_user,
    )
    return CourseResponse.model_validate(course)


@router.patch("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: uuid.UUID,
    payload: CourseUpdate,
    db: DBSession,
    current_user: CurrentUser,
) -> CourseResponse:
    course = await build_course_service(db).update_course(
        course_id,
        payload,
        current_user,
    )
    return CourseResponse.model_validate(course)


@router.delete(
    "/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_course(
    course_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> None:
    await build_course_service(db).delete_course(
        course_id,
        current_user,
    )
