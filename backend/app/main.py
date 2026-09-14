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
