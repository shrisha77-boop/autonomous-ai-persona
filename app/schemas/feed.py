from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PostResponse(BaseModel):
    id: str
    createdAt: datetime
    text: str
    rationale: str
    sources: list[str]

    model_config = ConfigDict(from_attributes=True)


class FeedResponse(BaseModel):
    posts: list[PostResponse]