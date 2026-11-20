from fastapi import APIRouter, status

from app.api.dependencies import CurrentUser, EnrollmentServiceDep
from app.schemas.enrollment import EnrollmentResponse

router = APIRouter(prefix="/enrollments", tags=["Enrollments"])


@router.post(
    "/{course_id}",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def enroll_student(
    course_id: str,
    service: EnrollmentServiceDep,
    current_user: CurrentUser,
) -> EnrollmentResponse:
    enrollment = await service.enroll_student(
        course_id,
        current_user,
    )
    return EnrollmentResponse.model_validate(enrollment)
