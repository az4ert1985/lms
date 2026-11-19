from uuid import UUID

from app.db.models.course import Course
from app.db.models.user import User, UserRole
from app.repositories.course_repository import CourseRepository
from app.schemas.course import CourseCreate, CourseUpdate
from fastapi import HTTPException, status


class CourseService:
    def __init__(self, courses: CourseRepository) -> None:
        self.courses = courses

    async def list_courses(self, current_user: User) -> list[Course]:
        return await self.courses.list_for_user(current_user)

    async def create_course(
        self,
        payload: CourseCreate,
        current_user: User,
    ) -> Course:
        if current_user.role not in (UserRole.ADMIN, UserRole.TEACHER):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only teachers and admins can create courses",
            )

        course = Course(
            title=payload.title,
            description=payload.description,
            teacher_id=current_user.id,
        )

        self.courses.add(course)
        await self.courses.commit()
        await self.courses.refresh(course)

        return course

    async def get_accessible_course(
        self,
        course_id: UUID,
        current_user: User,
    ) -> Course:
        if not hasattr(current_user, "id"):
            raise HTTPException(status_code=403, detail="Access denied")

        course = await self.courses.get_by_id(course_id)

        if course is None:
            raise HTTPException(status_code=404, detail="Course not found")

        return course

    async def get_course(
        self,
        course_id: UUID,
        current_user: User,
    ) -> Course:
        course = await self.get_accessible_course(course_id, current_user)

        if current_user.role == UserRole.STUDENT and not course.is_published:
            raise HTTPException(status_code=404, detail="Course not found")

        if (
            current_user.role == UserRole.TEACHER
            and course.teacher_id != current_user.id
        ):
            raise HTTPException(status_code=403, detail="Access denied")

        return course

    async def update_course(
        self,
        course_id: UUID,
        payload: CourseUpdate,
        current_user: User,
    ) -> Course:
        course = await self.get_accessible_course(course_id, current_user)

        if current_user.role != UserRole.ADMIN and course.teacher_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(course, field, value)

        await self.courses.commit()
        await self.courses.refresh(course)

        return course

    async def delete_course(
        self,
        course_id: UUID,
        current_user: User,
    ) -> None:
        course = await self.get_accessible_course(course_id, current_user)

        if current_user.role != UserRole.ADMIN and course.teacher_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        await self.courses.delete(course)
        await self.courses.commit()
