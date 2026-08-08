from pydantic import BaseModel, Field


class PersonaInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    domain: str = Field(min_length=1, max_length=100)


class AgentInitRequest(BaseModel):
    persona: PersonaInput


class AgentInitResponse(BaseModel):
    agentId: str