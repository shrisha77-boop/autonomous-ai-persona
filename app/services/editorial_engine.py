from dataclasses import dataclass
from datetime import datetime, timezone

from app.models.topic import TopicCandidate


@dataclass
class EditorialDecision:
    topic: TopicCandidate
    decision: str
    score: int
    reason: str


class EditorialEngine:
    """
    Deterministic editorial filter.

    The engine evaluates whether a discovered topic is worth
    considering for publication based on persona alignment,
    AI relevance, recency, and topic significance.
    """

    AI_KEYWORDS = {
        "ai",
        "artificial intelligence",
        "machine learning",
        "deep learning",
        "llm",
        "large language model",
        "generative ai",
        "openai",
        "anthropic",
        "claude",
        "gemini",
        "deepseek",
        "neural network",
        "robotics",
        "agentic",
        "autonomous agent",
        "open model",
    }

    def evaluate(
        self,
        topic: TopicCandidate,
        persona_domain: str,
    ) -> EditorialDecision:

        text = f"{topic.title} {topic.summary}".lower()
        domain = persona_domain.lower()

        score = 0
        reasons = []

        # AI / technology relevance
        ai_matches = [
            keyword
            for keyword in self.AI_KEYWORDS
            if keyword in text
        ]

        if ai_matches:
            score += 30
            reasons.append(
                f"AI relevance detected ({', '.join(ai_matches[:3])})"
            )
        else:
            reasons.append("Weak direct AI relevance")

        # Persona alignment
        domain_terms = domain.replace("-", " ").split()

        domain_matches = [
            term
            for term in domain_terms
            if len(term) > 2 and term in text
        ]

        if domain_matches:
            score += 25
            reasons.append("Strong persona-domain alignment")
        else:
            score += 5
            reasons.append("Limited persona-domain alignment")

        # Recency
        if topic.published_at:
            now = datetime.now(timezone.utc)

            published_at = topic.published_at

            if published_at.tzinfo is None:
                published_at = published_at.replace(
                    tzinfo=timezone.utc
                )

            age_hours = (
                now - published_at
            ).total_seconds() / 3600

            if age_hours <= 24:
                score += 25
                reasons.append("Published within the last 24 hours")
            elif age_hours <= 72:
                score += 15
                reasons.append("Published within the last 3 days")
            else:
                score += 5
                reasons.append("Older than 3 days")
        else:
            score += 5
            reasons.append("Publication time unavailable")

        # Source credibility
        if topic.source_name in {
            "Hacker News",
            "arXiv AI",
            "arXiv ML",
        }:
            score += 10
            reasons.append("Recognized technology source")

        # Final editorial decision
        threshold = 60

        if score >= threshold:
            decision = "ACCEPT"
            reason = (
                f"Selected because the topic meets the publishing "
                f"threshold ({score}/100). "
                + "; ".join(reasons)
            )
        else:
            decision = "REJECT"
            reason = (
                f"Rejected because the topic does not meet the "
                f"publishing threshold ({score}/100). "
                + "; ".join(reasons)
            )

        return EditorialDecision(
            topic=topic,
            decision=decision,
            score=score,
            reason=reason,
        )