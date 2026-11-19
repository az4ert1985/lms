import uuid

from app.db.models.enrollment import Enrollment
from app.db.models.user import User, UserRole
from app.repositories.enrollment_repository import EnrollmentRepository
from fastapi import HTTPException


class EnrollmentService:
    def __init__(self, enrollments: EnrollmentRepository) -> None:
        self.enrollments = enrollments

    async def enroll_student(
        self,
        course_id: str,
        current_user: User,
    ) -> Enrollment:
        if current_user.role != UserRole.STUDENT:
            raise HTTPException(status_code=403, detail="Students only")

        try:
            parsed_id = uuid.UUID(course_id)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail="Invalid course ID",
            ) from None

        course = await self.enrollments.get_published_course(parsed_id)

        if course is None:
            raise HTTPException(status_code=404, detail="Course not found")

        existing = await self.enrollments.get_by_student_and_course(
            current_user.id,
            parsed_id,
        )

        if existing is not None:
            raise HTTPException(status_code=409, detail="Already enrolled")

        enrollment = Enrollment(
            student_id=current_user.id,
            course_id=parsed_id,
        )

        self.enrollments.add(enrollment)
        await self.enrollments.commit()
        await self.enrollments.refresh(enrollment)

        return enrollment
