from datetime import datetime, timezone, timedelta
from app.models.topic import TopicCandidate
from app.services.editorial_engine import EditorialEngine, EditorialDecision


def test_editorial_evaluate_accept():
    engine = EditorialEngine()
    candidate = TopicCandidate(
        title="New Agentic AI Architecture Released for Cybersecurity",
        summary="A breakthrough in autonomous LLM agent security.",
        source_url="https://example.com/ai-agent-sec",
        source_name="Hacker News",
        published_at=datetime.now(timezone.utc) - timedelta(hours=2),
    )

    decision = engine.evaluate(candidate, persona_domain="AI Security")
    assert decision.decision == "ACCEPT"
    assert decision.score >= 60
    assert "AI relevance" in decision.reason
    assert "Hacker News" in decision.topic.source_name


def test_editorial_evaluate_reject_irrelevant():
    engine = EditorialEngine()
    candidate = TopicCandidate(
        title="Baking Sourdough Bread: A Beginner's Guide",
        summary="Learn how to make delicious sourdough bread at home.",
        source_url="https://example.com/sourdough",
        source_name="FoodBlog",
        published_at=datetime.now(timezone.utc) - timedelta(hours=10),
    )

    decision = engine.evaluate(candidate, persona_domain="AI Security")
    assert decision.decision == "REJECT"
    assert decision.score < 60
    assert "Rejected" in decision.reason
