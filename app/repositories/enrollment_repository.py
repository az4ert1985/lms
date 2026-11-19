from uuid import UUID

from sqlalchemy import select

from app.db.models.course import Course
from app.db.models.enrollment import Enrollment
from app.repositories.base import BaseRepository


class EnrollmentRepository(BaseRepository):
    async def get_published_course(self, course_id: UUID) -> Course | None:
        result = await self.session.execute(
            select(Course).where(
                Course.id == course_id,
                Course.is_published.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_student_and_course(
        self,
        student_id: UUID,
        course_id: UUID,
    ) -> Enrollment | None:
        result = await self.session.execute(
            select(Enrollment).where(
                Enrollment.student_id == student_id,
                Enrollment.course_id == course_id,
            )
        )
        return result.scalar_one_or_none()
