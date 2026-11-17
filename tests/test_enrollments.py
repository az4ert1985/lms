from uuid import uuid4

import pytest
from app.api.v1 import enrollments
from app.db.models import UserRole
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_enroll_student_wrong_role(fake_db, make_user) -> None:
    user = make_user(role=UserRole.TEACHER)

    with pytest.raises(HTTPException) as exc:
        await enrollments.enroll_student(str(uuid4()), fake_db, user)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_enroll_student_invalid_course_id(fake_db, make_user) -> None:
    user = make_user(role=UserRole.STUDENT)

    with pytest.raises(HTTPException) as exc:
        await enrollments.enroll_student("invalid-uuid", fake_db, user)

    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_enroll_student_course_not_found(
    fake_db,
    make_user,
    make_result,
) -> None:
    user = make_user(role=UserRole.STUDENT)
    fake_db.execute.return_value = make_result(scalar=None)

    with pytest.raises(HTTPException) as exc:
        await enrollments.enroll_student(str(uuid4()), fake_db, user)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_enroll_student_already_enrolled(
    fake_db,
    make_user,
    make_course,
    make_result,
) -> None:
    user = make_user(role=UserRole.STUDENT)
    course = make_course(uuid4())
    fake_db.execute.side_effect = [
        make_result(scalar=course),
        make_result(scalar=object()),
    ]

    with pytest.raises(HTTPException) as exc:
        await enrollments.enroll_student(str(course.id), fake_db, user)

    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_enroll_student_success(
    fake_db,
    make_user,
    make_course,
    make_result,
) -> None:
    user = make_user(role=UserRole.STUDENT)
    course = make_course(uuid4())
    fake_db.execute.side_effect = [
        make_result(scalar=course),
        make_result(scalar=None),
    ]

    async def refresh(enrollment) -> None:
        enrollment.id = uuid4()
        enrollment.enrolled_at = user.created_at

    fake_db.refresh.side_effect = refresh

    response = await enrollments.enroll_student(
        str(course.id),
        fake_db,
        user,
    )

    assert response.course_id == course.id
    assert response.student_id == user.id
    fake_db.commit.assert_awaited_once()
