"""
Tools API endpoints for CrewAI agent integration.

This module provides tool definitions and endpoints that CrewAI agents can register
and use for accessing medical data and performing operations.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from src.auth.dependencies import CurrentUser
from src.db.neo4j_db import get_graph
from src.db.mongo_db import get_mongo
from src.db.milvus_db import get_milvus
from src.utils.logging import logger

router = APIRouter(prefix="/tools", tags=["tools"])


class ToolDefinition(BaseModel):
    """Tool definition for CrewAI agent registration."""
    name: str
    description: str
    parameters: Dict[str, Any]
    required: List[str]


@router.get("/", response_model=List[ToolDefinition])
async def get_available_tools():
    """
    Get list of available tools for CrewAI agent registration.
    
    Returns:
        List of tool definitions that agents can use
    """
    tools = [
        ToolDefinition(
            name="get_timeline",
            description="Get chronological timeline of medical events for a user",
            parameters={
                "type": "object",
                "properties": {
                    "userId": {
                        "type": "string",
                        "description": "User identifier"
                    },
                    "bodyPart": {
                        "type": "string",
                        "description": "Optional body part to filter events (e.g., 'Heart', 'Left Knee')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of events to retrieve",
                        "default": 10
                    }
                }
            },
            required=["userId"]
        ),
        ToolDefinition(
            name="get_body_part_status",
            description="Get current severity status for all or specific body parts",
            parameters={
                "type": "object",
                "properties": {
                    "userId": {
                        "type": "string",
                        "description": "User identifier"
                    },
                    "bodyPart": {
                        "type": "string",
                        "description": "Optional specific body part to check"
                    }
                }
            },
            required=["userId"]
        ),
        ToolDefinition(
            name="search_medical_records",
            description="Search user's medical records using semantic similarity",
            parameters={
                "type": "object",
                "properties": {
                    "userId": {
                        "type": "string",
                        "description": "User identifier"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query for medical records"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 5
                    }
                }
            },
            required=["userId", "query"]
        ),
        ToolDefinition(
            name="get_medical_history",
            description="Get user's medical history and profile information",
            parameters={
                "type": "object",
                "properties": {
                    "userId": {
                        "type": "string",
                        "description": "User identifier"
                    },
                    "includeProfile": {
                        "type": "boolean",
                        "description": "Whether to include user profile (lifestyle factors)",
                        "default": True
                    }
                }
            },
            required=["userId"]
        )
    ]
    
    return tools


@router.post("/get_timeline")
async def tool_get_timeline(
    userId: str,
    bodyPart: Optional[str] = None,
    limit: int = 10
):
    """
    Tool implementation: Get timeline of medical events.
    Used by CrewAI agents to access patient timeline data.
    """
    try:
        neo4j_client = get_graph()
        
        if bodyPart:
            # Get events for specific body part
            events = neo4j_client.get_body_part_history(userId, bodyPart, limit=limit)
        else:
            # Get general patient timeline
            events = neo4j_client.get_patient_timeline(userId, limit=limit)
        
        return {
            "success": True,
            "userId": userId,
            "bodyPart": bodyPart,
            "events": events,
            "total": len(events)
        }
        
    except Exception as e:
        logger.error(f"get_timeline tool failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "events": []
        }


@router.post("/get_body_part_status")
async def tool_get_body_part_status(
    userId: str,
    bodyPart: Optional[str] = None
):
    """
    Tool implementation: Get body part severity status.
    Used by CrewAI agents to check current health status.
    """
    try:
        neo4j_client = get_graph()
        
        # Ensure user is initialized
        neo4j_client.ensure_user_initialized(userId)
        
        if bodyPart:
            # Get specific body part details
            severities = neo4j_client.get_body_part_severities(userId)
            severity = severities.get(bodyPart, "NA")
            
            return {
                "success": True,
                "userId": userId,
                "bodyPart": bodyPart,
                "severity": severity,
                "status": {bodyPart: severity}
            }
        else:
            # Get all body part severities
            severities = neo4j_client.get_body_part_severities(userId)
            
            # Filter to only active conditions
            active_conditions = {
                bp: severity for bp, severity in severities.items()
                if severity and severity.lower() not in ['na', 'normal']
            }
            
            return {
                "success": True,
                "userId": userId,
                "active_conditions": active_conditions,
                "all_severities": severities
            }
        
    except Exception as e:
        logger.error(f"get_body_part_status tool failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "status": {}
        }


@router.post("/search_medical_records")
async def tool_search_medical_records(
    userId: str,
    query: str,
    limit: int = 5
):
    """
    Tool implementation: Search medical records using vector similarity.
    Used by CrewAI agents to find relevant medical information.
    """
    try:
        # Search vector database for similar content
        milvus_db = get_milvus()
        results = milvus_db.search_similar_documents(
            user_id=userId,
            query_text=query,
            limit=limit,
            score_threshold=0.6
        )
        
        # Also search MongoDB for recent records
        mongo_client = await get_mongo()
        recent_records = await mongo_client.get_medical_records(
            userId, 
            limit=limit
        )
        
        return {
            "success": True,
            "userId": userId,
            "query": query,
            "vector_results": results,
            "recent_records": recent_records[:limit],
            "total_found": len(results) + len(recent_records)
        }
        
    except Exception as e:
        logger.error(f"search_medical_records tool failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "vector_results": [],
            "recent_records": []
        }


@router.post("/get_medical_history")
async def tool_get_medical_history(
    userId: str,
    includeProfile: bool = True
):
    """
    Tool implementation: Get user's medical history and profile.
    Used by CrewAI agents to access long-term patient information.
    """
    try:
        from src.chat.long_term import LongTermMemory
        
        ltm = LongTermMemory()
        context = await ltm.get_user_context(userId)
        
        result = {
            "success": True,
            "userId": userId,
            "medical_history": context.get("medical_history", []),
            "preferences": context.get("preferences", {})
        }
        
        if includeProfile:
            result["profile"] = context.get("user_profile", {})
        
        return result
        
    except Exception as e:
        logger.error(f"get_medical_history tool failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "medical_history": [],
            "preferences": {},
            "profile": {}
        }
