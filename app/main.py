from fastapi import FastAPI

app = FastAPI(
    title="SignalForge AI",
    description="Autonomous AI technology persona",
    version="0.1.0",
)


@app.get("/")
async def root():
    return {
        "message": "SignalForge AI is running",
        "status": "healthy",
    }