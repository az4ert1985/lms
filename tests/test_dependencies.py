from unittest.mock import patch
from uuid import uuid4

import jwt
import pytest
from app.api import dependencies
from app.api.dependencies import get_current_user, require_roles
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.db.models import UserRole
from fastapi import HTTPException


def test_password_hashing() -> None:
    password = "Strong-Test-Password-123!"  # noqa: S105

    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong-password", hashed)


def test_jwt_token() -> None:
    token = create_access_token("test-user-id")

    payload = decode_access_token(token)

    assert payload["sub"] == "test-user-id"
    assert "exp" in payload


@pytest.mark.asyncio
async def test_get_current_user_success(fake_db, make_user, make_result) -> None:
    user = make_user(user_id=uuid4())
    fake_db.execute.return_value = make_result(scalar=user)

    with patch.object(
        dependencies,
        "decode_access_token",
        return_value={"sub": str(user.id)},
    ):
        result = await get_current_user("valid-token", fake_db)

    assert result is user
    fake_db.execute.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("token", "decoded"),
    [
        ("invalid-token", jwt.InvalidTokenError),
        ("invalid-uuid", {"sub": "not-a-uuid"}),
        ("missing-sub", {}),
        ("numeric-sub", {"sub": 123}),
    ],
)
async def test_get_current_user_invalid_token(
    fake_db,
    token,
    decoded,
) -> None:
    if isinstance(decoded, type) and issubclass(decoded, Exception):
        with (
            patch.object(
                dependencies,
                "decode_access_token",
                side_effect=decoded,
            ),
            pytest.raises(HTTPException) as exc,
        ):
            await get_current_user(token, fake_db)
    else:
        with (
            patch.object(
                dependencies,
                "decode_access_token",
                return_value=decoded,
            ),
            pytest.raises(HTTPException) as exc,
        ):
            await get_current_user(token, fake_db)

    assert exc.value.status_code == 401
    assert exc.value.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.asyncio
async def test_get_current_user_not_found(fake_db, make_result) -> None:
    fake_db.execute.return_value = make_result(scalar=None)

    with (
        patch.object(
            dependencies,
            "decode_access_token",
            return_value={"sub": str(uuid4())},
        ),
        pytest.raises(HTTPException) as exc,
    ):
        await get_current_user("valid-token", fake_db)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_inactive(fake_db, make_user, make_result) -> None:
    user = make_user(is_active=False)
    fake_db.execute.return_value = make_result(scalar=user)

    with (
        patch.object(
            dependencies,
            "decode_access_token",
            return_value={"sub": str(user.id)},
        ),
        pytest.raises(HTTPException) as exc,
    ):
        await get_current_user("valid-token", fake_db)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_require_roles_allowed(make_user) -> None:
    user = make_user(role=UserRole.TEACHER)
    checker = require_roles(UserRole.TEACHER, UserRole.ADMIN)

    result = await checker(user)

    assert result is user


@pytest.mark.asyncio
async def test_require_roles_forbidden(make_user) -> None:
    user = make_user(role=UserRole.STUDENT)
    checker = require_roles(UserRole.TEACHER)

    with pytest.raises(HTTPException) as exc:
        await checker(user)

    assert exc.value.status_code == 403
