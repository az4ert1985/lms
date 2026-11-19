from uuid import UUID

from fastapi import HTTPException

from app.db.models.module import Module
from app.db.models.user import User, UserRole
from app.repositories.course_repository import CourseRepository
from app.repositories.module_repository import ModuleRepository
from app.schemas.module import ModuleCreate


class ModuleService:
    def __init__(
        self,
        courses: CourseRepository,
        modules: ModuleRepository,
    ) -> None:
        self.courses = courses
        self.modules = modules

    async def create_module(
        self,
        course_id: UUID,
        payload: ModuleCreate,
        current_user: User,
    ) -> Module:
        course = await self.courses.get_by_id(course_id)

        if course is None:
            raise HTTPException(status_code=404, detail="Course not found")

        if current_user.role != UserRole.ADMIN and course.teacher_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        module = Module(
            course_id=course_id,
            title=payload.title,
            position=payload.position,
        )

        self.modules.add(module)
        await self.modules.commit()
        await self.modules.refresh(module)

        return module

    async def list_modules(
        self,
        course_id: UUID,
        current_user: User,
    ) -> list[Module]:
        course = await self.courses.get_by_id(course_id)

        if course is None:
            raise HTTPException(status_code=404, detail="Course not found")

        if current_user.role == UserRole.STUDENT and not course.is_published:
            raise HTTPException(status_code=404, detail="Course not found")

        if (
            current_user.role == UserRole.TEACHER
            and course.teacher_id != current_user.id
        ):
            raise HTTPException(status_code=403, detail="Access denied")

        return await self.modules.list_by_course(course_id)
