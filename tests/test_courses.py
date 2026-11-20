from uuid import uuid4

import pytest
from app.api.dependencies import build_course_service
from app.api.v1 import courses
from app.db.models import UserRole
from app.schemas.course import CourseCreate, CourseUpdate
from fastapi import HTTPException
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_courses_require_authentication(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/v1/courses/")

    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("role", "expected_count"),
    [
        (UserRole.ADMIN, 2),
        (UserRole.TEACHER, 2),
        (UserRole.STUDENT, 2),
    ],
)
async def test_list_courses(
    fake_db,
    make_user,
    make_course,
    make_result,
    role,
    expected_count,
) -> None:
    user = make_user(role=role)
    course_list = [
        make_course(user.id),
        make_course(user.id),
    ]
    fake_db.execute.return_value = make_result(rows=course_list)

    response = await courses.list_courses(build_course_service(fake_db), user)

    assert len(response) == expected_count


@pytest.mark.asyncio
async def test_create_course_success(fake_db, make_user) -> None:
    user = make_user(role=UserRole.TEACHER)

    async def refresh(course) -> None:
        course.id = uuid4()
        course.created_at = user.created_at
        course.is_published = False

    fake_db.refresh.side_effect = refresh

    response = await courses.create_course(
        CourseCreate(title="Python course", description="Description"),
        build_course_service(fake_db),
        user,
    )

    assert response.title == "Python course"
    assert response.teacher_id == user.id
    fake_db.add.assert_called_once()
    fake_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_course_student_forbidden(fake_db, make_user) -> None:
    user = make_user(role=UserRole.STUDENT)

    with pytest.raises(HTTPException) as exc:
        await courses.create_course(
            CourseCreate(title="Python course"),
            build_course_service(fake_db),
            user,
        )

    assert exc.value.status_code == 403
    fake_db.add.assert_not_called()


@pytest.mark.asyncio
async def test_get_accessible_course_without_user_id(fake_db) -> None:
    with pytest.raises(HTTPException) as exc:
        await courses.get_accessible_course(
            uuid4(),
            build_course_service(fake_db),
            object(),
        )

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_get_accessible_course_not_found(fake_db, make_result, make_user) -> None:
    fake_db.execute.return_value = make_result(scalar=None)
    user = make_user()

    with pytest.raises(HTTPException) as exc:
        await courses.get_accessible_course(
            uuid4(), build_course_service(fake_db), user
        )

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_accessible_course_success(
    fake_db,
    make_result,
    make_user,
    make_course,
) -> None:
    user = make_user()
    course = make_course(user.id)
    fake_db.execute.return_value = make_result(scalar=course)

    result = await courses.get_accessible_course(
        course.id, build_course_service(fake_db), user
    )

    assert result is course


@pytest.mark.asyncio
async def test_get_course_student_unpublished(
    fake_db,
    make_result,
    make_user,
    make_course,
) -> None:
    user = make_user(role=UserRole.STUDENT)
    course = make_course(user.id, is_published=False)
    fake_db.execute.return_value = make_result(scalar=course)

    with pytest.raises(HTTPException) as exc:
        await courses.get_course(course.id, build_course_service(fake_db), user)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_course_teacher_forbidden(
    fake_db,
    make_result,
    make_user,
    make_course,
) -> None:
    user = make_user(role=UserRole.TEACHER)
    course = make_course(uuid4())
    fake_db.execute.return_value = make_result(scalar=course)

    with pytest.raises(HTTPException) as exc:
        await courses.get_course(course.id, build_course_service(fake_db), user)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_get_course_admin_success(
    fake_db,
    make_result,
    make_user,
    make_course,
) -> None:
    user = make_user(role=UserRole.ADMIN)
    course = make_course(uuid4())
    fake_db.execute.return_value = make_result(scalar=course)

    response = await courses.get_course(course.id, build_course_service(fake_db), user)

    assert response.id == course.id


@pytest.mark.asyncio
async def test_update_course_forbidden(
    fake_db,
    make_result,
    make_user,
    make_course,
) -> None:
    user = make_user(role=UserRole.TEACHER)
    course = make_course(uuid4())
    fake_db.execute.return_value = make_result(scalar=course)

    with pytest.raises(HTTPException) as exc:
        await courses.update_course(
            course.id,
            CourseUpdate(title="New title"),
            build_course_service(fake_db),
            user,
        )

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_update_course_success(
    fake_db,
    make_result,
    make_user,
    make_course,
) -> None:
    user = make_user(role=UserRole.TEACHER)
    course = make_course(user.id)
    fake_db.execute.return_value = make_result(scalar=course)

    response = await courses.update_course(
        course.id,
        CourseUpdate(title="Updated title", is_published=True),
        build_course_service(fake_db),
        user,
    )

    assert response.title == "Updated title"
    assert response.is_published is True
    fake_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_course_forbidden(
    fake_db,
    make_result,
    make_user,
    make_course,
) -> None:
    user = make_user(role=UserRole.TEACHER)
    course = make_course(uuid4())
    fake_db.execute.return_value = make_result(scalar=course)

    with pytest.raises(HTTPException) as exc:
        await courses.delete_course(course.id, build_course_service(fake_db), user)

    assert exc.value.status_code == 403
    fake_db.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_course_success(
    fake_db,
    make_result,
    make_user,
    make_course,
) -> None:
    user = make_user(role=UserRole.ADMIN)
    course = make_course(uuid4())
    fake_db.execute.return_value = make_result(scalar=course)

    await courses.delete_course(course.id, build_course_service(fake_db), user)

    fake_db.delete.assert_awaited_once_with(course)
    fake_db.commit.assert_awaited_once()
