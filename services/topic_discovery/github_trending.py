"""GitHub Trending topic discovery service.

This module fetches repositories from GitHub Trending and converts
technology-relevant repositories into topic candidates.

The module is intentionally independent of:
- FastAPI
- SQLAlchemy
- SQLite
- APScheduler
- Backend API routes

It can be consumed by the Topic Discovery aggregator.
"""

from __future__ import annotations
import html
import logging
import re
from datetime import datetime, timezone
from typing import Any

import httpx


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GITHUB_TRENDING_URL = "https://github.com/trending"

REQUEST_TIMEOUT = 15.0

DEFAULT_LANGUAGE = ""

DEFAULT_LIMIT = 25


# Repository topics/keywords that indicate AI or technology relevance.
TECH_KEYWORDS: tuple[str, ...] = (
    "ai",
    "artificial-intelligence",
    "machine-learning",
    "deep-learning",
    "llm",
    "large-language-model",
    "generative-ai",
    "chatgpt",
    "openai",
    "anthropic",
    "gemini",
    "claude",
    "neural-network",
    "robotics",
    "computer-vision",
    "nlp",
    "natural-language-processing",
    "python",
    "developer-tools",
    "developer",
    "programming",
    "software",
    "open-source",
    "cybersecurity",
    "quantum-computing",
    "cloud",
    "database",
)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _clean_text(value: str) -> str:
    """Clean unnecessary whitespace and HTML entities from text.

    Args:
        value: Raw text.

    Returns:
        Cleaned text.
    """
    value = html.unescape(value)

    return " ".join(value.split()).strip()


def _matches_keyword(text: str, keyword: str) -> bool:
    """Check whether a keyword occurs as a meaningful term.

    Args:
        text: Text to search.
        keyword: Keyword to search for.

    Returns:
        True if the keyword occurs in the text.
    """
    normalized_text = text.lower()
    normalized_keyword = keyword.lower()

    # GitHub repository metadata commonly uses hyphens.
    # Convert them to spaces so matching works for both forms.
    normalized_text = normalized_text.replace("-", " ")
    normalized_keyword = normalized_keyword.replace("-", " ")

    pattern = rf"(?<!\w){re.escape(normalized_keyword)}(?!\w)"

    return re.search(
        pattern,
        normalized_text,
        flags=re.IGNORECASE,
    ) is not None


def _extract_tags(text: str) -> list[str]:
    """Extract technology tags from repository metadata.

    Args:
        text: Combined repository name and description.

    Returns:
        List of matching technology keywords.
    """
    return [
        keyword
        for keyword in TECH_KEYWORDS
        if _matches_keyword(text, keyword)
    ]


def _is_technology_repository(
    repository_name: str,
    description: str,
) -> bool:
    """Determine whether a repository is technology-related.

    Args:
        repository_name: GitHub repository name.
        description: Repository description.

    Returns:
        True if the repository matches at least one technology
        keyword.
    """
    searchable_text = f"{repository_name} {description}"

    return any(
        _matches_keyword(searchable_text, keyword)
        for keyword in TECH_KEYWORDS
    )


def _extract_repository_url(
    repository_name: str,
) -> str:
    """Build the canonical GitHub repository URL.

    Args:
        repository_name:
            Repository identifier in the form ``owner/name``.

    Returns:
        GitHub repository URL.
    """
    return f"https://github.com/{repository_name}"


def _normalize_repository(
    repository_name: str,
    description: str,
) -> dict[str, Any]:
    """Convert a GitHub repository into a topic candidate.

    Args:
        repository_name: Repository identifier.
        description: Repository description.

    Returns:
        Topic candidate using the common discovery format.
    """
    cleaned_name = _clean_text(repository_name)
    cleaned_description = _clean_text(description)

    combined_text = f"{cleaned_name} {cleaned_description}"

    return {
        "title": cleaned_name,
        "summary": cleaned_description,
        "url": _extract_repository_url(cleaned_name),
        "source": "GitHub Trending",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "tags": _extract_tags(combined_text),
    }


# ---------------------------------------------------------------------------
# HTML parsing
# ---------------------------------------------------------------------------

def _parse_trending_repositories(
    html: str,
) -> list[dict[str, Any]]:
    """Parse repositories from GitHub Trending HTML.

    GitHub Trending repository entries are represented by article
    elements with the CSS class ``Box-row``.

    Args:
        html: Raw HTML returned by GitHub Trending.

    Returns:
        List of technology-related repository candidates.
    """
    repositories: list[dict[str, Any]] = []

    article_pattern = re.compile(
        r'<article[^>]*class="[^"]*Box-row[^"]*"[^>]*>(.*?)</article>',
        flags=re.IGNORECASE | re.DOTALL,
    )

    articles = article_pattern.findall(html)

    for article in articles:
        try:
            # Extract repository owner/name from the first repository link.
            repo_match = re.search(
                r'href="/([^"]+/[^"]+)"',
                article,
                flags=re.IGNORECASE,
            )

            if not repo_match:
                continue

            repository_name = _clean_text(
                repo_match.group(1)
            )
            if repository_name.startswith("sponsors/"):
                continue

            # Remove trailing HTML fragments if needed.
            repository_name = repository_name.split('"')[0].strip()

            # Extract the repository description.
            description_match = re.search(
                r'<p[^>]*class="[^"]*color-fg-muted[^"]*"[^>]*>(.*?)</p>',
                article,
                flags=re.IGNORECASE | re.DOTALL,
            )

            description = ""

            if description_match:
                description = re.sub(
                    r"<[^>]+>",
                    " ",
                    description_match.group(1),
                )

                description = _clean_text(description)

            if not repository_name:
                continue

            if not _is_technology_repository(
                repository_name,
                description,
            ):
                continue

            repositories.append(
                _normalize_repository(
                    repository_name,
                    description,
                )
            )

        except Exception:
            logger.exception(
                "Failed to parse a GitHub Trending repository."
            )

    return repositories


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------

async def _fetch_trending_page(
    client: httpx.AsyncClient,
    language: str = DEFAULT_LANGUAGE,
) -> str:
    """Fetch the GitHub Trending HTML page.

    Args:
        client: HTTPX asynchronous client.
        language: Optional GitHub programming language filter.

    Returns:
        Raw HTML content.

    Raises:
        httpx.HTTPError:
            If the request fails.
    """
    url = GITHUB_TRENDING_URL

    if language:
        url = f"{url}/{language}"

    response = await client.get(
        url,
        headers={
            "User-Agent": "SignalForge-AI-Topic-Discovery/1.0",
            "Accept": "text/html",
        },
    )

    response.raise_for_status()

    return response.text


# ---------------------------------------------------------------------------
# Public service function
# ---------------------------------------------------------------------------

async def fetch_github_trending_topics(
    limit: int = DEFAULT_LIMIT,
    language: str = DEFAULT_LANGUAGE,
) -> list[dict[str, Any]]:
    """Fetch AI and technology repositories from GitHub Trending.

    Args:
        limit:
            Maximum number of technology repositories to return.

        language:
            Optional GitHub programming language filter.
            Empty string means all languages.

    Returns:
        List of topic candidates using the common format.

    Notes:
        GitHub Trending is parsed from its public HTML page because
        GitHub does not provide an official public Trending API.

        Network failures are handled gracefully by returning an
        empty list.
    """
    if limit <= 0:
        logger.warning(
            "GitHub Trending limit must be greater than zero."
        )
        return []

    logger.info(
        "Starting GitHub Trending discovery. Limit=%d, language=%s",
        limit,
        language or "all",
    )

    try:
        async with httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True,
        ) as client:

            html = await _fetch_trending_page(
                client,
                language=language,
            )

            repositories = _parse_trending_repositories(
                html
            )

            repositories = repositories[:limit]

            logger.info(
                "GitHub Trending discovery completed. "
                "Found %d technology repositories.",
                len(repositories),
            )

            return repositories

    except httpx.HTTPError as exc:
        logger.error(
            "GitHub Trending request failed: %s",
            exc,
        )
        return []

    except Exception:
        logger.exception(
            "Unexpected error during GitHub Trending discovery."
        )
        return []


# ---------------------------------------------------------------------------
# Local test entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        """Run a local test of GitHub Trending discovery."""
        topics = await fetch_github_trending_topics()

        print(
            f"\nFound {len(topics)} GitHub Trending topics.\n"
        )

        for topic in topics:
            print(topic)
            print("-" * 80)

    asyncio.run(main())