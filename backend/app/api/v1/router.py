from fastapi import APIRouter
from app.api.v1.endpoints import query, classify, abs, bhashini, escalation, cases, knowledge_graph

api_router = APIRouter()

api_router.include_router(query.router, tags=["RAG Query Engine"])
api_router.include_router(classify.router, tags=["Formulation Classifier"])
api_router.include_router(cases.router, tags=["Phase 2 — Innovation Intake & Cases"])
api_router.include_router(abs.router, tags=["Access & Benefit-Sharing (ABS)"])
api_router.include_router(bhashini.router, tags=["Bhashini Multilingual"])
api_router.include_router(escalation.router, tags=["Human Facilitator Escalation"])
api_router.include_router(knowledge_graph.router, tags=["Knowledge Graph"])

