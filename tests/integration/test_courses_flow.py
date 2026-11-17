import pytest
from app.core.security import hash_password
from app.db.models.user import User, UserRole
from app.db.session import AsyncSessionFactory
from httpx import AsyncClient


@pytest.mark.integration
async def test_teacher_can_create_and_publish_course(
    client: AsyncClient,
    teacher: tuple[str, dict[str, str]],
    student: tuple[str, dict[str, str]],
) -> None:
    teacher_id, teacher_headers = teacher
    _, student_headers = student

    create_response = await client.post(
        "/api/v1/courses/",
        headers=teacher_headers,
        json={
            "title": "Integration Testing",
            "description": "Course created by integration test",
        },
    )

    assert create_response.status_code == 201

    course = create_response.json()
    course_id = course["id"]

    assert course["title"] == "Integration Testing"
    assert course["teacher_id"] == teacher_id
    assert course["is_published"] is False

    student_courses = await client.get(
        "/api/v1/courses/",
        headers=student_headers,
    )

    assert student_courses.status_code == 200
    assert student_courses.json() == []

    publish_response = await client.patch(
        f"/api/v1/courses/{course_id}",
        headers=teacher_headers,
        json={"is_published": True},
    )

    assert publish_response.status_code == 200
    assert publish_response.json()["is_published"] is True

    student_courses = await client.get(
        "/api/v1/courses/",
        headers=student_headers,
    )

    assert student_courses.status_code == 200
    assert len(student_courses.json()) == 1
    assert student_courses.json()[0]["id"] == course_id


@pytest.mark.integration
async def test_student_cannot_create_course(
    client: AsyncClient,
    student: tuple[str, dict[str, str]],
) -> None:
    _, student_headers = student

    response = await client.post(
        "/api/v1/courses/",
        headers=student_headers,
        json={
            "title": "Unauthorized Course",
            "description": "This course must not be created",
        },
    )

    assert response.status_code == 403


@pytest.mark.integration
async def test_student_cannot_access_unpublished_course(
    client: AsyncClient,
    teacher: tuple[str, dict[str, str]],
    student: tuple[str, dict[str, str]],
) -> None:
    _, teacher_headers = teacher
    _, student_headers = student

    create_response = await client.post(
        "/api/v1/courses/",
        headers=teacher_headers,
        json={"title": "Private Course"},
    )

    assert create_response.status_code == 201

    course_id = create_response.json()["id"]

    response = await client.get(
        f"/api/v1/courses/{course_id}",
        headers=student_headers,
    )

    assert response.status_code == 404


@pytest.mark.integration
async def test_teacher_cannot_modify_another_teachers_course(
    client: AsyncClient,
    teacher: tuple[str, dict[str, str]],
) -> None:
    _, owner_headers = teacher

    create_response = await client.post(
        "/api/v1/courses/",
        headers=owner_headers,
        json={"title": "Owner Course"},
    )

    assert create_response.status_code == 201

    course_id = create_response.json()["id"]

    other_teacher = User(
        email="other.teacher@example.com",
        full_name="Other Teacher",
        hashed_password=hash_password("Other-Password-123!"),
        role=UserRole.TEACHER,
    )

    async with AsyncSessionFactory() as session:
        session.add(other_teacher)
        await session.commit()

    login_response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "other.teacher@example.com",
            "password": "Other-Password-123!",
        },
    )

    assert login_response.status_code == 200

    other_headers = {
        "Authorization": (f"Bearer {login_response.json()['access_token']}")
    }

    response = await client.patch(
        f"/api/v1/courses/{course_id}",
        headers=other_headers,
        json={"title": "Modified by another teacher"},
    )

    assert response.status_code == 403
