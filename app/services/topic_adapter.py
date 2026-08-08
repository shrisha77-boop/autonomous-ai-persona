from datetime import datetime

from app.models.topic import TopicCandidate


def adapt_topic(item: dict) -> TopicCandidate:
    published_at = item.get("published_at")

    if isinstance(published_at, str):
        published_at = datetime.fromisoformat(
            published_at.replace("Z", "+00:00")
        )

    return TopicCandidate(
        title=item.get("title", ""),
        summary=item.get("summary", ""),
        source_url=item.get("url", ""),
        source_name=item.get("source", ""),
        published_at=published_at,
    )