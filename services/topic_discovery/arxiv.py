"""arXiv topic discovery service.

Fetches recent research papers from arXiv RSS feeds, filters them
for AI and technology relevance, and converts them into the common
topic-candidate format.

This module is independent of:
- FastAPI
- SQLAlchemy
- SQLite
- APScheduler
- Backend API routes
"""

from __future__ import annotations

import html
import logging
import re
from datetime import datetime, timezone
from typing import Any

import feedparser
import httpx


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ARXIV_RSS_CATEGORIES: tuple[str, ...] = (
    "cs.AI",  # Artificial Intelligence
    "cs.LG",  # Machine Learning
    "cs.CL",  # Computation and Language
    "cs.CV",  # Computer Vision
    "cs.RO",  # Robotics
)

ARXIV_RSS_BASE_URL = "https://export.arxiv.org/rss"

REQUEST_TIMEOUT = 20.0

DEFAULT_LIMIT = 20


# ---------------------------------------------------------------------------
# Technology keywords
# ---------------------------------------------------------------------------

TECH_KEYWORDS: tuple[str, ...] = (
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "large language model",
    "llm",
    "generative ai",
    "foundation model",
    "language model",
    "multimodal",
    "computer vision",
    "natural language processing",
    "nlp",
    "neural network",
    "reinforcement learning",
    "robotics",
    "autonomous agent",
    "ai agent",
    "agentic",
    "transformer",
    "diffusion model",
    "generative model",
    "speech recognition",
    "knowledge graph",
    "reasoning",
    "computer science",
    "cybersecurity",
    "quantum computing",
)


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def _clean_text(value: str) -> str:
    """Clean whitespace and HTML entities from text.

    Args:
        value: Raw text.

    Returns:
        Cleaned text.
    """
    value = html.unescape(value)

    return " ".join(value.split()).strip()


def _keyword_matches(text: str, keyword: str) -> bool:
    """Check whether a keyword appears as a complete term.

    Args:
        text: Text to search.
        keyword: Keyword to find.

    Returns:
        True if the keyword appears in the text.
    """
    pattern = rf"(?<!\w){re.escape(keyword)}(?!\w)"

    return re.search(
        pattern,
        text,
        flags=re.IGNORECASE,
    ) is not None


def _extract_tags(text: str) -> list[str]:
    """Extract technology tags from paper metadata.

    Args:
        text: Combined paper title and summary.

    Returns:
        Matching technology keywords.
    """
    return [
        keyword
        for keyword in TECH_KEYWORDS
        if _keyword_matches(text, keyword)
    ]


def _is_relevant_paper(
    title: str,
    summary: str,
) -> bool:
    """Determine whether a paper is technology-related.

    Args:
        title: Paper title.
        summary: Paper abstract.

    Returns:
        True when at least one technology keyword matches.
    """
    searchable_text = f"{title} {summary}"

    return any(
        _keyword_matches(searchable_text, keyword)
        for keyword in TECH_KEYWORDS
    )


# ---------------------------------------------------------------------------
# Date handling
# ---------------------------------------------------------------------------

def _parse_published_at(entry: Any) -> str:
    """Convert an RSS publication date to ISO-8601.

    Args:
        entry: feedparser entry.

    Returns:
        ISO-8601 UTC timestamp.
    """
    published_struct = entry.get("published_parsed")

    if published_struct:
        try:
            published_datetime = datetime(
                *published_struct[:6],
                tzinfo=timezone.utc,
            )

            return published_datetime.isoformat()

        except (TypeError, ValueError, OverflowError):
            logger.warning(
                "Unable to parse arXiv publication timestamp."
            )

    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Entry normalization
# ---------------------------------------------------------------------------

def _normalize_entry(
    entry: Any,
) -> dict[str, Any]:
    """Convert an arXiv RSS entry to a topic candidate.

    Args:
        entry: Parsed feedparser entry.

    Returns:
        Normalized topic candidate.
    """
    title = _clean_text(
        str(entry.get("title", ""))
    )

    summary = _clean_text(
        str(entry.get("summary", ""))
    )

    url = _clean_text(
        str(entry.get("link", ""))
    )

    searchable_text = f"{title} {summary}"

    return {
        "title": title,
        "summary": summary,
        "url": url,
        "source": "arXiv",
        "published_at": _parse_published_at(entry),
        "tags": _extract_tags(searchable_text),
    }


# ---------------------------------------------------------------------------
# RSS fetching
# ---------------------------------------------------------------------------

async def _fetch_arxiv_feed(
    client: httpx.AsyncClient,
    category: str,
) -> str:
    """Fetch one arXiv RSS category.

    Args:
        client: HTTPX asynchronous client.
        category: arXiv category such as ``cs.CL``.

    Returns:
        Raw RSS content.

    Raises:
        httpx.HTTPError:
            If the request fails.
    """
    url = f"{ARXIV_RSS_BASE_URL}/{category}"

    response = await client.get(
        url,
        headers={
            "User-Agent": "SignalForge-AI-Topic-Discovery/1.0",
            "Accept": (
                "application/rss+xml, "
                "application/xml, text/xml"
            ),
        },
    )

    response.raise_for_status()

    return response.text


# ---------------------------------------------------------------------------
# RSS parsing
# ---------------------------------------------------------------------------

def _parse_feed(
    feed_content: str,
) -> list[Any]:
    """Parse RSS content using feedparser.

    Args:
        feed_content: Raw RSS/XML content.

    Returns:
        Parsed feed entries.
    """
    parsed_feed = feedparser.parse(feed_content)

    if getattr(parsed_feed, "bozo", False):
        logger.warning(
            "arXiv RSS parser reported a feed issue: %s",
            getattr(
                parsed_feed,
                "bozo_exception",
                "unknown parsing issue",
            ),
        )

    return list(
        getattr(
            parsed_feed,
            "entries",
            [],
        )
    )


# ---------------------------------------------------------------------------
# Public service
# ---------------------------------------------------------------------------

async def fetch_arxiv_topics(
    limit: int = DEFAULT_LIMIT,
) -> list[dict[str, Any]]:
    """Fetch recent AI and technology papers from arXiv.

    Args:
        limit:
            Maximum number of candidates to return.

    Returns:
        List of normalized arXiv topic candidates.

    Notes:
        Multiple arXiv RSS categories are checked. A failure in one
        category does not stop discovery from the remaining categories.
    """
    if limit <= 0:
        logger.warning(
            "arXiv limit must be greater than zero."
        )
        return []

    logger.info(
        "Starting arXiv topic discovery. Limit=%d",
        limit,
    )

    topics: list[dict[str, Any]] = []

    seen_urls: set[str] = set()

    try:
        async with httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True,
        ) as client:

            for category in ARXIV_RSS_CATEGORIES:
                if len(topics) >= limit:
                    break

                logger.info(
                    "Fetching arXiv category: %s",
                    category,
                )

                try:
                    feed_content = await _fetch_arxiv_feed(
                        client,
                        category,
                    )

                    entries = _parse_feed(
                        feed_content
                    )

                    logger.info(
                        "Category %s returned %d entries.",
                        category,
                        len(entries),
                    )

                    for entry in entries:
                        if len(topics) >= limit:
                            break

                        try:
                            title = _clean_text(
                                str(
                                    entry.get(
                                        "title",
                                        "",
                                    )
                                )
                            )

                            summary = _clean_text(
                                str(
                                    entry.get(
                                        "summary",
                                        "",
                                    )
                                )
                            )

                            url = _clean_text(
                                str(
                                    entry.get(
                                        "link",
                                        "",
                                    )
                                )
                            )

                            if not title or not url:
                                continue

                            if url in seen_urls:
                                continue

                            if not _is_relevant_paper(
                                title,
                                summary,
                            ):
                                continue

                            topic = _normalize_entry(
                                entry
                            )

                            topics.append(topic)
                            seen_urls.add(url)

                        except Exception:
                            logger.exception(
                                "Failed to normalize an arXiv "
                                "entry from category %s.",
                                category,
                            )

                except httpx.HTTPError as exc:
                    logger.error(
                        "Failed to fetch arXiv category %s: %s",
                        category,
                        exc,
                    )

                except Exception:
                    logger.exception(
                        "Unexpected error processing "
                        "arXiv category %s.",
                        category,
                    )

    except Exception:
        logger.exception(
            "Unexpected error during arXiv discovery."
        )
        return []

    logger.info(
        "arXiv topic discovery completed. Found %d topics.",
        len(topics),
    )

    return topics


# ---------------------------------------------------------------------------
# Local test entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        """Run a local arXiv discovery test."""
        topics = await fetch_arxiv_topics()

        print(
            f"\nFound {len(topics)} arXiv topics.\n"
        )

        for topic in topics:
            print(topic)
            print("-" * 80)

    asyncio.run(main())