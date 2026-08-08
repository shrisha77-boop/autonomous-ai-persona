import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.models.agent import Agent
from app.models.post import Post
from app.schemas.feed import FeedResponse, PostResponse

router = APIRouter(
    prefix="/api/agent",
    tags=["Feed"],
)


@router.get("/feed", response_model=FeedResponse)
async def get_feed(
    agentId: str,
    db: AsyncSession = Depends(get_db),
):
    # Verify that the agent exists.
    agent_result = await db.execute(
        select(Agent).where(Agent.id == agentId)
    )

    agent = agent_result.scalar_one_or_none()

    if agent is None:
        raise HTTPException(
            status_code=404,
            detail="Agent not found",
        )

    # Get newest posts first.
    result = await db.execute(
        select(Post)
        .where(Post.agent_id == agentId)
        .order_by(Post.created_at.desc())
    )

    posts = result.scalars().all()

    response_posts = []

    for post in posts:
        try:
            sources = json.loads(post.sources)
        except (json.JSONDecodeError, TypeError):
            sources = []

        response_posts.append(
            PostResponse(
                id=post.id,
                createdAt=post.created_at,
                text=post.text,
                rationale=post.rationale,
                sources=sources,
            )
        )

    return FeedResponse(posts=response_posts)