import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from the repo-root .env (COHERE_API_KEY, LLM_PROVIDER, etc.)
# before Settings/ml_pipeline modules read them via os.getenv(). Without this, the app
# silently runs on offline hash-embeddings + deterministic heuristics even when real
# API keys are configured, because nothing else in the app ever reads the .env file.
load_dotenv(Path(__file__).resolve().parents[3] / ".env")


class Settings(BaseSettings):
    PROJECT_NAME: str = "Charaka IP Backend"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Vector Database
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    
    # Knowledge Graph
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "ipsakti_secret_pass")

    # Relational Database (Phase 2 — Case / Innovation Intake persistence)
    # Explicit DATABASE_URL always wins. Otherwise the app attempts the configured
    # PostgreSQL instance and falls back to a local SQLite file if it isn't reachable
    # (see backend/app/db/session.py), mirroring ml_pipeline/crag/llm_factory.py's
    # graceful-degrade pattern so Phase 2 never requires a live DB in tests/dev.
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "ipsakti")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "ipsakti_db_pass")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "ipsakti_db")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))

    # Redis Query Cache (Sub-5ms response for repeated questions)
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_CACHE_TTL: int = int(os.getenv("REDIS_CACHE_TTL", "86400"))  # 24 hours
    REDIS_ENABLED: bool = os.getenv("REDIS_ENABLED", "true").lower() in ("true", "1", "yes")

    # DPDP Audit Log Settings
    LOG_ANONYMOUS_QUERIES: bool = True
    LEGAL_DISCLAIMER_TEXT: str = (
        "INFORMATION PROVIDED IS FOR EDUCATIONAL & REGULATORY GUIDANCE PURPOSES ONLY "
        "AND DOES NOT CONSTITUTE FORMAL LEGAL ADVICE."
    )
    
    class Config:
        case_sensitive = True

settings = Settings()
