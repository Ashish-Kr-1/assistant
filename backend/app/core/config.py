import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "IP-SAKTI Sahayak Backend"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Vector Database
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    
    # Knowledge Graph
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "ipsakti_secret_pass")
    
    # DPDP Audit Log Settings
    LOG_ANONYMOUS_QUERIES: bool = True
    LEGAL_DISCLAIMER_TEXT: str = (
        "INFORMATION PROVIDED IS FOR EDUCATIONAL & REGULATORY GUIDANCE PURPOSES ONLY "
        "AND DOES NOT CONSTITUTE FORMAL LEGAL ADVICE."
    )
    
    class Config:
        case_sensitive = True

settings = Settings()
