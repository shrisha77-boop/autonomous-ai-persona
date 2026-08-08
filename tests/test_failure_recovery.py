import pytest
from unittest.mock import patch
from app.database.database import AsyncSessionLocal, Base, engine
from app.models.topic import TopicCandidate
from app.services.scheduler import run_agent_cycle, stop_agent
from app.services.editorial_engine import EditorialDecision


@pytest.mark.asyncio
async def test_failure_recovery_ollama_down():
    """Verify that when Ollama raises an exception, run_agent_cycle recovers gracefully with fallback."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    mock_topic = TopicCandidate(
        title="Breakthrough in LLM Security Guardrails",
        summary="A new open source benchmark for LLM safety and vulnerability detection.",
        source_url="https://arxiv.org/abs/2401.00001",
        source_name="arXiv AI",
    )
    mock_decision = EditorialDecision(
        topic=mock_topic,
        decision="ACCEPT",
        score=85,
        reason="Strong AI relevance",
    )

    with patch("app.services.agent_engine.AgentEngine.discover_and_select", return_value=[mock_decision]):
        with patch("app.services.llm.ollama_provider.OllamaProvider.generate", side_effect=Exception("Connection refused")):
            # Should not raise exception, but use MockLLMProvider fallback and publish post
            await run_agent_cycle(
                agent_id="failure-test-agent",
                persona_name="Ada",
                persona_domain="AI Security",
            )


@pytest.mark.asyncio
async def test_failure_recovery_empty_discovery():
    """Verify cycle runs safely without error when no topics are discovered."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    with patch("app.services.agent_engine.AgentEngine.discover_and_select", return_value=[]):
        # Should complete silently without publishing post or crashing
        await run_agent_cycle(
            agent_id="empty-disc-agent",
            persona_name="Ada",
            persona_domain="AI Security",
        )
