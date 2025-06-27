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
from src.db.mongo_db import init_mongo
from src.db.neo4j_db import init_graph
from src.db.milvus_db import init_milvus
from src.db.redis_db import init_redis


async def _startup():
    """Initialize DB/tool connections and AgentOps."""
    try:
        # Initialize databases
        await init_mongo(settings.mongo_uri, settings.mongo_db_name)
        init_graph(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)
        init_milvus(settings.milvus_host, settings.milvus_port)
        init_redis(settings.redis_host, settings.redis_port)
        
        # Initialize AgentOps if API key provided
        if settings.agentops_api_key:
            agentops.init(settings.agentops_api_key)
            logger.info("AgentOps initialized")
        
        logger.info("All systems initialized successfully")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise


app = FastAPI(
    title="MediTwin Backend",
    version="1.0.0",
    description="HIPAA-compliant multi-agent RAG backend for personalized medical insights",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Attach API routers
attach_routers(app)


@app.on_event("startup")
async def on_startup():
    await _startup()


@app.get("/", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "MediTwin Backend",
        "version": "1.0.0"
    }


@app.get("/health", tags=["health"])
async def detailed_health():
    """Detailed health check with system status."""
    try:
        # Basic health check - could be expanded to check DB connections
        return {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",
            "services": {
                "api": "healthy",
                "mongodb": "unknown",  # Could check connection
                "neo4j": "unknown",
                "milvus": "unknown", 
                "redis": "unknown"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy", 
            "error": str(e)
        }
