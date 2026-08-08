import asyncio

from app.database.database import AsyncSessionLocal
from app.services.agent_engine import AgentEngine


async def main():
    print("[TEST] Opening database...", flush=True)

    async with AsyncSessionLocal() as db:
        print("[TEST] Creating AgentEngine...", flush=True)

        engine = AgentEngine(db)

        print("[TEST] Running multi-source discovery...", flush=True)

        decisions = await engine.discover_and_select(
            agent_id="integration-test-agent",
            persona_domain="AI Security",
        )

        print(
            f"[TEST] Received {len(decisions)} accepted decisions",
            flush=True,
        )

        for decision in decisions[:5]:
            print(
                f"{decision.score}/100 - "
                f"{decision.topic.title}",
                flush=True,
            )


if __name__ == "__main__":
    asyncio.run(main())