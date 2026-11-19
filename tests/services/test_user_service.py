from unittest.mock import AsyncMock, MagicMock

import pytest
from app.schemas.user import UserCreate
from app.services import user_service
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_create_user_success(monkeypatch):
    users = MagicMock()
    users.get_by_email = AsyncMock(return_value=None)
    users.add = MagicMock()
    users.commit = AsyncMock()
    users.refresh = AsyncMock()
    monkeypatch.setattr(user_service, "hash_password", lambda _password: "hashed")
    payload = UserCreate(
        email="new@example.com", full_name="New User", password="secret"
    )

    user = await user_service.UserService(users).create_user(payload)

    assert user.email == "new@example.com"
    assert user.hashed_password == "hashed"
    users.add.assert_called_once_with(user)
    users.commit.assert_awaited_once()
    users.refresh.assert_awaited_once_with(user)


@pytest.mark.asyncio
async def test_create_user_duplicate():
    users = MagicMock()
    users.get_by_email = AsyncMock(return_value=object())

    with pytest.raises(HTTPException) as exc:
        await user_service.UserService(users).create_user(
            UserCreate(email="taken@example.com", full_name="Taken", password="secret")
        )

    assert exc.value.status_code == 409
