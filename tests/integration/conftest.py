import uuid

import pytest
from app.core.security import hash_password
from app.db.models.user import User, UserRole
from app.db.session import AsyncSessionFactory, engine
from httpx import AsyncClient
from sqlalchemy import text

TEST_PASSWORD = "Integration-Test-Password-123!"  # noqa: S105


@pytest.fixture(autouse=True)
async def clean_database():
    await engine.dispose()
    async with engine.begin() as connection:
        await connection.execute(
            text(
                """
                TRUNCATE TABLE
                    lessons,
                    modules,
                    enrollments,
                    courses,
                    users
                RESTART IDENTITY CASCADE
                """
            )
        )


async def login(
    client: AsyncClient,
    email: str,
) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def teacher(
    client: AsyncClient,
) -> tuple[str, dict[str, str]]:
    teacher_id = uuid.uuid4()

    user = User(
        id=teacher_id,
        email="teacher@example.com",
        full_name="Integration Teacher",
        hashed_password=hash_password(TEST_PASSWORD),
        role=UserRole.TEACHER,
    )

    async with AsyncSessionFactory() as session:
        session.add(user)
        await session.commit()

    headers = await login(client, "teacher@example.com")

    return str(teacher_id), headers


@pytest.fixture
async def student(
    client: AsyncClient,
) -> tuple[str, dict[str, str]]:
    response = await client.post(
        "/api/v1/users/",
        json={
            "email": "student@example.com",
            "full_name": "Integration Student",
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 201

    student_id = response.json()["id"]
    headers = await login(client, "student@example.com")

    return student_id, headers
