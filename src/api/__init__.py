"""
Mount endpoint routers here so `src.main` can simply:

    from src.api import attach_routers
    attach_routers(app)

New routers can be added to `_ROUTERS` list.
"""

from fastapi import FastAPI

from src.api.endpoints import (
    chat,
    expert_opinion,
    upload,
    timeline,
    anatomy,
    events,
    tools,
    openai_compat,
    openai_compatible,
)

_ROUTERS = [
    chat,
    expert_opinion,
    upload,
    timeline,
    anatomy,
    events,
    tools,
    openai_compat,
    openai_compatible,
]


def attach_routers(app: FastAPI):
    """Attach all endpoint routers to FastAPI instance."""
    for r in _ROUTERS:
        app.include_router(r)
