"""
Mount endpoint routers here so `src.main` can simply:

    from src.api import attach_routers
    attach_routers(app)
"""

from fastapi import FastAPI
from .router import main_router


def attach_routers(app: FastAPI):
    """Attach all endpoint routers to FastAPI instance."""
    app.include_router(main_router)


__all__ = ["attach_routers"]
