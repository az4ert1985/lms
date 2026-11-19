from uuid import UUID

from app.db.models.module import Module
from app.repositories.base import BaseRepository
from sqlalchemy import select


class ModuleRepository(BaseRepository):
    async def list_by_course(self, course_id: UUID) -> list[Module]:
        result = await self.session.execute(
            select(Module)
            .where(Module.course_id == course_id)
            .order_by(Module.position)
        )
        return list(result.scalars().all())
