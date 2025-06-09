from fastapi import APIRouter

from .upload import router as upload_router
from .chat import router as chat_router
from .timeline import router as timeline_router
from .anatomy import router as anatomy_router

api_router = APIRouter()
api_router.include_router(upload_router)
api_router.include_router(chat_router)
api_router.include_router(timeline_router)
api_router.include_router(anatomy_router)
