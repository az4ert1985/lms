from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from app.repositories.module_repository import ModuleRepository


@pytest.mark.asyncio
async def test_list_by_course():
    modules = [object()]
    scalars = MagicMock()
    scalars.all.return_value = modules
    result = MagicMock()
    result.scalars.return_value = scalars
    session = MagicMock()
    session.execute = AsyncMock(return_value=result)

    assert await ModuleRepository(session).list_by_course(uuid4()) == modules
