import asyncio

from app.database.database import AsyncSessionLocal
from app.services.agent_engine import AgentEngine
from app.services.llm.ollama_provider import OllamaProvider
from app.services.persona_writer import PersonaWriter
from app.services.post_publisher import PostPublisher


async def main():
    async with AsyncSessionLocal() as db:
        print("[TEST] Discovering topics...", flush=True)

        engine = AgentEngine(db)

        decisions = await engine.discover_and_select(
            agent_id="integration-test-agent",
            persona_domain="AI Security",
        )

        if not decisions:
            print("[TEST] No acceptable topics.")
            return

        decision = decisions[0]
        topic = decision.topic

        print(
            f"[TEST] Selected: {topic.title} "
            f"({decision.score}/100)",
            flush=True,
        )

        print("[TEST] Generating post...", flush=True)

        writer = PersonaWriter(
            OllamaProvider()
        )

        text = await writer.generate_post(
            topic=topic,
            persona_name="Ada",
            persona_domain="AI Security",
        )

        print("[TEST] Publishing...", flush=True)

        publisher = PostPublisher(db)

        post = await publisher.publish(
            agent_id="integration-test-agent",
            topic=topic,
            decision=decision,
            text=text,
        )

        print(
            f"[TEST] Published successfully: {post.id}",
            flush=True,
        )


if __name__ == "__main__":
    asyncio.run(main())