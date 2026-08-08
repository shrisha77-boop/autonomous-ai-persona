from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, field_serializer


class PostResponse(BaseModel):
    id: str
    createdAt: datetime
    text: str
    rationale: str
    sources: list[str]

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("createdAt")
    def serialize_created_at(self, dt: datetime, _info) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()


class FeedResponse(BaseModel):
    posts: list[PostResponse]