import uuid
import pytest
from app.database.database import AsyncSessionLocal, Base, engine
from app.models.post import Post
from app.services.memory import MemoryService


@pytest.mark.asyncio
async def test_memory_has_seen_topic():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        agent_id = f"test-agent-mem-{uuid.uuid4()}"
        other_agent_id = f"test-agent-mem-{uuid.uuid4()}"
        title = f"Unique Breakthrough in Quantum AI {uuid.uuid4()}"

        memory = MemoryService(db)

        # Before post, memory should return False
        assert await memory.has_seen_topic(agent_id, title) is False

        # Add post for agent 1
        post = Post(
            agent_id=agent_id,
            topic_title=title,
            text="Sample post content",
            rationale="Sample rationale",
            sources='["https://example.com"]',
        )
        db.add(post)
        await db.commit()

        # After post, memory for agent 1 should return True
        assert await memory.has_seen_topic(agent_id, title) is True

        # Memory for agent 2 should still return False (agent isolation)
        assert await memory.has_seen_topic(other_agent_id, title) is False

