from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from app.db.models.user import UserRole
from app.schemas.course import CourseCreate, CourseUpdate
from app.services.course_service import CourseService
from fastapi import HTTPException


@pytest.fixture
def course_repo():
    repo = MagicMock()
    repo.list_for_user = AsyncMock(return_value=[])
    repo.get_by_id = AsyncMock()
    repo.commit = AsyncMock()
    repo.refresh = AsyncMock()
    repo.delete = AsyncMock()
    repo.add = MagicMock()
    return repo


@pytest.mark.asyncio
async def test_list_courses(course_repo, make_user):
    user = make_user()
    assert await CourseService(course_repo).list_courses(user) == []
    course_repo.list_for_user.assert_awaited_once_with(user)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("role", "allowed"),
    [(UserRole.ADMIN, True), (UserRole.TEACHER, True), (UserRole.STUDENT, False)],
)
async def test_create_course(course_repo, make_user, role, allowed):
    user = make_user(role)
    service = CourseService(course_repo)
    payload = CourseCreate(title="New course", description="Description")
    if not allowed:
        with pytest.raises(HTTPException) as exc:
            await service.create_course(payload, user)
        assert exc.value.status_code == 403
        return
    course = await service.create_course(payload, user)
    assert course.title == payload.title
    course_repo.add.assert_called_once_with(course)
    course_repo.commit.assert_awaited_once()
    course_repo.refresh.assert_awaited_once_with(course)


@pytest.mark.asyncio
async def test_get_accessible_course_missing_user_id(course_repo):
    with pytest.raises(HTTPException) as exc:
        await CourseService(course_repo).get_accessible_course(uuid4(), object())
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_get_accessible_course_not_found(course_repo, make_user):
    course_repo.get_by_id.return_value = None
    with pytest.raises(HTTPException) as exc:
        await CourseService(course_repo).get_accessible_course(uuid4(), make_user())
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_accessible_course_success(course_repo, make_user, make_course):
    user = make_user()
    course = make_course(user.id)
    course_repo.get_by_id.return_value = course
    assert (
        await CourseService(course_repo).get_accessible_course(course.id, user)
        is course
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("role", "published", "owner", "expected"),
    [
        (UserRole.STUDENT, False, True, 404),
        (UserRole.TEACHER, True, False, 403),
        (UserRole.ADMIN, False, False, None),
        (UserRole.TEACHER, True, True, None),
        (UserRole.STUDENT, True, True, None),
    ],
)
async def test_get_course_permissions(
    course_repo, make_user, make_course, role, published, owner, expected
):
    user = make_user(role)
    course = make_course(user.id if owner else uuid4(), is_published=published)
    course_repo.get_by_id.return_value = course
    service = CourseService(course_repo)
    if expected:
        with pytest.raises(HTTPException) as exc:
            await service.get_course(course.id, user)
        assert exc.value.status_code == expected
    else:
        assert await service.get_course(course.id, user) is course


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("role", "owner", "allowed"),
    [
        (UserRole.ADMIN, False, True),
        (UserRole.TEACHER, True, True),
        (UserRole.TEACHER, False, False),
    ],
)
async def test_update_course_permissions(
    course_repo, make_user, make_course, role, owner, allowed
):
    user = make_user(role)
    course = make_course(user.id if owner else uuid4())
    course_repo.get_by_id.return_value = course
    payload = CourseUpdate(title="Updated course")
    service = CourseService(course_repo)
    if not allowed:
        with pytest.raises(HTTPException) as exc:
            await service.update_course(course.id, payload, user)
        assert exc.value.status_code == 403
    else:
        updated = await service.update_course(course.id, payload, user)
        assert updated.title == "Updated course"
        course_repo.commit.assert_awaited_once()
        course_repo.refresh.assert_awaited_once_with(course)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("role", "owner", "allowed"),
    [
        (UserRole.ADMIN, False, True),
        (UserRole.TEACHER, True, True),
        (UserRole.TEACHER, False, False),
    ],
)
async def test_delete_course_permissions(
    course_repo, make_user, make_course, role, owner, allowed
):
    user = make_user(role)
    course = make_course(user.id if owner else uuid4())
    course_repo.get_by_id.return_value = course
    service = CourseService(course_repo)
    if not allowed:
        with pytest.raises(HTTPException) as exc:
            await service.delete_course(course.id, user)
        assert exc.value.status_code == 403
    else:
        assert await service.delete_course(course.id, user) is None
        course_repo.delete.assert_awaited_once_with(course)
        course_repo.commit.assert_awaited_once()
