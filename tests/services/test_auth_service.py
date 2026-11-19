from unittest.mock import AsyncMock, MagicMock

import pytest
from app.db.models.user import UserRole
from app.services import auth_service
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_login_success(monkeypatch, make_user):
    user = make_user(UserRole.STUDENT)
    users = MagicMock()
    users.get_by_email = AsyncMock(return_value=user)
    monkeypatch.setattr(
        auth_service, "verify_password", lambda _password, _hashed: True
    )
    monkeypatch.setattr(auth_service, "create_access_token", lambda _subject: "token")

    assert await auth_service.AuthService(users).login(user.email, "secret") == "token"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("user_state", "password_valid"),
    [(None, True), ("inactive", True), ("active", False)],
)
async def test_login_rejected(monkeypatch, make_user, user_state, password_valid):
    user = None if user_state is None else make_user(is_active=user_state == "active")
    users = MagicMock()
    users.get_by_email = AsyncMock(return_value=user)
    monkeypatch.setattr(
        auth_service, "verify_password", lambda _password, _hashed: password_valid
    )

    with pytest.raises(HTTPException) as exc:
        await auth_service.AuthService(users).login("user@example.com", "wrong")

    assert exc.value.status_code == 401
