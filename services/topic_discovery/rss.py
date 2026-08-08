"""RSS-based topic discovery service.

This module fetches AI and technology news from RSS feeds and converts
the entries into the common topic-candidate format used by SignalForge AI.

Supported sources:
    - OpenAI Blog
    - Anthropic News
    - Google AI Blog
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any

import feedparser
import httpx


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# RSS feed configuration
# ---------------------------------------------------------------------------

RSS_FEEDS: dict[str, str] = {
    "OpenAI": "https://openai.com/news/rss.xml",
    "Google AI": "https://blog.google/technology/ai/rss/",
}


# ---------------------------------------------------------------------------
# Technology keywords
# ---------------------------------------------------------------------------

TECH_KEYWORDS: tuple[str, ...] = (
    "ai",
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "llm",
    "large language model",
    "generative ai",
    "chatgpt",
    "openai",
    "anthropic",
    "gemini",
    "claude",
    "neural network",
    "robotics",
    "computer vision",
    "natural language processing",
    "nlp",
    "python",
    "programming",
    "software",
    "developer",
    "github",
    "open source",
    "cybersecurity",
    "quantum computing",
    "cloud computing",
    "database",
    "technology",
)


# ---------------------------------------------------------------------------
# Internal helper functions
# ---------------------------------------------------------------------------


def _keyword_matches(text: str, keyword: str) -> bool:
    """Check whether a keyword appears as a complete term in text.

    Short keywords such as ``ai`` must not match inside unrelated words.

    Args:
        text: Text to search.
        keyword: Technology keyword to find.

    Returns:
        True if the keyword appears as a standalone term.
    """
    pattern = rf"(?<!\w){re.escape(keyword)}(?!\w)"

    return re.search(
        pattern,
        text,
        flags=re.IGNORECASE,
    ) is not None


def _extract_tags(title: str, summary: str) -> list[str]:
    """Extract technology-related tags from an RSS entry.

    Args:
        title: RSS entry title.
        summary: RSS entry summary or description.

    Returns:
        List of matching technology keywords.
    """
    searchable_text = f"{title} {summary}"

    return [
        keyword
        for keyword in TECH_KEYWORDS
        if _keyword_matches(searchable_text, keyword)
    ]


def _clean_text(value: Any) -> str:
    """Convert a feed value into clean text.

    Args:
        value: Raw value returned by feedparser.

    Returns:
        Clean string.
    """
    if value is None:
        return ""

    return str(value).strip()


def _parse_published_at(entry: Any) -> str:
    """Extract and normalize an RSS publication timestamp.

    Args:
        entry: feedparser entry.

    Returns:
        ISO-8601 timestamp when available, otherwise the current UTC time.
    """
    parsed_time = entry.get("published_parsed")

    if parsed_time is None:
        parsed_time = entry.get("updated_parsed")

    if parsed_time is not None:
        try:
            published_datetime = datetime(
                parsed_time.tm_year,
                parsed_time.tm_mon,
                parsed_time.tm_mday,
                parsed_time.tm_hour,
                parsed_time.tm_min,
                parsed_time.tm_sec,
                tzinfo=timezone.utc,
            )

            return published_datetime.isoformat()
        except (AttributeError, TypeError, ValueError):
            logger.warning("Unable to parse RSS publication timestamp.")

    return datetime.now(timezone.utc).isoformat()


def _is_technology_entry(title: str, summary: str) -> bool:
    """Determine whether an RSS entry is technology-related.

    Args:
        title: RSS entry title.
        summary: RSS entry summary.

    Returns:
        True if at least one technology keyword is present.
    """
    searchable_text = f"{title} {summary}"

    return any(
        _keyword_matches(searchable_text, keyword)
        for keyword in TECH_KEYWORDS
    )


def _normalize_entry(entry: Any, source: str) -> dict[str, Any] | None:
    """Convert one RSS entry into the common topic format.

    Args:
        entry: feedparser RSS entry.
        source: Name of the RSS source.

    Returns:
        Normalized topic candidate or None when required data is missing.
    """
    title = _clean_text(entry.get("title"))
    summary = _clean_text(
        entry.get("summary") or entry.get("description")
    )
    url = _clean_text(entry.get("link"))

    if not title or not url:
        logger.debug(
            "Skipping RSS entry from %s because title or URL is missing.",
            source,
        )
        return None

    if not _is_technology_entry(title, summary):
        return None

    tags = _extract_tags(title, summary)

    return {
        "title": title,
        "summary": summary,
        "url": url,
        "source": source,
        "published_at": _parse_published_at(entry),
        "tags": tags,
    }


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


def fetch_rss_topics(
    source: str,
    feed_url: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Fetch and normalize topics from a single RSS feed.

    Args:
        source: Human-readable source name.
        feed_url: RSS feed URL.
        limit: Maximum number of entries to inspect.

    Returns:
        List of normalized technology topic candidates.
    """
    logger.info("Fetching RSS feed: %s", source)

    try:
        headers = {
            "User-Agent": "SignalForge-AI/1.0",
        }

        response = httpx.get(
            feed_url,
            headers=headers,
            timeout=20.0,
            follow_redirects=True,
        )

        response.raise_for_status()

        feed = feedparser.parse(response.content)

        if feed.bozo:
            logger.warning(
                "RSS feed %s returned a parsing warning: %s",
                source,
                feed.bozo_exception,
            )

        topics: list[dict[str, Any]] = []

        for entry in feed.entries[:limit]:
            topic = _normalize_entry(entry, source)

            if topic is not None:
                topics.append(topic)

        logger.info(
            "Found %d technology topics from %s.",
            len(topics),
            source,
        )

        return topics

    except httpx.HTTPError as exc:
        logger.error(
            "HTTP error while fetching %s: %s",
            source,
            exc,
        )
        return []

    except Exception:
        logger.exception(
            "Unexpected error while processing RSS source: %s",
            source,
        )
        return []


def fetch_all_rss_topics(
    limit_per_source: int = 10,
) -> list[dict[str, Any]]:
    """Fetch technology topics from all configured RSS sources.

    A failure in one source does not prevent the remaining sources
    from being processed.

    Args:
        limit_per_source: Maximum number of entries inspected per source.

    Returns:
        Combined list of normalized topic candidates.
    """
    all_topics: list[dict[str, Any]] = []

    for source, feed_url in RSS_FEEDS.items():
        topics = fetch_rss_topics(
            source=source,
            feed_url=feed_url,
            limit=limit_per_source,
        )

        all_topics.extend(topics)

    logger.info(
        "Found %d total RSS technology topics.",
        len(all_topics),
    )

    return all_topics


# ---------------------------------------------------------------------------
# Local test entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    topics = fetch_all_rss_topics(limit_per_source=10)

    print(f"\nFound {len(topics)} RSS topics.\n")

    for topic in topics:
        print(topic)
        print("-" * 80)