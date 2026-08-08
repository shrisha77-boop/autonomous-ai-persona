from dataclasses import dataclass
from datetime import datetime


@dataclass
class TopicCandidate:
    title: str
    summary: str
    source_url: str
    source_name: str
    published_at: datetime | None = None