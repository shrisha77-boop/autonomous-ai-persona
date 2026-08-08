from sqlalchemy.ext.asyncio import AsyncSession

from app.services.editorial_engine import EditorialEngine
from app.services.memory import MemoryService
from app.services.sources.hackernews import discover_hackernews_topics


class AgentEngine:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.editorial_engine = EditorialEngine()
        self.memory = MemoryService(db)

    async def discover_and_select(
        self,
        agent_id: str,
        persona_domain: str,
    ):
        topics = discover_hackernews_topics(limit=20)

        decisions = []

        for topic in topics:
            # Memory check
            already_seen = await self.memory.has_seen_topic(
                agent_id=agent_id,
                title=topic.title,
            )

            if already_seen:
                continue

            # Editorial judgment
            decision = self.editorial_engine.evaluate(
                topic=topic,
                persona_domain=persona_domain,
            )

            decisions.append(decision)

        # Highest scoring acceptable topic first
        accepted = [
            decision
            for decision in decisions
            if decision.decision == "ACCEPT"
        ]

        accepted.sort(
            key=lambda decision: decision.score,
            reverse=True,
        )

        return accepted