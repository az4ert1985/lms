from unittest.mock import AsyncMock, MagicMock

import pytest
from app.repositories.user_repository import UserRepository


@pytest.mark.asyncio
async def test_get_by_email_found(make_user):
    user = make_user()
    session = MagicMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = user
    session.execute = AsyncMock(return_value=result)

    found = await UserRepository(session).get_by_email(user.email)

    assert found is user
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_by_email_missing():
    session = MagicMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=result)

    assert await UserRepository(session).get_by_email("missing@example.com") is None
