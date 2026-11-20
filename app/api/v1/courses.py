import uuid

from fastapi import APIRouter, status

from app.api.dependencies import CourseServiceDep, CurrentUser
from app.db.models.course import Course
from app.db.models.user import User
from app.schemas.course import CourseCreate, CourseResponse, CourseUpdate
from app.services.course_service import CourseService

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("/", response_model=list[CourseResponse])
async def list_courses(
    service: CourseServiceDep,
    current_user: CurrentUser,
) -> list[CourseResponse]:
    courses = await service.list_courses(current_user)
    return [CourseResponse.model_validate(course) for course in courses]


@router.post(
    "/",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_course(
    payload: CourseCreate,
    service: CourseServiceDep,
    current_user: CurrentUser,
) -> CourseResponse:
    course = await service.create_course(
        payload,
        current_user,
    )
    return CourseResponse.model_validate(course)


async def get_accessible_course(
    course_id: uuid.UUID,
    service: CourseService,
    current_user: User,
) -> Course:
    return await service.get_accessible_course(
        course_id,
        current_user,
    )


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: uuid.UUID,
    service: CourseServiceDep,
    current_user: CurrentUser,
) -> CourseResponse:
    course = await service.get_course(
        course_id,
        current_user,
    )
    return CourseResponse.model_validate(course)


@router.patch("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: uuid.UUID,
    payload: CourseUpdate,
    service: CourseServiceDep,
    current_user: CurrentUser,
) -> CourseResponse:
    course = await service.update_course(
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
    service: CourseServiceDep,
    current_user: CurrentUser,
) -> None:
    await service.delete_course(
        course_id,
        current_user,
    )
