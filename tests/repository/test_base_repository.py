from unittest.mock import AsyncMock, MagicMock

import pytest
from app.repositories.base import BaseRepository


@pytest.mark.asyncio
async def test_base_repository_operations():
    session = MagicMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    repository = BaseRepository(session)
    instance = object()

    repository.add(instance)
    await repository.delete(instance)
    await repository.commit()
    await repository.refresh(instance)

    session.add.assert_called_once_with(instance)
    session.delete.assert_awaited_once_with(instance)
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once_with(instance)
