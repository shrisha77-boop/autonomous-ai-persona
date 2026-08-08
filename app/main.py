from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database.database import Base, engine
from app.models.agent import Agent  # noqa: F401
from app.models.post import Post

from app.api.v1.routes.agent import router as agent_router

from app.api.v1.routes.feed import router as feed_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()


app = FastAPI(
    title="SignalForge AI",
    description="Autonomous AI technology persona",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(agent_router)
app.include_router(feed_router)

@app.get("/")
async def root():
    return {
        "message": "SignalForge AI is running",
        "status": "healthy",
    }