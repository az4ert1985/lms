from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from app.db.models.user import UserRole
from app.services.enrollment_service import EnrollmentService
from fastapi import HTTPException


@pytest.fixture
def enrollment_repo():
    repo = MagicMock()
    repo.get_published_course = AsyncMock()
    repo.get_by_student_and_course = AsyncMock(return_value=None)
    repo.add = MagicMock()
    repo.commit = AsyncMock()
    repo.refresh = AsyncMock()
    return repo


@pytest.mark.asyncio
async def test_enroll_student_success(enrollment_repo, make_user, make_course):
    user = make_user(UserRole.STUDENT)
    course = make_course(user.id)
    enrollment_repo.get_published_course.return_value = course
    enrollment = await EnrollmentService(enrollment_repo).enroll_student(
        str(course.id), user
    )
    assert enrollment.student_id == user.id
    assert enrollment.course_id == course.id
    enrollment_repo.add.assert_called_once_with(enrollment)
    enrollment_repo.commit.assert_awaited_once()
    enrollment_repo.refresh.assert_awaited_once_with(enrollment)


@pytest.mark.asyncio
async def test_enroll_student_wrong_role(enrollment_repo, make_user):
    with pytest.raises(HTTPException) as exc:
        await EnrollmentService(enrollment_repo).enroll_student(
            str(uuid4()), make_user(UserRole.TEACHER)
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_enroll_student_invalid_id(enrollment_repo, make_user):
    with pytest.raises(HTTPException) as exc:
        await EnrollmentService(enrollment_repo).enroll_student("invalid", make_user())
    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_enroll_student_course_missing(enrollment_repo, make_user):
    enrollment_repo.get_published_course.return_value = None
    with pytest.raises(HTTPException) as exc:
        await EnrollmentService(enrollment_repo).enroll_student(
            str(uuid4()), make_user()
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_enroll_student_already_enrolled(enrollment_repo, make_user, make_course):
    user = make_user()
    course = make_course(user.id)
    enrollment_repo.get_published_course.return_value = course
    enrollment_repo.get_by_student_and_course.return_value = object()
    with pytest.raises(HTTPException) as exc:
        await EnrollmentService(enrollment_repo).enroll_student(str(course.id), user)
    assert exc.value.status_code == 409
