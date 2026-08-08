import asyncio

from app.services.scheduler import start_agent


async def main():
    print("[TEST] Starting integrated autonomous agent...", flush=True)

    start_agent(
        agent_id="integration-test-agent",
        persona_name="Ada",
        persona_domain="AI Security",
    )

    print("[TEST] Autonomous task started.", flush=True)

    await asyncio.sleep(90)

    print("[TEST] Test duration complete.", flush=True)


if __name__ == "__main__":
    asyncio.run(main())