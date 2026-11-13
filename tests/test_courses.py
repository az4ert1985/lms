import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_courses_require_authentication(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/v1/courses/")

    assert response.status_code == 401
