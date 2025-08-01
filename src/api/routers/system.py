"""
System Information API endpoints for service status and metrics.

Provides system information including:
- Service status and health
- Available endpoints
- System metrics  
- API documentation links
"""

from fastapi import APIRouter, Depends, Request
from typing import Dict, List, Any
from datetime import datetime
import logging

from src.core.limiter import limiter
from src.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/status")
@limiter.limit("100/minute")
async def get_system_status(request: Request):
    """Get overall system status and information"""
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "docs": "/api/docs" if not settings.PRODUCTION else None,
            "health": "/health",
            "metrics": "/metrics"
        }
    }

@router.get("/metrics")
@limiter.limit("100/minute") 
async def get_system_metrics(request: Request):
    """Get basic system metrics and information"""
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "uptime": "unknown",  # Could be enhanced with actual uptime tracking
        "requests_total": "unknown",  # Could be enhanced with metrics
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/endpoints")
@limiter.limit("100/minute")
async def list_available_endpoints(request: Request):
    """List all available API endpoints with correct methods"""
    endpoints = {
        "authentication": [
            "POST /api/v1/auth/login",
            "POST /api/v1/auth/refresh"
        ],
        "documents": [
            "POST /api/v1/documents/upload",
            "GET /api/v1/documents/status",
            "GET /api/v1/documents/document/{document_id}",
            "POST /api/v1/documents/reprocess/{document_id}",
            "DELETE /api/v1/documents/delete/{document_id}"
        ],
        "chat": [
            "POST /api/v1/chat/stream",
            "POST /api/v1/chat/message", 
            "GET /api/v1/chat/history"
        ],
        "expert_opinion": [
            "POST /api/v1/expert-opinion/",
            "POST /api/v1/expert-opinion/quick"
        ],
        "health": [
            "GET /api/v1/health/body-parts",
            "GET /api/v1/health/summary",
            "GET /api/v1/health/3d-visualization",
            "GET /api/v1/health/body-part/{body_part}"
        ],
        "timeline": [
            "POST /api/v1/timeline/",  # For creating timeline queries
            "GET /api/v1/timeline/patient",
            "GET /api/v1/timeline/summary"
        ],
        "reports": [
            "POST /api/v1/reports/generate",
            "GET /api/v1/reports/status/{report_id}",
            "GET /api/v1/reports/download/{report_id}",
            "GET /api/v1/reports/list"
        ],
        "visualization": [
            "GET /api/v1/visualization/data"
        ],
        "system": [
            "GET /api/v1/system/status",
            "GET /api/v1/system/metrics",
            "GET /api/v1/system/endpoints"
        ],
        "admin": [
            "GET /api/v1/admin/health",
            "GET /api/v1/admin/database-status"
        ],
        "user": [
            "GET /api/v1/user/profile",
            "PUT /api/v1/user/profile",  # Correct method for updates
            "GET /api/v1/user/preferences",
            "PUT /api/v1/user/preferences",
            "GET /api/v1/user/settings"
        ],
        "symptoms": [
            "POST /api/v1/symptoms/analyze",
            "POST /api/v1/symptoms/diagnostic/suggestions",
            "POST /api/v1/symptoms/treatment/recommendations",
            "GET /api/v1/symptoms/health/insights"
        ],
        "events": [
            "POST /api/v1/events/",  # Create event
            "GET /api/v1/events/",   # List events
            "GET /api/v1/events/{event_id}",
            "PUT /api/v1/events/{event_id}",
            "DELETE /api/v1/events/{event_id}"
        ],
        "anatomy": [
            "GET /api/v1/anatomy/body-parts/severities",
            "GET /api/v1/anatomy/body-part/{body_part}/details",
            "GET /api/v1/anatomy/severity-trends/{body_part}"
        ]
    }
    
    return {
        "endpoints": endpoints,
        "total_endpoints": sum(len(v) for v in endpoints.values()),
        "note": "Ensure clients use the correct HTTP methods as specified",
        "timestamp": datetime.utcnow().isoformat()
    }
