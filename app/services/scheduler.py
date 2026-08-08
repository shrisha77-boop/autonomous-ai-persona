import asyncio

from app.database.database import AsyncSessionLocal
from app.services.agent_engine import AgentEngine
from app.services.llm.provider import MockLLMProvider
from app.services.persona_writer import PersonaWriter
from app.services.post_publisher import PostPublisher


# Development interval.
# Later we'll make this configurable through .env.
PUBLISH_INTERVAL_SECONDS = 60


_active_tasks: dict[str, asyncio.Task] = {}


async def run_agent_cycle(
    agent_id: str,
    persona_name: str,
    persona_domain: str,
):
    async with AsyncSessionLocal() as db:
        engine = AgentEngine(db)

        decisions = await engine.discover_and_select(
            agent_id=agent_id,
            persona_domain=persona_domain,
        )

        if not decisions:
            print(
                f"[SignalForge] No suitable topic for {agent_name}",
                flush=True,
            )
            return

        decision = decisions[0]
        topic = decision.topic

        print(
            f"[SignalForge] Selected: {topic.title} "
            f"({decision.score}/100)",
            flush=True,
        )

        writer = PersonaWriter(
            MockLLMProvider()
        )

        text = await writer.generate_post(
            topic=topic,
            persona_name=persona_name,
            persona_domain=persona_domain,
        )

        publisher = PostPublisher(db)

        post = await publisher.publish(
            agent_id=agent_id,
            topic=topic,
            decision=decision,
            text=text,
        )

        print(
            f"[SignalForge] Published post {post.id}",
            flush=True,
        )


async def agent_loop(
    agent_id: str,
    persona_name: str,
    persona_domain: str,
):
    print(
        f"[SignalForge] Autonomous loop started for "
        f"{persona_name}",
        flush=True,
    )

    while True:
        try:
            await run_agent_cycle(
                agent_id=agent_id,
                persona_name=persona_name,
                persona_domain=persona_domain,
            )

        except asyncio.CancelledError:
            print(
                f"[SignalForge] Autonomous loop stopped for "
                f"{persona_name}",
                flush=True,
            )
            raise

        except Exception as exc:
            print(
                f"[SignalForge] Agent cycle failed: {exc}",
                flush=True,
            )

        await asyncio.sleep(PUBLISH_INTERVAL_SECONDS)


def start_agent(
    agent_id: str,
    persona_name: str,
    persona_domain: str,
):
    existing_task = _active_tasks.get(agent_id)

    if existing_task and not existing_task.done():
        return

    task = asyncio.create_task(
        agent_loop(
            agent_id=agent_id,
            persona_name=persona_name,
            persona_domain=persona_domain,
        )
    )

    _active_tasks[agent_id] = task