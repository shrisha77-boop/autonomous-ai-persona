"""Hacker News topic discovery service.

This module fetches recent stories from the Hacker News API,
filters them for AI and technology relevance, and converts them
into a common topic-candidate format.

This module is independent of:
- FastAPI
- SQLAlchemy
- SQLite
- APScheduler
- Backend API routes

It can therefore be reused by the Topic Discovery aggregator.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any

import httpx


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

HN_API_BASE_URL = "https://hacker-news.firebaseio.com/v0"

DEFAULT_LIMIT = 30
REQUEST_TIMEOUT = 10.0


# Keywords used to identify AI and technology-related stories.
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

    Short keywords such as ``ai`` must not match inside unrelated
    words such as ``paid`` or ``laid``.

    Args:
        text: Text to search.
        keyword: Technology keyword to find.

    Returns:
        True if the keyword appears as a standalone term.
    """
    pattern = rf"(?<!\w){re.escape(keyword)}(?!\w)"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def _is_technology_story(story: dict[str, Any]) -> bool:
    """Check whether a Hacker News story is technology-related.

    Args:
        story: Raw story returned by the Hacker News API.

    Returns:
        True if the story appears technology-related, otherwise False.
    """
    searchable_text = " ".join(
        [
            str(story.get("title", "")),
            str(story.get("text", "")),
        ]
    )

    return any(
        _keyword_matches(searchable_text, keyword)
        for keyword in TECH_KEYWORDS
    )


def _extract_tags(story: dict[str, Any]) -> list[str]:
    """Extract technology-related tags from a Hacker News story.

    Args:
        story: Raw Hacker News story.

    Returns:
        List of matching technology keywords.
    """
    searchable_text = " ".join(
        [
            str(story.get("title", "")),
            str(story.get("text", "")),
        ]
    )

    return [
        keyword
        for keyword in TECH_KEYWORDS
        if _keyword_matches(searchable_text, keyword)
    ]

def _normalize_timestamp(timestamp: Any) -> str:
    """Convert a Hacker News Unix timestamp into ISO 8601 format.

    Args:
        timestamp: Unix timestamp supplied by Hacker News.

    Returns:
        UTC ISO 8601 timestamp, or an empty string if invalid.
    """
    if not timestamp:
        return ""

    try:
        return datetime.fromtimestamp(
            float(timestamp),
            tz=timezone.utc,
        ).isoformat()

    except (TypeError, ValueError, OverflowError):
        logger.warning(
            "Invalid Hacker News timestamp: %r",
            timestamp,
        )
        return ""


def _normalize_story(story: dict[str, Any]) -> dict[str, Any]:
    """Convert a Hacker News story to the common topic format.

    Args:
        story: Raw Hacker News story.

    Returns:
        Topic candidate dictionary.
    """
    story_id = story.get("id")
    url = story.get("url")

    # Some Hacker News stories do not contain an external URL.
    # In that situation, link to the Hacker News discussion itself.
    if not url and story_id:
        url = f"https://news.ycombinator.com/item?id={story_id}"

    return {
        "title": str(story.get("title", "")).strip(),
        "summary": str(story.get("text", "")).strip(),
        "url": str(url or "").strip(),
        "source": "Hacker News",
        "published_at": _normalize_timestamp(
            story.get("time")
        ),
        "tags": _extract_tags(story),
    }


async def _fetch_json(
    client: httpx.AsyncClient,
    url: str,
) -> Any:
    """Fetch JSON data from a URL.

    Args:
        client: HTTPX asynchronous client.
        url: API endpoint URL.

    Returns:
        Parsed JSON response.

    Raises:
        httpx.HTTPError: If the HTTP request fails.
    """
    response = await client.get(url)

    response.raise_for_status()

    return response.json()


# ---------------------------------------------------------------------------
# Public service function
# ---------------------------------------------------------------------------

async def fetch_hackernews_topics(
    limit: int = DEFAULT_LIMIT,
) -> list[dict[str, Any]]:
    """Fetch AI and technology topics from Hacker News.

    The Hacker News API first provides IDs for recent stories.
    Each story is then retrieved individually and filtered for
    technology relevance.

    Args:
        limit:
            Maximum number of recent Hacker News stories to inspect.

    Returns:
        A list of topic candidates using the common format:

        [
            {
                "title": "...",
                "summary": "...",
                "url": "...",
                "source": "Hacker News",
                "published_at": "...",
                "tags": [...]
            }
        ]

    Notes:
        Network failures and malformed individual stories are
        handled gracefully. A failure in one story does not stop
        processing of the remaining stories.
    """
    if limit <= 0:
        logger.warning(
            "Hacker News limit must be greater than zero."
        )
        return []

    logger.info(
        "Starting Hacker News topic discovery. Limit=%d",
        limit,
    )

    try:
        async with httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT
        ) as client:

            # Get IDs of recent stories.
            story_ids = await _fetch_json(
                client,
                f"{HN_API_BASE_URL}/newstories.json",
            )

            if not isinstance(story_ids, list):
                logger.warning(
                    "Unexpected response from Hacker News newstories API."
                )
                return []

            selected_ids = story_ids[:limit]

            topics: list[dict[str, Any]] = []

            for story_id in selected_ids:
                try:
                    story = await _fetch_json(
                        client,
                        f"{HN_API_BASE_URL}/item/{story_id}.json",
                    )

                    if not isinstance(story, dict):
                        continue

                    # Only process normal Hacker News stories.
                    if story.get("type") != "story":
                        continue

                    # Ignore deleted or dead stories.
                    if story.get("dead") or story.get("deleted"):
                        continue

                    # Ignore stories unrelated to technology.
                    if not _is_technology_story(story):
                        continue

                    topic = _normalize_story(story)

                    # Don't add malformed topics.
                    if not topic["title"] or not topic["url"]:
                        continue

                    topics.append(topic)

                except httpx.HTTPError as exc:
                    logger.warning(
                        "Failed to fetch Hacker News story %s: %s",
                        story_id,
                        exc,
                    )

                except Exception:
                    logger.exception(
                        "Unexpected error processing Hacker News story %s",
                        story_id,
                    )

            logger.info(
                "Hacker News discovery completed. "
                "Found %d technology topics.",
                len(topics),
            )

            return topics

    except httpx.HTTPError as exc:
        logger.error(
            "Hacker News API request failed: %s",
            exc,
        )
        return []

    except Exception:
        logger.exception(
            "Unexpected error during Hacker News discovery."
        )
        return []


# ---------------------------------------------------------------------------
# Local test entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        """Run a local test of the Hacker News discovery service."""
        topics = await fetch_hackernews_topics()

        print(f"\nFound {len(topics)} Hacker News topics.\n")

        for topic in topics:
            print(topic)
            print("-" * 80)

    asyncio.run(main())