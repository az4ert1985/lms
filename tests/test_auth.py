from types import SimpleNamespace
from unittest.mock import patch

import pytest
from app.api.v1 import auth
from app.api.v1.users import create_user
from app.db.models import UserRole
from app.schemas.user import UserCreate
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_login_success(fake_db, make_user, make_result) -> None:
    user = make_user(role=UserRole.STUDENT)
    fake_db.execute.return_value = make_result(scalar=user)

    form = SimpleNamespace(
        username=user.email,
        password="correct-password",
    )

    with (
        patch(
            "app.services.auth_service.verify_password",
            return_value=True,
        ),
        patch(
            "app.services.auth_service.create_access_token",
            return_value="test-token",
        ),
    ):
        response = await auth.login(fake_db, form)

    assert response.access_token == "test-token"
    assert response.token_type == "bearer"


@pytest.mark.asyncio
async def test_login_user_not_found(fake_db, make_result) -> None:
    fake_db.execute.return_value = make_result(scalar=None)

    form = SimpleNamespace(
        username="missing@example.com",
        password="password",
    )

    with pytest.raises(HTTPException) as exc:
        await auth.login(fake_db, form)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_login_inactive_user(fake_db, make_user, make_result) -> None:
    user = make_user(is_active=False)
    fake_db.execute.return_value = make_result(scalar=user)

    form = SimpleNamespace(
        username=user.email,
        password="password",
    )

    with (
        patch(
            "app.services.auth_service.verify_password",
            return_value=True,
        ),
        pytest.raises(HTTPException) as exc,
    ):
        await auth.login(fake_db, form)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_login_wrong_password(fake_db, make_user, make_result) -> None:
    user = make_user()
    fake_db.execute.return_value = make_result(scalar=user)

    form = SimpleNamespace(
        username=user.email,
        password="wrong-password",
    )

    with (
        patch(
            "app.services.auth_service.verify_password",
            return_value=False,
        ),
        pytest.raises(HTTPException) as exc,
    ):
        await auth.login(fake_db, form)

    assert exc.value.status_code == 401


@pytest.mark.parametrize("requested_role", ["admin", "teacher"])
async def test_registration_always_assigns_student_role(
    requested_role: str,
    fake_db,
    make_result,
    make_user,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Public registration must always assign the STUDENT role."""

    payload = UserCreate.model_validate(
        {
            "email": f"{requested_role}@example.com",
            "full_name": "Test User",
            "password": "Strong-Test-Password-123!",
            "role": requested_role,
        }
    )

    fake_db.execute.return_value = make_result()

    monkeypatch.setattr(
        "app.services.user_service.hash_password",
        lambda _: "hashed-password",
    )

    async def refresh_user(user: object) -> None:
        test_user = make_user(
            role=UserRole.STUDENT,
            email=f"{requested_role}@example.com",
        )
        user.id = test_user.id
        user.is_active = test_user.is_active
        user.created_at = test_user.created_at

    fake_db.refresh.side_effect = refresh_user

    response = await create_user(payload, fake_db)

    created_user = fake_db.add.call_args.args[0]

    assert created_user.role == UserRole.STUDENT
    assert response.role == UserRole.STUDENT

    fake_db.execute.assert_awaited_once()
    fake_db.add.assert_called_once_with(created_user)
    fake_db.commit.assert_awaited_once()
    fake_db.refresh.assert_awaited_once_with(created_user)


async def test_registration_without_role_assigns_student(
    fake_db,
    make_result,
    make_user,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Registration without an explicit role must assign STUDENT."""

    payload = UserCreate(
        email="student@example.com",
        full_name="Test User",
        password="Strong-Test-Password-123!",
    )

    fake_db.execute.return_value = make_result()

    monkeypatch.setattr(
        "app.services.user_service.hash_password",
        lambda _: "hashed-password",
    )

    async def refresh_user(user: object) -> None:
        test_user = make_user(email="student@example.com")
        user.id = test_user.id
        user.is_active = test_user.is_active
        user.created_at = test_user.created_at

    fake_db.refresh.side_effect = refresh_user

    response = await create_user(payload, fake_db)

    created_user = fake_db.add.call_args.args[0]

    assert created_user.role == UserRole.STUDENT
    assert response.role == UserRole.STUDENT
