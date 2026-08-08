import feedparser

from app.models.topic import TopicCandidate


RSS_FEEDS = {
    "arXiv AI": "https://export.arxiv.org/rss/cs.AI",
    "arXiv ML": "https://export.arxiv.org/rss/cs.LG",
}


def discover_topics(limit_per_source: int = 10) -> list[TopicCandidate]:
    candidates: list[TopicCandidate] = []

    for source_name, feed_url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(feed_url)

            for entry in feed.entries[:limit_per_source]:
                published_at = None

                if getattr(entry, "published_parsed", None):
                    published_at = datetime_from_struct_time(
                        entry.published_parsed
                    )

                candidates.append(
                    TopicCandidate(
                        title=getattr(entry, "title", "").strip(),
                        summary=getattr(entry, "summary", "").strip(),
                        source_url=getattr(entry, "link", "").strip(),
                        source_name=source_name,
                        published_at=published_at,
                    )
                )

        except Exception as exc:
            print(
                f"Topic discovery failed for {source_name}: {exc}",
                flush=True,
            )

    return candidates


def datetime_from_struct_time(value):
    from datetime import datetime, timezone

    return datetime(*value[:6], tzinfo=timezone.utc)