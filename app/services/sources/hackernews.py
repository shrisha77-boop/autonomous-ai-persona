from datetime import datetime, timezone

import requests

from app.models.topic import TopicCandidate


TOP_STORIES_URL = (
    "https://hacker-news.firebaseio.com/v0/topstories.json"
)

ITEM_URL = (
    "https://hacker-news.firebaseio.com/v0/item/{}.json"
)

REQUEST_TIMEOUT = 5


def discover_hackernews_topics(
    limit: int = 20,
) -> list[TopicCandidate]:
    candidates: list[TopicCandidate] = []

    # Fetch the list of top stories.
    try:
        response = requests.get(
            TOP_STORIES_URL,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        story_ids = response.json()[:limit]

    except requests.RequestException as exc:
        print(
            f"[SignalForge] Failed to fetch Hacker News top stories: "
            f"{exc}",
            flush=True,
        )
        return candidates

    # Fetch each individual story.
    for story_id in story_ids:
        try:
            story_response = requests.get(
                ITEM_URL.format(story_id),
                timeout=REQUEST_TIMEOUT,
            )
            story_response.raise_for_status()

            story = story_response.json()

            if not story:
                continue

            # Ignore deleted/dead stories.
            if story.get("deleted") or story.get("dead"):
                continue

            title = story.get("title", "").strip()

            if not title:
                continue

            url = story.get("url", "").strip()

            published_at = None

            if story.get("time"):
                published_at = datetime.fromtimestamp(
                    story["time"],
                    tz=timezone.utc,
                )

            candidates.append(
                TopicCandidate(
                    title=title,
                    summary=title,
                    source_url=url,
                    source_name="Hacker News",
                    published_at=published_at,
                )
            )

        except requests.RequestException as exc:
            print(
                f"[SignalForge] Skipping Hacker News story "
                f"{story_id}: {exc}",
                flush=True,
            )
            continue

    print(
        f"[SignalForge] Hacker News discovery found "
        f"{len(candidates)} topics.",
        flush=True,
    )

    return candidates