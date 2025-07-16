"""
FastAPI entry-point – starts app, connects to DBs, and mounts routers.

Run via:
    uvicorn src.main:app --host 0.0.0.0 --port 8000
    
Or directly:
    python src/main.py --host 0.0.0.0 --port 8000
"""

import sys
import os
from pathlib import Path

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import agentops
from src.config.settings import settings
from src.api.router import main_router
from src.utils.logging import logger
from src.db.mongo_db import init_mongo
from src.db.neo4j_db import init_graph
from src.db.milvus_db import init_milvus
from src.db.redis_db import init_redis
from src.auth.middleware import JWTAuthMiddleware
from src.middleware.request_logging import RequestLoggingMiddleware
from src.middleware.user_initialization import UserInitializationMiddleware


async def _startup():
    """Initialize DB/tool connections and AgentOps."""
    errors = []
    
    # Try to initialize databases (optional for development)
    try:
        await init_mongo(settings.mongo_uri, settings.mongo_db_name)
        logger.info("MongoDB initialized successfully")
    except Exception as e:
        logger.warning(f"MongoDB initialization failed: {e}")
        errors.append("MongoDB")
    
    try:
        init_graph(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)
        logger.info("Neo4j initialized successfully")
    except Exception as e:
        logger.warning(f"Neo4j initialization failed: {e}")
        errors.append("Neo4j")
    
    try:
        init_milvus(settings.milvus_host, settings.milvus_port)
        logger.info("Milvus initialized successfully")
    except Exception as e:
        logger.warning(f"Milvus initialization failed: {e}")
        errors.append("Milvus")
    
    try:
        init_redis(settings.redis_host, settings.redis_port)
        logger.info("Redis initialized successfully")
    except Exception as e:
        logger.warning(f"Redis initialization failed: {e}")
        errors.append("Redis")
    
    # Initialize AgentOps if API key provided
    if settings.agentops_api_key:
        try:
            agentops.init(settings.agentops_api_key)
            logger.info("AgentOps initialized")
        except Exception as e:
            logger.warning(f"AgentOps initialization failed: {e}")
    
    if errors:
        logger.warning(f"Some services failed to initialize: {', '.join(errors)}")
        logger.info("Server will run in limited mode (authentication and basic APIs only)")
    else:
        logger.info("All systems initialized successfully")
    
    logger.info("Server startup completed")


app = FastAPI(
    title="MediTwin Backend",
    version="1.0.0",
    description="HIPAA-compliant multi-agent RAG backend for personalized medical insights",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware, log_requests=True)

# Add JWT authentication middleware  
# NOTE: Set require_auth=True for production with proper JWT tokens
# For development/testing, you can use require_auth=False
jwt_require_auth = getattr(settings, 'jwt_require_auth', False)
app.add_middleware(JWTAuthMiddleware, require_auth=jwt_require_auth)

# Add user initialization middleware (after auth middleware)
app.add_middleware(UserInitializationMiddleware)

# Attach main API router
app.include_router(main_router)


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
