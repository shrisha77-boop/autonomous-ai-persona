from datetime import datetime, timezone

import requests

from app.models.topic import TopicCandidate


TOP_STORIES_URL = (
    "https://hacker-news.firebaseio.com/v0/topstories.json"
)

ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"


def discover_hackernews_topics(
    limit: int = 20,
) -> list[TopicCandidate]:
    candidates: list[TopicCandidate] = []

    response = requests.get(
        TOP_STORIES_URL,
        timeout=10,
    )
    response.raise_for_status()

    story_ids = response.json()[:limit]

    for story_id in story_ids:
        try:
            story_response = requests.get(
                ITEM_URL.format(story_id),
                timeout=10,
            )
            story_response.raise_for_status()

            story = story_response.json()

            if not story:
                continue

            title = story.get("title", "").strip()
            url = story.get("url", "").strip()

            if not title:
                continue

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
                f"Failed to fetch Hacker News story {story_id}: {exc}",
                flush=True,
            )

    return candidates