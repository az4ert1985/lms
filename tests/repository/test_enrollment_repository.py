from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from app.repositories.enrollment_repository import EnrollmentRepository


@pytest.mark.asyncio
@pytest.mark.parametrize("found", [True, False])
async def test_get_published_course(found, make_user, make_course):
    user = make_user()
    course = make_course(user.id) if found else None
    result = MagicMock()
    result.scalar_one_or_none.return_value = course
    session = MagicMock()
    session.execute = AsyncMock(return_value=result)

    assert await EnrollmentRepository(session).get_published_course(uuid4()) is course


@pytest.mark.asyncio
@pytest.mark.parametrize("found", [True, False])
async def test_get_by_student_and_course(found):
    enrollment = object() if found else None
    result = MagicMock()
    result.scalar_one_or_none.return_value = enrollment
    session = MagicMock()
    session.execute = AsyncMock(return_value=result)

    actual = await EnrollmentRepository(session).get_by_student_and_course(
        uuid4(), uuid4()
    )

    assert actual is enrollment
