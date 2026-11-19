from unittest.mock import AsyncMock, MagicMock

import pytest
from app.db.models.user import UserRole
from app.repositories.course_repository import CourseRepository


@pytest.mark.asyncio
@pytest.mark.parametrize("role", [UserRole.ADMIN, UserRole.TEACHER, UserRole.STUDENT])
async def test_list_for_user(role, make_user, make_course):
    user = make_user(role)
    courses = [make_course(user.id)]
    scalars = MagicMock()
    scalars.all.return_value = courses
    result = MagicMock()
    result.scalars.return_value = scalars
    session = MagicMock()
    session.execute = AsyncMock(return_value=result)

    found = await CourseRepository(session).list_for_user(user)

    assert found == courses
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("course_exists", [True, False])
async def test_get_by_id(course_exists, make_user, make_course):
    user = make_user()
    course = make_course(user.id) if course_exists else None
    result = MagicMock()
    result.scalar_one_or_none.return_value = course
    session = MagicMock()
    session.execute = AsyncMock(return_value=result)

    found = await CourseRepository(session).get_by_id(
        course.id if course else __import__("uuid").uuid4()
    )

    assert found is course
