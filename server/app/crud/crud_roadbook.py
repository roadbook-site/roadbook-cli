from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import CRUDBase
from ..models.roadbook import Roadbook
from ..schemas.roadbook import RoadbookCreate, RoadbookUpdate

class CRUDRoadbook(CRUDBase[Roadbook, RoadbookCreate, RoadbookUpdate]):
    async def get_by_id(self, db: AsyncSession, *, id: str) -> Optional[Roadbook]:
        result = await db.execute(select(Roadbook).filter(Roadbook.id == id))
        return result.scalars().first()

    async def get_multi_by_owner(
        self, db: AsyncSession, *, owner_id: str, skip: int = 0, limit: int = 100
    ) -> List[Roadbook]:
        result = await db.execute(
            select(Roadbook)
            .filter(Roadbook.author == owner_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

roadbook = CRUDRoadbook(Roadbook)
