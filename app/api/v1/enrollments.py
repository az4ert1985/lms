from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.dependencies import CurrentUser, DBSession
from app.db.models.course import Course
from app.db.models.enrollment import Enrollment
from app.db.models.user import UserRole
from app.schemas.enrollment import EnrollmentResponse

router = APIRouter(prefix="/enrollments", tags=["Enrollments"])


@router.post(
    "/{course_id}",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def enroll_student(
    course_id: str,
    db: DBSession,
    current_user: CurrentUser,
) -> EnrollmentResponse:
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Students only")

    import uuid

    try:
        parsed_id = uuid.UUID(course_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid course ID") from None

    result = await db.execute(
        select(Course).where(
            Course.id == parsed_id,
            Course.is_published.is_(True),
        )
    )
    course = result.scalar_one_or_none()

    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")

    existing = await db.execute(
        select(Enrollment).where(
            Enrollment.student_id == current_user.id,
            Enrollment.course_id == parsed_id,
        )
    )

    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Already enrolled")

    enrollment = Enrollment(
        student_id=current_user.id,
        course_id=parsed_id,
    )

    db.add(enrollment)
    await db.commit()
    await db.refresh(enrollment)

    return EnrollmentResponse.model_validate(enrollment)
