import pytest
from httpx import AsyncClient

TEST_PASSWORD = "Integration-Test-Password-123!"  # noqa: S105


@pytest.mark.integration
async def test_registration_login_and_get_current_user(
    client: AsyncClient,
) -> None:
    registration_response = await client.post(
        "/api/v1/users/",
        json={
            "email": "new.student@example.com",
            "full_name": "New Student",
            "password": TEST_PASSWORD,
        },
    )

    assert registration_response.status_code == 201

    registered_user = registration_response.json()

    assert registered_user["email"] == "new.student@example.com"
    assert registered_user["full_name"] == "New Student"
    assert registered_user["role"] == "student"
    assert "hashed_password" not in registered_user

    login_response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "new.student@example.com",
            "password": TEST_PASSWORD,
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    assert token

    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == registered_user["id"]
    assert response.json()["email"] == "new.student@example.com"


@pytest.mark.integration
async def test_registration_rejects_duplicate_email(
    client: AsyncClient,
) -> None:
    payload = {
        "email": "duplicate@example.com",
        "full_name": "Duplicate User",
        "password": TEST_PASSWORD,
    }

    first_response = await client.post(
        "/api/v1/users/",
        json=payload,
    )

    second_response = await client.post(
        "/api/v1/users/",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


@pytest.mark.integration
async def test_login_rejects_invalid_password(
    client: AsyncClient,
) -> None:
    await client.post(
        "/api/v1/users/",
        json={
            "email": "login@example.com",
            "full_name": "Login User",
            "password": TEST_PASSWORD,
        },
    )

    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "login@example.com",
            "password": "Wrong-Password-123!",
        },
    )

    assert response.status_code == 401
