"""
API router for v1 endpoints.
"""

from fastapi import APIRouter

from src.api.v1.endpoints import (
    admin,
    anatomy,
    analytics,
    chat,
    documents,
    events,
    expert_opinion,
    knowledge_base,
    medical_analysis,
    openai_compat,
    openai_compatible,
    system_info,
    timeline,
    tools,
    upload,
    user_profile,
)

api_router = APIRouter()

# v1 routes
api_router.include_router(admin, prefix="/admin", tags=["admin"])
api_router.include_router(anatomy, prefix="/anatomy", tags=["anatomy"])
api_router.include_router(analytics, prefix="/analytics", tags=["analytics"])
api_router.include_router(chat, prefix="/chat", tags=["chat"])
api_router.include_router(documents, prefix="/documents", tags=["documents"])
api_router.include_router(events, prefix="/events", tags=["events"])
api_router.include_router(
    expert_opinion, prefix="/expert_opinion", tags=["expert_opinion"]
)
api_router.include_router(
    knowledge_base, prefix="/knowledge_base", tags=["knowledge_base"]
)
api_router.include_router(
    medical_analysis, prefix="/medical_analysis", tags=["medical_analysis"]
)
api_router.include_router(
    openai_compat, prefix="/openai_compat", tags=["openai_compat"]
)
api_router.include_router(
    openai_compatible, prefix="/openai_compatible", tags=["openai_compatible"]
)
api_router.include_router(
    system_info, prefix="/system_info", tags=["system_info"]
)
api_router.include_router(timeline, prefix="/timeline", tags=["timeline"])
api_router.include_router(tools, prefix="/tools", tags=["tools"])
api_router.include_router(upload, prefix="/upload", tags=["upload"])
api_router.include_router(
    user_profile, prefix="/user_profile", tags=["user_profile"]
)

__all__ = ["api_router"]
