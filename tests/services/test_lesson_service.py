from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from app.db.models.user import UserRole
from app.schemas.lesson import LessonCreate
from app.services.lesson_service import LessonService
from fastapi import HTTPException


@pytest.fixture
def lesson_repo():
    repo = MagicMock()
    repo.get_module_and_course = AsyncMock()
    repo.list_by_module = AsyncMock(return_value=[])
    repo.add = MagicMock()
    repo.commit = AsyncMock()
    repo.refresh = AsyncMock()
    return repo


@pytest.mark.asyncio
async def test_create_lesson_module_missing(lesson_repo, make_user):
    lesson_repo.get_module_and_course.return_value = None
    with pytest.raises(HTTPException) as exc:
        await LessonService(lesson_repo).create_lesson(
            uuid4(), LessonCreate(title="Intro"), make_user()
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_create_lesson_forbidden(
    lesson_repo, make_user, make_course, make_module
):
    user = make_user(UserRole.TEACHER)
    course = make_course(uuid4())
    lesson_repo.get_module_and_course.return_value = (make_module(course.id), course)
    with pytest.raises(HTTPException) as exc:
        await LessonService(lesson_repo).create_lesson(
            uuid4(), LessonCreate(title="Intro"), user
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_create_lesson_success(lesson_repo, make_user, make_course, make_module):
    user = make_user(UserRole.ADMIN)
    course = make_course(uuid4())
    module = make_module(course.id)
    lesson_repo.get_module_and_course.return_value = (module, course)
    lesson = await LessonService(lesson_repo).create_lesson(
        module.id, LessonCreate(title="Intro", content="Body", position=1), user
    )
    assert lesson.title == "Intro"
    assert lesson.content == "Body"
    lesson_repo.add.assert_called_once_with(lesson)
    lesson_repo.commit.assert_awaited_once()
    lesson_repo.refresh.assert_awaited_once_with(lesson)


@pytest.mark.asyncio
async def test_list_lessons_module_missing(lesson_repo, make_user):
    lesson_repo.get_module_and_course.return_value = None
    with pytest.raises(HTTPException) as exc:
        await LessonService(lesson_repo).list_lessons(uuid4(), make_user())
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
async def test_list_lessons_permissions(
    lesson_repo, make_user, make_course, make_module, role, published, owner, expected
):
    user = make_user(role)
    course = make_course(user.id if owner else uuid4(), is_published=published)
    module = make_module(course.id)
    lesson_repo.get_module_and_course.return_value = (module, course)
    service = LessonService(lesson_repo)
    if expected:
        with pytest.raises(HTTPException) as exc:
            await service.list_lessons(module.id, user)
        assert exc.value.status_code == expected
    else:
        assert await service.list_lessons(module.id, user) == []
        lesson_repo.list_by_module.assert_awaited_once_with(module.id)
