import asyncio

from app.core.config import settings
from app.database.database import AsyncSessionLocal
from app.services.agent_engine import AgentEngine
from app.services.llm.ollama_provider import OllamaProvider
from app.services.llm.provider import MockLLMProvider
from app.services.persona_writer import PersonaWriter
from app.services.post_publisher import PostPublisher

_active_tasks: dict[str, asyncio.Task] = {}


async def run_agent_cycle(
    agent_id: str,
    persona_name: str,
    persona_domain: str,
):
    print(
        f"[SignalForge] Starting cycle for {persona_name}",
        flush=True,
    )

    async with AsyncSessionLocal() as db:
        engine = AgentEngine(db)

        decisions = await engine.discover_and_select(
            agent_id=agent_id,
            persona_domain=persona_domain,
        )

        if not decisions:
            print(
                f"[SignalForge] No suitable topic for {persona_name}",
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

        try:
            print(
                "[SignalForge] Generating post with Ollama...",
                flush=True,
            )
            writer = PersonaWriter(OllamaProvider())
            text = await writer.generate_post(
                topic=topic,
                persona_name=persona_name,
                persona_domain=persona_domain,
            )
            print(
                "[SignalForge] LLM generation complete.",
                flush=True,
            )
        except Exception as exc:
            print(
                f"[SignalForge] Ollama generation unavailable ({exc}). Using fallback provider...",
                flush=True,
            )
            writer = PersonaWriter(MockLLMProvider())
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
    interval_seconds: int | None = None,
):
    interval = interval_seconds or settings.PUBLISH_INTERVAL_SECONDS
    print(
        f"[SignalForge] Autonomous loop started for {persona_name} (interval: {interval}s)",
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
                f"[SignalForge] Autonomous loop stopped for {persona_name}",
                flush=True,
            )
            raise

        except Exception as exc:
            print(
                f"[SignalForge] Agent cycle failed: {exc}",
                flush=True,
            )

        print(
            f"[SignalForge] Sleeping for {interval} seconds...",
            flush=True,
        )

        await asyncio.sleep(interval)


def start_agent(
    agent_id: str,
    persona_name: str,
    persona_domain: str,
    interval_seconds: int | None = None,
):
    existing_task = _active_tasks.get(agent_id)

    if existing_task and not existing_task.done():
        print(
            f"[SignalForge] Agent {agent_id} is already running.",
            flush=True,
        )
        return

    print(
        f"[SignalForge] Starting autonomous task for {persona_name} ({agent_id})",
        flush=True,
    )

    task = asyncio.create_task(
        agent_loop(
            agent_id=agent_id,
            persona_name=persona_name,
            persona_domain=persona_domain,
            interval_seconds=interval_seconds,
        )
    )

    _active_tasks[agent_id] = task

    print(
        f"[SignalForge] Autonomous task created for {persona_name}",
        flush=True,
    )


def stop_agent(agent_id: str):
    task = _active_tasks.pop(agent_id, None)
    if task and not task.done():
        task.cancel()
        print(f"[SignalForge] Cancelled autonomous task for agent {agent_id}", flush=True)