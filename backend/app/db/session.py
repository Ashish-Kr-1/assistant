"""
Database session management (Phase 2 — Charaka IP PS045).

Reuses the project's existing PostgreSQL configuration (docker/docker-compose.yml,
.env POSTGRES_* vars). If PostgreSQL isn't reachable — e.g. in local dev/test
environments where the docker stack isn't running — this falls back to a local
SQLite file, mirroring the graceful-degrade convention already used for the LLM
factory and offline embeddings elsewhere in this project. No new database
technology is introduced.
"""

import logging
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base

from app.core.config import settings

logger = logging.getLogger("phase2_db")

Base = declarative_base()

_SQLITE_FALLBACK_PATH = Path(__file__).resolve().parents[3] / "ipsakti_cases.db"


def _postgres_url() -> str:
    return (
        f"postgresql+psycopg2://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    )


def _sqlite_url() -> str:
    return f"sqlite:///{_SQLITE_FALLBACK_PATH}"


def _build_engine():
    if settings.DATABASE_URL:
        logger.info("Phase 2 case store: using explicit DATABASE_URL.")
        return create_engine(settings.DATABASE_URL, pool_pre_ping=True)

    try:
        engine = create_engine(
            _postgres_url(), pool_pre_ping=True, connect_args={"connect_timeout": 2}
        )
        with engine.connect():
            pass
        logger.info("Phase 2 case store: connected to PostgreSQL at %s.", settings.POSTGRES_HOST)
        return engine
    except Exception as e:
        logger.warning(
            "Phase 2 case store: PostgreSQL unavailable (%s); falling back to local SQLite at %s.",
            e, _SQLITE_FALLBACK_PATH,
        )
        return create_engine(_sqlite_url(), connect_args={"check_same_thread": False})


engine = _build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Creates Phase 2 tables if they don't already exist. Safe to call repeatedly."""
    from app.db import models  # noqa: F401 (registers models with Base.metadata)
    Base.metadata.create_all(bind=engine)


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding a scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Tables are created eagerly at import time (in addition to the FastAPI startup
# hook in app/main.py) so Phase 2 works correctly under TestClient(app) usage
# that doesn't trigger ASGI lifespan events, and under direct service-layer use.
init_db()
