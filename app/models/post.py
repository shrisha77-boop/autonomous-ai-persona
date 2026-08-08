import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    agent_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("agents.id"),
        nullable=False,
        index=True,
    )

    topic_title: Mapped[str] = mapped_column(
    String(500),
    nullable=False,
    index=True,
   )

    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    rationale: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    sources: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="[]",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )