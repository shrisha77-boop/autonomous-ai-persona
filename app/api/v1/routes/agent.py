from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.models.agent import Agent
from app.schemas.agent import AgentInitRequest, AgentInitResponse

router = APIRouter(
    prefix="/api/agent",
    tags=["Agent"],
)


@router.post("/init", response_model=AgentInitResponse)
async def initialize_agent(
    request: AgentInitRequest,
    db: AsyncSession = Depends(get_db),
):
    agent = Agent(
        name=request.persona.name,
        domain=request.persona.domain,
    )

    db.add(agent)
    await db.commit()
    await db.refresh(agent)

    return AgentInitResponse(
        agentId=agent.id,
    )
