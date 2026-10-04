from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Agent Memory OS"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "https://app.agentmemory.io",
    ]

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    DATABASE_URL: str = ""

    # Qdrant — free tier: sign up at https://cloud.qdrant.io, create a free
    # cluster, paste its URL + API key here. Free tier = 1GB RAM, 4GB disk,
    # permanently free, no credit card. For local dev only, point to
    # http://localhost:6333 with `docker run -p 6333:6333 qdrant/qdrant`.
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str = ""
    QDRANT_COLLECTION: str = "agent_memories"

    # OpenAI (for embeddings)
    OPENAI_API_KEY: str = ""
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIM: int = 1536

    # Auth
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Azure-specific: these are injected as env vars by Container Apps,
    # sourced from Key Vault via secretRef in the container app config.
    # No .env file is used in production — see azure/containerapp.yaml

    class Config:
        env_file = ".env"


settings = Settings()
