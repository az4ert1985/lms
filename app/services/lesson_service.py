from uuid import UUID

from app.db.models.lesson import Lesson
from app.db.models.user import User, UserRole
from app.repositories.lesson_repository import LessonRepository
from app.schemas.lesson import LessonCreate
from fastapi import HTTPException


class LessonService:
    def __init__(self, lessons: LessonRepository) -> None:
        self.lessons = lessons

    async def create_lesson(
        self,
        module_id: UUID,
        payload: LessonCreate,
        current_user: User,
    ) -> Lesson:
        row = await self.lessons.get_module_and_course(module_id)

        if row is None:
            raise HTTPException(status_code=404, detail="Module not found")

        _, course = row

        if current_user.role != UserRole.ADMIN and course.teacher_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        lesson = Lesson(
            module_id=module_id,
            title=payload.title,
            content=payload.content,
            position=payload.position,
        )

        self.lessons.add(lesson)
        await self.lessons.commit()
        await self.lessons.refresh(lesson)

        return lesson

    async def list_lessons(
        self,
        module_id: UUID,
        current_user: User,
    ) -> list[Lesson]:
        row = await self.lessons.get_module_and_course(module_id)

        if row is None:
            raise HTTPException(status_code=404, detail="Module not found")

        _, course = row

        if current_user.role == UserRole.STUDENT and not course.is_published:
            raise HTTPException(status_code=404, detail="Module not found")

        if (
            current_user.role == UserRole.TEACHER
            and course.teacher_id != current_user.id
        ):
            raise HTTPException(status_code=403, detail="Access denied")

        return await self.lessons.list_by_module(module_id)
