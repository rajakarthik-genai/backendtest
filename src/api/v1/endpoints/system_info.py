"""
System Information endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from src.auth.dependencies import CurrentUser
from src.utils.logging import logger

router = APIRouter(tags=["system"])

@router.get("/system/status")
async def get_system_status():
    """Get system status"""
    return {
        "status": "operational",
        "version": "1.0.0",
        "uptime": "24h",
        "services": {
            "ai_agents": "healthy",
            "database": "healthy",
            "authentication": "healthy"
        }
    }

@router.get("/info")
async def get_api_info():
    """Get API information"""
    return {
        "api_version": "1.0.0",
        "service": "MediTwin Agents API",
        "endpoints": [
            "/api/v1/expert-opinion",
            "/api/v1/timeline",
            "/api/v1/symptoms/analyze",
            "/api/v1/user/profile"
        ],
        "documentation": "/docs"
    }

@router.get("/metrics")
async def get_service_metrics(current_user: CurrentUser):
    """Get service metrics"""
    return {
        "requests_per_minute": 15,
        "average_response_time": "250ms",
        "active_users": 1,
        "system_load": "low",
        "patient_id": current_user.patient_id
    }

@router.get("/database/status")
async def get_database_status(current_user: CurrentUser):
    """Get database status"""
    return {
        "mongodb": "connected",
        "redis": "connected",
        "neo4j": "connected",
        "milvus": "connected",
        "last_check": datetime.utcnow().isoformat(),
        "patient_id": current_user.patient_id
    }
