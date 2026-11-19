from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from app.repositories.lesson_repository import LessonRepository


@pytest.mark.asyncio
@pytest.mark.parametrize("found", [True, False])
async def test_get_module_and_course(found):
    module, course = object(), object()
    result = MagicMock()
    result.one_or_none.return_value = (module, course) if found else None
    session = MagicMock()
    session.execute = AsyncMock(return_value=result)

    actual = await LessonRepository(session).get_module_and_course(uuid4())

    assert actual == ((module, course) if found else None)


@pytest.mark.asyncio
async def test_list_by_module():
    lessons = [object(), object()]
    scalars = MagicMock()
    scalars.all.return_value = lessons
    result = MagicMock()
    result.scalars.return_value = scalars
    session = MagicMock()
    session.execute = AsyncMock(return_value=result)

    assert await LessonRepository(session).list_by_module(uuid4()) == lessons
