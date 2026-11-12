import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser, DBSession
from app.db.models.course import Course
from app.db.models.user import UserRole
from app.schemas.course import CourseCreate, CourseResponse, CourseUpdate

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("/", response_model=list[CourseResponse])
async def list_courses(
    db: DBSession,
    current_user: CurrentUser,
) -> list[CourseResponse]:
    query = select(Course)

    if current_user.role == UserRole.STUDENT:
        query = query.where(Course.is_published.is_(True))

    elif current_user.role == UserRole.TEACHER:
        query = query.where(Course.teacher_id == current_user.id)

    result = await db.execute(query.order_by(Course.created_at.desc()))

    return [CourseResponse.model_validate(course) for course in result.scalars().all()]


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
    if current_user.role not in (
        UserRole.ADMIN,
        UserRole.TEACHER,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers and admins can create courses",
        )

    course = Course(
        title=payload.title,
        description=payload.description,
        teacher_id=current_user.id,
    )

    db.add(course)
    await db.commit()
    await db.refresh(course)

    return CourseResponse.model_validate(course)


async def get_accessible_course(
    course_id: uuid.UUID,
    db: AsyncSession,
    current_user: object,
) -> Course:
    if not hasattr(current_user, "id"):
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()

    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")

    return course


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> CourseResponse:
    course = await get_accessible_course(course_id, db, current_user)

    if current_user.role == UserRole.STUDENT and not course.is_published:
        raise HTTPException(status_code=404, detail="Course not found")

    if current_user.role == UserRole.TEACHER and course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return CourseResponse.model_validate(course)


@router.patch("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: uuid.UUID,
    payload: CourseUpdate,
    db: DBSession,
    current_user: CurrentUser,
) -> CourseResponse:
    course = await get_accessible_course(course_id, db, current_user)

    if current_user.role != UserRole.ADMIN and course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(course, field, value)

    await db.commit()
    await db.refresh(course)

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
    course = await get_accessible_course(course_id, db, current_user)

    if current_user.role != UserRole.ADMIN and course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    await db.delete(course)
    await db.commit()
