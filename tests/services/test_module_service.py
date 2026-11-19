from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from app.db.models.user import UserRole
from app.schemas.module import ModuleCreate
from app.services.module_service import ModuleService
from fastapi import HTTPException


@pytest.fixture
def repositories():
    courses, modules = MagicMock(), MagicMock()
    courses.get_by_id = AsyncMock()
    modules.list_by_course = AsyncMock(return_value=[])
    modules.add = MagicMock()
    modules.commit = AsyncMock()
    modules.refresh = AsyncMock()
    return courses, modules


@pytest.mark.asyncio
async def test_create_module_course_missing(repositories, make_user):
    courses, modules = repositories
    courses.get_by_id.return_value = None
    with pytest.raises(HTTPException) as exc:
        await ModuleService(courses, modules).create_module(
            uuid4(), ModuleCreate(title="Intro"), make_user()
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_create_module_forbidden(repositories, make_user, make_course):
    courses, modules = repositories
    user = make_user(UserRole.TEACHER)
    courses.get_by_id.return_value = make_course(uuid4())
    with pytest.raises(HTTPException) as exc:
        await ModuleService(courses, modules).create_module(
            uuid4(), ModuleCreate(title="Intro"), user
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
@pytest.mark.parametrize("role", [UserRole.ADMIN, UserRole.TEACHER])
async def test_create_module_success(repositories, make_user, make_course, role):
    courses, modules = repositories
    user = make_user(role)
    courses.get_by_id.return_value = make_course(user.id)
    module = await ModuleService(courses, modules).create_module(
        uuid4(), ModuleCreate(title="Intro", position=2), user
    )
    assert module.title == "Intro"
    assert module.position == 2
    modules.add.assert_called_once_with(module)
    modules.commit.assert_awaited_once()
    modules.refresh.assert_awaited_once_with(module)


@pytest.mark.asyncio
async def test_list_modules_course_missing(repositories, make_user):
    courses, modules = repositories
    courses.get_by_id.return_value = None
    with pytest.raises(HTTPException) as exc:
        await ModuleService(courses, modules).list_modules(uuid4(), make_user())
    assert exc.value.status_code == 404


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("role", "published", "owner", "expected"),
    [
        (UserRole.STUDENT, False, True, 404),
        (UserRole.TEACHER, True, False, 403),
        (UserRole.STUDENT, True, True, None),
        (UserRole.ADMIN, False, False, None),
        (UserRole.TEACHER, True, True, None),
    ],
)
async def test_list_modules_permissions(
    repositories, make_user, make_course, role, published, owner, expected
):
    courses, modules = repositories
    user = make_user(role)
    course = make_course(user.id if owner else uuid4(), is_published=published)
    courses.get_by_id.return_value = course
    service = ModuleService(courses, modules)
    if expected:
        with pytest.raises(HTTPException) as exc:
            await service.list_modules(course.id, user)
        assert exc.value.status_code == expected
    else:
        assert await service.list_modules(course.id, user) == []
        modules.list_by_course.assert_awaited_once_with(course.id)
