import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database.database import Base, engine
from app.services.scheduler import run_agent_cycle, stop_agent


@pytest.mark.asyncio
async def test_hackathon_evaluator_simulation():
    """
    Locally simulates the exact Hackathon Evaluator workflow:
    1. Initialize agent via POST /api/agent/init
    2. Receive agentId
    3. Run cycle 1 automatically
    4. GET /api/agent/feed?agentId=... and assert API contract compliance
    5. Run cycle 2 automatically
    6. GET /api/agent/feed?agentId=... again and assert post accumulation & deduplication
    """
    print("\n[EVALUATOR SIMULATION] Step 1: Initializing DB schema...", flush=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        # Step 2: POST /api/agent/init
        print("[EVALUATOR SIMULATION] Step 2: Calling POST /api/agent/init...", flush=True)
        init_res = await client.post(
            "/api/agent/init",
            json={
                "persona": {
                    "name": "Ada",
                    "domain": "AI Security",
                }
            },
        )
        assert init_res.status_code == 200, f"Init failed: {init_res.text}"
        data = init_res.json()
        assert "agentId" in data, "agentId missing from response"
        agent_id = data["agentId"]
        print(f"[EVALUATOR SIMULATION] Received agentId: {agent_id}", flush=True)

        # Step 3: Run Cycle 1 explicitly
        print("[EVALUATOR SIMULATION] Step 3: Executing Cycle 1...", flush=True)
        await run_agent_cycle(
            agent_id=agent_id,
            persona_name="Ada",
            persona_domain="AI Security",
        )

        # Step 4: GET /api/agent/feed?agentId=...
        print("[EVALUATOR SIMULATION] Step 4: Calling GET /api/agent/feed...", flush=True)
        feed_res1 = await client.get(f"/api/agent/feed?agentId={agent_id}")
        assert feed_res1.status_code == 200, f"Feed failed: {feed_res1.text}"
        feed1 = feed_res1.json()

        assert "posts" in feed1, "'posts' key missing from feed response"
        posts1 = feed1["posts"]
        print(f"[EVALUATOR SIMULATION] Feed returned {len(posts1)} post(s) after Cycle 1.", flush=True)

        if len(posts1) > 0:
            post = posts1[0]
            assert "id" in post and len(post["id"]) > 0, "Post ID missing"
            assert "createdAt" in post and len(post["createdAt"]) > 0, "createdAt missing"
            assert "text" in post and len(post["text"]) > 0, "text missing"
            assert "rationale" in post and len(post["rationale"]) > 0, "rationale missing"
            assert "sources" in post and isinstance(post["sources"], list), "sources missing or not a list"
            assert len(post["sources"]) > 0, "sources list is empty"

            print(f"   - Post ID: {post['id']}")
            print(f"   - Timestamp: {post['createdAt']}")
            print(f"   - Rationale: {post['rationale'][:80]}...")
            print(f"   - Sources: {post['sources']}")


        # Step 5: Run Cycle 2 explicitly
        print("[EVALUATOR SIMULATION] Step 5: Executing Cycle 2...", flush=True)
        await run_agent_cycle(
            agent_id=agent_id,
            persona_name="Ada",
            persona_domain="AI Security",
        )

        # Step 6: GET feed again
        print("[EVALUATOR SIMULATION] Step 6: Calling GET /api/agent/feed again...", flush=True)
        feed_res2 = await client.get(f"/api/agent/feed?agentId={agent_id}")
        assert feed_res2.status_code == 200
        feed2 = feed_res2.json()
        posts2 = feed2["posts"]
        print(f"[EVALUATOR SIMULATION] Feed returned {len(posts2)} post(s) after Cycle 2.", flush=True)

        # Ensure previous posts remain in feed
        if len(posts1) > 0:
            post1_ids = {p["id"] for p in posts1}
            post2_ids = {p["id"] for p in posts2}
            assert post1_ids.issubset(post2_ids), "Previous posts disappeared from feed!"

        # Ensure unique IDs across all posts
        all_ids = [p["id"] for p in posts2]
        assert len(all_ids) == len(set(all_ids)), "Duplicate post IDs found in feed!"

        # Clean up background agent task
        stop_agent(agent_id)

    print("\n[EVALUATOR SIMULATION] SUCCESS: All evaluator checks passed!\n", flush=True)

