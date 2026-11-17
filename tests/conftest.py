from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from app.db.models.user import UserRole
from app.main import app
from httpx import ASGITransport, AsyncClient


class FakeResult:
    """Мінімальна імітація результату SQLAlchemy execute()."""

    def __init__(
        self,
        scalar: object | None = None,
        rows: list[object] | None = None,
        one: object | None = None,
    ) -> None:
        self.scalar = scalar
        self.rows = rows or []
        self.one = one

    def scalar_one_or_none(self) -> object | None:
        return self.scalar

    def scalars(self) -> FakeResult:
        return self

    def all(self) -> list[object]:
        return self.rows

    def one_or_none(self) -> object | None:
        return self.one


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as test_client:
        yield test_client


@pytest.fixture
def fake_db() -> MagicMock:
    """Мок AsyncSession без підключення до бази даних."""
    db = MagicMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.delete = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.fixture
def make_result():
    """Фабрика результатів для підставляння y fake_db.execute."""

    def factory(
        scalar: object | None = None,
        rows: list[object] | None = None,
        one: object | None = None,
    ) -> FakeResult:
        return FakeResult(scalar=scalar, rows=rows, one=one)

    return factory


@pytest.fixture
def make_user():
    def factory(
        role: UserRole = UserRole.STUDENT,
        *,
        user_id: UUID | None = None,
        email: str = "user@example.com",
        is_active: bool = True,
        password_hash: str = "hashed-password",  # noqa: S107
    ) -> SimpleNamespace:
        return SimpleNamespace(
            id=user_id or uuid4(),
            email=email,
            full_name="Test User",
            hashed_password=password_hash,
            role=role,
            is_active=is_active,
            created_at=datetime.now(UTC),
        )

    return factory


@pytest.fixture
def make_course():
    def factory(
        teacher_id: UUID,
        *,
        course_id: UUID | None = None,
        is_published: bool = True,
    ) -> SimpleNamespace:
        return SimpleNamespace(
            id=course_id or uuid4(),
            title="Python course",
            description="Test course description",
            teacher_id=teacher_id,
            is_published=is_published,
            created_at=datetime.now(UTC),
        )

    return factory


@pytest.fixture
def make_module():
    def factory(
        course_id: UUID,
        *,
        module_id: UUID | None = None,
    ) -> SimpleNamespace:
        return SimpleNamespace(
            id=module_id or uuid4(),
            course_id=course_id,
            title="Python basics",
            position=0,
        )

    return factory


@pytest.fixture
def make_lesson():
    def factory(
        module_id: UUID,
        *,
        lesson_id: UUID | None = None,
    ) -> SimpleNamespace:
        return SimpleNamespace(
            id=lesson_id or uuid4(),
            module_id=module_id,
            title="Introduction",
            content="Lesson content",
            position=0,
        )

    return factory
