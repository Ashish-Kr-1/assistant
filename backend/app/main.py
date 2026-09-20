from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router
from app.db.session import init_db

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Multilingual RAG-based AI Assistant for Intellectual Property & Regulatory Guidance in Ayurveda.",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS Middleware Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

# Mount the standalone Charaka IP agent app (root-level main.py: corpus stats/
# versions/refresh, live connector search, Bhashini voice STT/TTS, and the
# security/audit admin endpoints) so both backends run from this one process
# instead of two separate uvicorn servers. The frontend's /api/v1/* contract
# above is untouched; these just become additionally reachable under /agent.
from main import app as charaka_agent_app  # noqa: E402  (repo root, via PYTHONPATH=.)

app.mount("/agent", charaka_agent_app)


@app.on_event("startup")
async def _init_phase2_db():
    """Creates Phase 2 (Innovation Intake / Case) tables on startup, if missing."""
    init_db()


@app.get("/")
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "status": "ONLINE",
        "version": "1.0.0",
        "docs_url": "/docs",
        "disclaimer": settings.LEGAL_DISCLAIMER_TEXT
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
