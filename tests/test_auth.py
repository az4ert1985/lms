from types import SimpleNamespace
from unittest.mock import patch

import pytest
from app.api.v1 import auth
from app.db.models import UserRole
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_login_success(fake_db, make_user, make_result) -> None:
    user = make_user(role=UserRole.STUDENT)
    fake_db.execute.return_value = make_result(scalar=user)
    form = SimpleNamespace(
        username=user.email,
        password="correct-password",  # noqa: S106
    )

    with (
        patch.object(auth, "verify_password", return_value=True),
        patch.object(auth, "create_access_token", return_value="test-token"),
    ):
        response = await auth.login(fake_db, form)

    assert response.access_token == "test-token"  # noqa: S105
    assert response.token_type == "bearer"  # noqa: S105


@pytest.mark.asyncio
async def test_login_user_not_found(fake_db, make_result) -> None:
    fake_db.execute.return_value = make_result(scalar=None)
    form = SimpleNamespace(
        username="missing@example.com",
        password="password",  # noqa: S106
    )

    with pytest.raises(HTTPException) as exc:
        await auth.login(fake_db, form)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_login_inactive_user(fake_db, make_user, make_result) -> None:
    user = make_user(is_active=False)
    fake_db.execute.return_value = make_result(scalar=user)
    form = SimpleNamespace(username=user.email, password="password")  # noqa: S106

    with (
        patch.object(auth, "verify_password", return_value=True),
        pytest.raises(HTTPException) as exc,
    ):
        await auth.login(fake_db, form)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_login_wrong_password(fake_db, make_user, make_result) -> None:
    user = make_user()
    fake_db.execute.return_value = make_result(scalar=user)
    form = SimpleNamespace(username=user.email, password="wrong-password")  # noqa: S106

    with (
        patch.object(auth, "verify_password", return_value=False),
        pytest.raises(HTTPException) as exc,
    ):
        await auth.login(fake_db, form)

    assert exc.value.status_code == 401
