from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post import Post


class MemoryService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def has_seen_topic(
        self,
        agent_id: str,
        title: str,
    ) -> bool:
        result = await self.db.execute(
            select(Post).where(
                Post.agent_id == agent_id,
                Post.text.ilike(f"%{title}%"),
            )
        )

        return result.scalar_one_or_none() is not None