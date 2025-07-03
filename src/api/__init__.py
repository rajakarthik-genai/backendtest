"""
Mount endpoint routers here so `src.main` can simply:

    from src.api import attach_routers
    attach_routers(app)

New routers can be added to `_ROUTERS` list.
"""

from fastapi import FastAPI

from src.api.endpoints import (
    auth,
    chat,
    expert_opinion,
    upload,
    timeline,
    anatomy,
    events,
)

_ROUTERS = [
    auth,
    chat,
    expert_opinion,
    upload,
    timeline,
    anatomy,
    events,
]


def attach_routers(app: FastAPI):
    """Attach all endpoint routers to FastAPI instance."""
    for r in _ROUTERS:
        app.include_router(r)
