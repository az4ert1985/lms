from uuid import UUID

from sqlalchemy import select

from app.db.models.course import Course
from app.db.models.lesson import Lesson
from app.db.models.module import Module
from app.repositories.base import BaseRepository


class LessonRepository(BaseRepository):
    async def get_module_and_course(
        self,
        module_id: UUID,
    ) -> tuple[Module, Course] | None:
        result = await self.session.execute(
            select(Module, Course)
            .join(Course, Module.course_id == Course.id)
            .where(Module.id == module_id)
        )
        row = result.one_or_none()

        if row is None:
            return None

        return row[0], row[1]

    async def list_by_module(self, module_id: UUID) -> list[Lesson]:
        result = await self.session.execute(
            select(Lesson)
            .where(Lesson.module_id == module_id)
            .order_by(Lesson.position)
        )
        return list(result.scalars().all())
