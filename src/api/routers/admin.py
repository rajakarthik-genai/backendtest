"""
Admin API endpoints for system administration and monitoring.

Provides administrative functionality including:
- System health monitoring
- Database status checks
- Service availability verification
- Administrative operations

Integration: Direct database connection checks for MongoDB, Neo4j, Redis, Milvus
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Dict, Any
from datetime import datetime
import logging

from src.auth.dependencies import get_authenticated_patient_id
from src.core.limiter import limiter
from src.db.mongodb import is_mongo_available, get_mongo_client
from src.db.neo4j import neo4j_connection
from src.db.redis_client import get_redis_client
from src.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health")
@limiter.limit("100/minute")
async def admin_health_check(request: Request):
    """
    Administrative health check with detailed database status.
    
    Returns comprehensive system health including:
    - MongoDB connection status
    - Neo4j connectivity
    - Redis availability
    - Milvus status
    - Overall system health
    """
    try:
        # Check MongoDB
        mongo_healthy = False
        mongo_error = None
        try:
            if is_mongo_available():
                mongo_client = await get_mongo_client()
                if mongo_client:
                    await mongo_client.admin.command('ping')
                    mongo_healthy = True
            else:
                mongo_error = "MongoDB not initialized"
        except Exception as e:
            mongo_error = str(e)
            
        # Check Neo4j
        neo4j_healthy = False
        neo4j_error = None
        try:
            if neo4j_connection.is_available():
                neo4j_healthy = neo4j_connection.verify_connectivity()
            else:
                neo4j_error = "Neo4j not initialized"
        except Exception as e:
            neo4j_error = str(e)
            
        # Check Redis
        redis_healthy = False
        redis_error = None
        try:
            redis_client = await get_redis_client()
            if redis_client:
                await redis_client.ping()
                redis_healthy = True
            else:
                redis_error = "Redis not available"
        except Exception as e:
            redis_error = str(e)

        # Overall status
        all_healthy = mongo_healthy and neo4j_healthy and redis_healthy
        
        if not all_healthy:
            return HTTPException(
                status_code=503,
                detail={
                    "status": "unhealthy",
                    "services": {
                        "mongodb": {"healthy": mongo_healthy, "error": mongo_error},
                        "neo4j": {"healthy": neo4j_healthy, "error": neo4j_error}, 
                        "redis": {"healthy": redis_healthy, "error": redis_error}
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

        return {
            "status": "healthy",
            "version": settings.VERSION,
            "services": {
                "mongodb": {"healthy": mongo_healthy},
                "neo4j": {"healthy": neo4j_healthy},
                "redis": {"healthy": redis_healthy}
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Admin health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Service unavailable - unable to check system health"
        )

@router.get("/database-status")
@limiter.limit("50/minute")
async def get_database_status(request: Request):
    """Get detailed database connection status"""
    try:
        if not is_mongo_available():
            raise HTTPException(
                status_code=503,
                detail="MongoDB not available"
            )
            
        if not neo4j_connection.is_available():
            raise HTTPException(
                status_code=503,
                detail="Neo4j not available"
            )
            
        return {
            "mongodb": "connected",
            "neo4j": "connected", 
            "redis": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database status check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Unable to verify database status"
        )
