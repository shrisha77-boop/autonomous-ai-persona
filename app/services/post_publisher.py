import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post import Post
from app.models.topic import TopicCandidate
from app.services.editorial_engine import EditorialDecision


class PostPublisher:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def publish(
        self,
        agent_id: str,
        topic: TopicCandidate,
        decision: EditorialDecision,
        text: str,
    ) -> Post:

        rationale = (
            f"Selected candidate topic '{topic.title}' with editorial score "
            f"{decision.score}/100. "
            f"Current relevance: {decision.reason}. "
            f"Selected over competing candidate topics in this cycle due to highest domain alignment "
            f"and source credibility ({topic.source_name})."
        )

        sources = [topic.source_url] if topic.source_url else []

        post = Post(
            agent_id=agent_id,
            topic_title=topic.title,
            text=text,
            rationale=rationale,
            sources=json.dumps(sources),
        )

        self.db.add(post)

        await self.db.commit()
        await self.db.refresh(post)

        return post