import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "SignalForge AI"
    VERSION: str = "0.1.0"
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./signalforge.db"
    
    # Scheduler & Publishing
    PUBLISH_INTERVAL_SECONDS: int = 60
    TOPIC_SCORE_THRESHOLD: int = 60
    
    # Ollama LLM Config
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    
    # Topic Discovery limits
    RSS_LIMIT: int = 10
    HACKERNEWS_LIMIT: int = 30
    GITHUB_LIMIT: int = 25
    ARXIV_LIMIT: int = 20

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
