from fastapi import APIRouter, status

from app.api.dependencies import (
    CurrentUser,
    DBSession,
    build_enrollment_service,
)
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
    enrollment = await build_enrollment_service(db).enroll_student(
        course_id,
        current_user,
    )
    return EnrollmentResponse.model_validate(enrollment)
