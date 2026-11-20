from datetime import UTC, datetime
from unittest.mock import patch
from uuid import uuid4

import pytest
from app.api.dependencies import build_user_service
from app.api.v1 import users
from app.db.models import UserRole
from app.schemas.user import UserCreate
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_create_user_duplicate_email(
    fake_db,
    make_result,
) -> None:
    fake_db.execute.return_value = make_result(scalar=object())

    with pytest.raises(HTTPException) as exc:
        await users.create_user(
            UserCreate(
                email="existing@example.com",
                full_name="Existing User",
                password="password",
            ),
            build_user_service(fake_db),
        )

    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_create_user_success(fake_db, make_result) -> None:
    fake_db.execute.return_value = make_result(scalar=None)

    async def refresh(user) -> None:
        user.id = uuid4()
        user.is_active = True
        user.created_at = datetime.now(UTC)

    fake_db.refresh.side_effect = refresh

    with patch(
        "app.services.user_service.hash_password",
        return_value="hashed-password",
    ):
        response = await users.create_user(
            UserCreate(
                email="new@example.com",
                full_name="New User",
                password="password",
            ),
            build_user_service(fake_db),
        )

    assert response.email == "new@example.com"
    assert response.role == UserRole.STUDENT
    fake_db.add.assert_called_once()
    fake_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_me(make_user) -> None:
    user = make_user(role=UserRole.STUDENT)

    response = await users.get_me(user)

    assert response.id == user.id
    assert response.email == user.email
