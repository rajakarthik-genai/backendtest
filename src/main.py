"""
Medical Digital Twin API - Main Application Entry Point
Production-ready FastAPI application with comprehensive error handling
"""

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
from prometheus_client import Counter, Histogram, generate_latest
from prometheus_client.core import CollectorRegistry
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded


import sys
import os

from pathlib import Path

# Add project root to Python path BEFORE local imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.core.limiter import limiter

from src.api.routers import (
    documents, chat, expert_opinion, health, timeline, reports, visualization,
    admin, system, user, symptoms, events, anatomy, auth
)
from src.api.dependencies import security
from src.core.config import settings
from src.core.logging import setup_logging
from src.db.mongodb import connect_to_mongo, close_mongo_connection
from src.db.neo4j import neo4j_connection
from src.db.redis_client import get_redis_client
from src.db.milvus_client import MilvusClient
# from src.db.minio_client import init_minio  # Temporarily disabled until container rebuild
from src.services.document_processor import start_document_processor, stop_document_processor
from src.core.exceptions import MedicalTwinException

# Setup logging
logger = setup_logging()

# Metrics
REGISTRY = CollectorRegistry()
REQUEST_COUNT = Counter(
    'medical_api_requests_total', 
    'Total requests',
    ['method', 'endpoint', 'status'],
    registry=REGISTRY
)
REQUEST_LATENCY = Histogram(
    'medical_api_request_duration_seconds',
    'Request latency',
    ['method', 'endpoint'],
    registry=REGISTRY
)

# Rate limiter instance will be stored in app.state

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle with graceful database connection handling"""
    try:
        # Startup
        logger.info("Starting Medical Digital Twin API...")
        
        # Connect to databases with graceful degradation
        try:
            await connect_to_mongo()
            logger.info("MongoDB initialized successfully")
        except Exception as e:
            logger.warning(f"MongoDB initialization failed: {e} - continuing in degraded mode")
        
        try:
            await neo4j_connection.connect()
            logger.info("Neo4j initialized successfully")
        except Exception as e:
            logger.warning(f"Neo4j initialization failed: {e} - continuing in degraded mode")
        
        try:
            app.state.redis = await get_redis_client()
            if app.state.redis:
                await app.state.redis.ping()
                logger.info("Redis initialized successfully")
        except Exception as e:
            logger.warning(f"Redis initialization failed: {e} - continuing in degraded mode")
            app.state.redis = None

        # Initialize Milvus
        try:
            milvus_client = MilvusClient()
            await milvus_client.initialize_collections()
            app.state.milvus = milvus_client
            logger.info("Milvus initialized successfully")
        except Exception as e:
            logger.warning(f"Milvus initialization failed: {e} - continuing in degraded mode")
            app.state.milvus = None

        # Initialize MinIO (temporarily disabled until container rebuild)
        # try:
        #     minio_success = await init_minio()
        #     if minio_success:
        #         logger.info("MinIO initialized successfully")
        #     else:
        #         logger.warning("MinIO initialization failed - continuing in degraded mode")
        # except Exception as e:
        #     logger.warning(f"MinIO initialization failed: {e} - continuing in degraded mode")
        
        # Start document processing service
        try:
            import asyncio
            asyncio.create_task(start_document_processor())
            logger.info("Document processor started successfully")
        except Exception as e:
            logger.warning(f"Document processor failed to start: {e}")
        
        logger.info("Medical Digital Twin API started successfully")
        
        yield
        
    finally:
        # Shutdown
        logger.info("Shutting down Medical Digital Twin API...")
        stop_document_processor()
        
        # Close database connections gracefully
        try:
            await close_mongo_connection()
        except Exception as e:
            logger.warning(f"Error closing MongoDB: {e}")
            
        try:
            await neo4j_connection.close()
        except Exception as e:
            logger.warning(f"Error closing Neo4j: {e}")
            
        try:
            if hasattr(app.state, "redis") and app.state.redis:
                await app.state.redis.close()
        except Exception as e:
            logger.warning(f"Error closing Redis: {e}")
            
        try:
            if hasattr(app.state, "milvus") and app.state.milvus:
                app.state.milvus.close()
        except Exception as e:
            logger.warning(f"Error closing Milvus: {e}")
        
        logger.info("Medical Digital Twin API shutdown complete")

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Medical Digital Twin API with AI-powered health analysis",
    lifespan=lifespan,
    # Remove global security dependency - use individual endpoint authentication
    # dependencies=[Depends(security)],
    docs_url="/api/docs" if not settings.PRODUCTION else None,
    redoc_url="/api/redoc" if not settings.PRODUCTION else None,
)

# -------------------------------------------------------------------
# Customize OpenAPI to add global JWTBearer security requirement so
# Swagger UI automatically sends the Authorization header once the
# user clicks "Authorize".
# -------------------------------------------------------------------
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    # Ensure only one HTTP bearer scheme exists
    components = openapi_schema.setdefault("components", {})
    security_schemes = components.setdefault("securitySchemes", {})
    # Remove any autogenerated JWTBearer to avoid duplicates
    security_schemes.pop("JWTBearer", None)
    # Add/ensure single scheme named HTTPBearer
    security_schemes["HTTPBearer"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    # Apply globally to all paths
    openapi_schema["security"] = [{"HTTPBearer": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# Add JWT authentication middleware to extract user_id from tokens
from src.auth.middleware import JWTAuthMiddleware
app.add_middleware(JWTAuthMiddleware, require_auth=False)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middleware for request tracking
@app.middleware("http")
async def track_requests(request: Request, call_next):
    """Track request metrics and add request ID"""
    start_time = time.time()
    request_id = request.headers.get("X-Request-ID", f"req_{int(time.time() * 1000)}")
    
    # Add request ID to request state
    request.state.request_id = request_id
    
    # Process request
    response = await call_next(request)
    
    # Track metrics
    duration = time.time() - start_time
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    # Add headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(duration)
    
    return response

# Global exception handler
@app.exception_handler(MedicalTwinException)
async def medical_exception_handler(request: Request, exc: MedicalTwinException):
    """Handle custom medical twin exceptions"""
    logger.error(f"Medical Twin Exception: {exc.detail}", exc_info=True)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "detail": exc.detail,
            "request_id": getattr(request.state, "request_id", None)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "detail": "An internal error occurred. Please try again later.",
            "request_id": getattr(request.state, "request_id", None)
        }
    )

# Include routers with correct prefixes to avoid 404 errors
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(expert_opinion.router, prefix="/api/v1/expert-opinion", tags=["expert"])
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(timeline.router, prefix="/api/v1/timeline", tags=["timeline"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(visualization.router, prefix="/api/v1/visualization", tags=["visualization"])

# Add new routers with proper prefixes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(system.router, prefix="/api/v1/system", tags=["system"])
app.include_router(user.router, prefix="/api/v1/user", tags=["user"])
app.include_router(symptoms.router, prefix="/api/v1/symptoms", tags=["symptoms"])
app.include_router(events.router, prefix="/api/v1/events", tags=["events"])  
app.include_router(anatomy.router, prefix="/api/v1/anatomy", tags=["anatomy"])

# Health check endpoint
@app.get("/health")
@limiter.limit("100/minute")
async def health_check(request: Request):
    """Health check endpoint"""
    try:
        # Check database connections
        redis_healthy = await app.state.redis.ping()
        neo4j_healthy = neo4j_connection.verify_connectivity()
        # MongoDB health check
        from src.db.mongodb import get_mongo_client
        mongo_healthy = False
        try:
            mongo_client = await get_mongo_client()
            if mongo_client is not None:
                await mongo_client.admin.command('ping')
                mongo_healthy = True
        except Exception as e:
            logger.warning(f"MongoDB health check failed: {e}")
            mongo_healthy = False

        status = "healthy" if all([redis_healthy, neo4j_healthy, mongo_healthy]) else "degraded"

        return {
            "status": status,
            "version": settings.VERSION,
            "services": {
                "mongodb": mongo_healthy,
                "neo4j": neo4j_healthy,
                "redis": redis_healthy,
            },
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest(REGISTRY)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "docs": "/api/docs" if not settings.PRODUCTION else None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main_new:app",
        host="0.0.0.0",
        port=8000,
        reload=not settings.PRODUCTION,
        log_config=None  # Use our custom logging
    )
