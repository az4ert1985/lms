import pytest
from httpx import AsyncClient


@pytest.mark.integration
async def test_student_can_enroll_in_published_course(
    client: AsyncClient,
    teacher: tuple[str, dict[str, str]],
    student: tuple[str, dict[str, str]],
) -> None:
    _, teacher_headers = teacher
    student_id, student_headers = student

    create_response = await client.post(
        "/api/v1/courses/",
        headers=teacher_headers,
        json={"title": "Enrollment Course"},
    )

    assert create_response.status_code == 201

    course_id = create_response.json()["id"]

    publish_response = await client.patch(
        f"/api/v1/courses/{course_id}",
        headers=teacher_headers,
        json={"is_published": True},
    )

    assert publish_response.status_code == 200

    enrollment_response = await client.post(
        f"/api/v1/enrollments/{course_id}",
        headers=student_headers,
    )

    assert enrollment_response.status_code == 201

    enrollment = enrollment_response.json()

    assert enrollment["student_id"] == student_id
    assert enrollment["course_id"] == course_id

    duplicate_response = await client.post(
        f"/api/v1/enrollments/{course_id}",
        headers=student_headers,
    )

    assert duplicate_response.status_code == 409


@pytest.mark.integration
async def test_student_cannot_enroll_in_unpublished_course(
    client: AsyncClient,
    teacher: tuple[str, dict[str, str]],
    student: tuple[str, dict[str, str]],
) -> None:
    _, teacher_headers = teacher
    _, student_headers = student

    create_response = await client.post(
        "/api/v1/courses/",
        headers=teacher_headers,
        json={"title": "Unpublished Course"},
    )

    assert create_response.status_code == 201

    course_id = create_response.json()["id"]

    response = await client.post(
        f"/api/v1/enrollments/{course_id}",
        headers=student_headers,
    )

    assert response.status_code == 404


@pytest.mark.integration
async def test_enrollment_requires_authentication(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/enrollments/00000000-0000-0000-0000-000000000000",
    )

    assert response.status_code == 401
