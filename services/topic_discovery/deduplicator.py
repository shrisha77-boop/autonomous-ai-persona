"""
Topic Deduplication Service
---------------------------

Removes duplicate and highly similar technology topics collected
from multiple discovery sources.

Expected topic format:

{
    "title": str,
    "summary": str,
    "url": str,
    "source": str,
    "published_at": str,
    "tags": list[str]
}

The module is intentionally deterministic and does not require
an external AI/LLM service.
"""

from __future__ import annotations

import logging
import re
from difflib import SequenceMatcher
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_SIMILARITY_THRESHOLD = 0.85


# ---------------------------------------------------------------------------
# Text normalization
# ---------------------------------------------------------------------------

def _clean_text(value: Any) -> str:
    """Convert a value to clean normalized text."""

    if value is None:
        return ""

    text = str(value)

    # Normalize whitespace.
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def _normalize_title(title: str) -> str:
    """Normalize a title for duplicate comparison."""

    title = _clean_text(title).lower()

    # Remove punctuation while preserving letters/numbers.
    title = re.sub(r"[^\w\s]", " ", title)

    # Normalize whitespace again.
    title = re.sub(r"\s+", " ", title)

    return title.strip()


def _title_tokens(title: str) -> set[str]:
    """Return meaningful tokens from a normalized title."""

    normalized = _normalize_title(title)

    if not normalized:
        return set()

    return set(normalized.split())


# ---------------------------------------------------------------------------
# URL normalization
# ---------------------------------------------------------------------------

def _normalize_url(url: str) -> str:
    """Normalize a URL so equivalent URLs can be compared."""

    url = _clean_text(url)

    if not url:
        return ""

    try:
        parts = urlsplit(url)

        scheme = parts.scheme.lower()
        netloc = parts.netloc.lower()

        # Remove default ports.
        netloc = netloc.replace(":80", "") if scheme == "http" else netloc
        netloc = netloc.replace(":443", "") if scheme == "https" else netloc

        path = parts.path.rstrip("/")

        # Remove common tracking parameters.
        tracking_parameters = {
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_term",
            "utm_content",
            "fbclid",
            "gclid",
        }

        query_parameters = [
            (key, value)
            for key, value in parse_qsl(
                parts.query,
                keep_blank_values=True,
            )
            if key.lower() not in tracking_parameters
        ]

        query = urlencode(query_parameters)

        return urlunsplit(
            (
                scheme,
                netloc,
                path,
                query,
                "",
            )
        )

    except Exception:
        # If URL parsing fails, use a conservative fallback.
        return url.rstrip("/")


# ---------------------------------------------------------------------------
# Similarity calculation
# ---------------------------------------------------------------------------

def _title_similarity(title_a: str, title_b: str) -> float:
    """Calculate similarity between two topic titles."""

    normalized_a = _normalize_title(title_a)
    normalized_b = _normalize_title(title_b)

    if not normalized_a or not normalized_b:
        return 0.0

    # Exact normalized match.
    if normalized_a == normalized_b:
        return 1.0

    sequence_similarity = SequenceMatcher(
        None,
        normalized_a,
        normalized_b,
    ).ratio()

    tokens_a = _title_tokens(normalized_a)
    tokens_b = _title_tokens(normalized_b)

    if not tokens_a or not tokens_b:
        return sequence_similarity

    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b

    token_similarity = len(intersection) / len(union)

    # Combine character and token similarity.
    return max(
        sequence_similarity,
        token_similarity,
    )


# ---------------------------------------------------------------------------
# Topic quality
# ---------------------------------------------------------------------------

def _topic_quality(topic: dict[str, Any]) -> int:
    """
    Calculate a simple quality score.

    Higher-quality topics are preferred when duplicates are found.
    """

    score = 0

    title = _clean_text(topic.get("title"))
    summary = _clean_text(topic.get("summary"))
    url = _clean_text(topic.get("url"))
    source = _clean_text(topic.get("source"))
    published_at = _clean_text(topic.get("published_at"))

    if title:
        score += 3

    if summary:
        score += 2

    if url:
        score += 2

    if source:
        score += 1

    if published_at:
        score += 1

    tags = topic.get("tags")

    if isinstance(tags, list):
        score += min(len(tags), 3)

    return score


def _merge_topics(
    existing: dict[str, Any],
    duplicate: dict[str, Any],
) -> dict[str, Any]:
    """
    Merge useful information from two duplicate topics.

    The higher-quality topic provides the base record.
    """

    existing_quality = _topic_quality(existing)
    duplicate_quality = _topic_quality(duplicate)

    if duplicate_quality > existing_quality:
        merged = duplicate.copy()
        other = existing
    else:
        merged = existing.copy()
        other = duplicate

    # Preserve a summary if the selected topic does not have one.
    if not _clean_text(merged.get("summary")):
        merged["summary"] = other.get("summary", "")

    # Preserve URL if missing.
    if not _clean_text(merged.get("url")):
        merged["url"] = other.get("url", "")

    # Preserve publication timestamp if missing.
    if not _clean_text(merged.get("published_at")):
        merged["published_at"] = other.get(
            "published_at",
            "",
        )

    # Merge tags.
    tags: list[str] = []

    for topic in (existing, duplicate):
        topic_tags = topic.get("tags", [])

        if isinstance(topic_tags, list):
            for tag in topic_tags:
                tag = _clean_text(tag)

                if tag and tag.lower() not in {
                    existing_tag.lower()
                    for existing_tag in tags
                }:
                    tags.append(tag)

    merged["tags"] = tags

    return merged


# ---------------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------------

def _is_duplicate(
    topic_a: dict[str, Any],
    topic_b: dict[str, Any],
    similarity_threshold: float,
) -> bool:
    """Determine whether two topics represent the same story."""

    title_a = _clean_text(topic_a.get("title"))
    title_b = _clean_text(topic_b.get("title"))

    url_a = _normalize_url(
        _clean_text(topic_a.get("url"))
    )

    url_b = _normalize_url(
        _clean_text(topic_b.get("url"))
    )

    # Same URL is a strong duplicate signal.
    if url_a and url_b and url_a == url_b:
        return True

    # Same normalized title is also an exact duplicate.
    normalized_a = _normalize_title(title_a)
    normalized_b = _normalize_title(title_b)

    if normalized_a and normalized_a == normalized_b:
        return True

    # Finally compare title similarity.
    similarity = _title_similarity(
        title_a,
        title_b,
    )

    return similarity >= similarity_threshold


# ---------------------------------------------------------------------------
# Public service function
# ---------------------------------------------------------------------------

def deduplicate_topics(
    topics: list[dict[str, Any]],
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> list[dict[str, Any]]:
    """
    Remove duplicate and highly similar topics.

    Args:
        topics:
            Combined topics produced by the aggregator.

        similarity_threshold:
            Title similarity threshold between 0 and 1.
            Higher values are stricter.

    Returns:
        A list containing unique topic candidates.
    """

    if not topics:
        logger.info(
            "No topics received for deduplication."
        )
        return []

    if not 0.0 <= similarity_threshold <= 1.0:
        raise ValueError(
            "similarity_threshold must be between 0 and 1."
        )

    logger.info(
        "Starting topic deduplication. Input topics=%d",
        len(topics),
    )

    unique_topics: list[dict[str, Any]] = []

    # Exact normalized URL lookup.
    url_index: dict[str, int] = {}

    # Exact normalized title lookup.
    title_index: dict[str, int] = {}

    duplicate_count = 0

    for topic in topics:

        if not isinstance(topic, dict):
            logger.warning(
                "Skipping invalid topic: %r",
                topic,
            )
            continue

        title = _clean_text(topic.get("title"))
        url = _normalize_url(
            _clean_text(topic.get("url"))
        )

        # A topic without a title cannot be useful.
        if not title:
            logger.warning(
                "Skipping topic without a title."
            )
            continue

        # ---------------------------------------------------------------
        # First: exact URL duplicate.
        # ---------------------------------------------------------------

        if url and url in url_index:
            existing_index = url_index[url]

            unique_topics[existing_index] = _merge_topics(
                unique_topics[existing_index],
                topic,
            )

            duplicate_count += 1
            continue

        # ---------------------------------------------------------------
        # Second: exact normalized title duplicate.
        # ---------------------------------------------------------------

        normalized_title = _normalize_title(title)

        if (
            normalized_title
            and normalized_title in title_index
        ):
            existing_index = title_index[
                normalized_title
            ]

            unique_topics[existing_index] = _merge_topics(
                unique_topics[existing_index],
                topic,
            )

            if url:
                url_index[url] = existing_index

            duplicate_count += 1
            continue

        # ---------------------------------------------------------------
        # Third: fuzzy title duplicate.
        # ---------------------------------------------------------------

        duplicate_index: int | None = None

        for index, existing_topic in enumerate(
            unique_topics
        ):
            if _is_duplicate(
                existing_topic,
                topic,
                similarity_threshold,
            ):
                duplicate_index = index
                break

        if duplicate_index is not None:
            unique_topics[duplicate_index] = _merge_topics(
                unique_topics[duplicate_index],
                topic,
            )

            if url:
                url_index[url] = duplicate_index

            title_index[normalized_title] = duplicate_index

            duplicate_count += 1
            continue

        # ---------------------------------------------------------------
        # New unique topic.
        # ---------------------------------------------------------------

        topic_copy = topic.copy()

        # Make sure tags have a predictable format.
        tags = topic_copy.get("tags")

        if not isinstance(tags, list):
            topic_copy["tags"] = []

        unique_index = len(unique_topics)

        unique_topics.append(topic_copy)

        if url:
            url_index[url] = unique_index

        if normalized_title:
            title_index[normalized_title] = unique_index

    logger.info(
        "Topic deduplication completed. "
        "Input=%d, unique=%d, duplicates_removed=%d",
        len(topics),
        len(unique_topics),
        duplicate_count,
    )

    return unique_topics


# ---------------------------------------------------------------------------
# Local test entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    sample_topics = [
        {
            "title": "OpenAI releases new AI model",
            "summary": "A new AI model was released.",
            "url": "https://example.com/openai-model",
            "source": "OpenAI",
            "published_at": "2026-08-08T10:00:00Z",
            "tags": ["ai", "openai"],
        },
        {
            "title": "OpenAI Releases New AI Model!",
            "summary": "Details about the new model.",
            "url": "https://example.com/openai-model/",
            "source": "Hacker News",
            "published_at": "2026-08-08T10:05:00Z",
            "tags": ["ai"],
        },
        {
            "title": "GitHub announces a new developer tool",
            "summary": "A new developer tool is trending.",
            "url": "https://example.com/github-tool",
            "source": "GitHub Trending",
            "published_at": "2026-08-08T09:00:00Z",
            "tags": ["github", "developer"],
        },
    ]

    result = deduplicate_topics(
        sample_topics
    )

    print(
        f"\nInput topics: {len(sample_topics)}"
    )

    print(
        f"Unique topics: {len(result)}\n"
    )

    for topic in result:
        print(topic)
        print("-" * 80)