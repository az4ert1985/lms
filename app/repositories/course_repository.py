from uuid import UUID

from app.db.models.course import Course
from app.db.models.user import User, UserRole
from app.repositories.base import BaseRepository
from sqlalchemy import select


class CourseRepository(BaseRepository):
    async def list_for_user(self, user: User) -> list[Course]:
        query = select(Course)

        if user.role == UserRole.STUDENT:
            query = query.where(Course.is_published.is_(True))
        elif user.role == UserRole.TEACHER:
            query = query.where(Course.teacher_id == user.id)

        result = await self.session.execute(query.order_by(Course.created_at.desc()))
        return list(result.scalars().all())

    async def get_by_id(self, course_id: UUID) -> Course | None:
        result = await self.session.execute(
            select(Course).where(Course.id == course_id)
        )
        return result.scalar_one_or_none()
