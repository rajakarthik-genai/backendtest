"""
FastAPI entry-point – starts app, connects to DBs, and mounts routers.

Run via:
    uvicorn src.main:app --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI
import agentops
from src.config.settings import settings
from src.api import attach_routers
from src.utils.logging import logger
from src.tools import init_mongo, init_graph, init_milvus


def _startup():
    """Initialise DB/tool connections and AgentOps."""
    init_mongo(settings.mongo_uri)
    init_graph(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)
    init_milvus(settings.milvus_host, settings.milvus_port)
    if settings.agentops_api_key:
        agentops.init(settings.agentops_api_key)
        logger.info("AgentOps initialised.")
    logger.info("Startup complete.")


app = FastAPI(
    title="Medical Digital-Twin Backend",
    version="1.0.0",
    description="RAG-powered multi-agent backend for personalised medical insights.",
)

attach_routers(app)


@app.on_event("startup")
def on_startup():
    _startup()


@app.get("/", tags=["health"])
def health():
    return {"status": "ok"}
