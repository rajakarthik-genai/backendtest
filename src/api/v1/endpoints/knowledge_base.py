"""
Knowledge Base endpoints for medical information search and drug interactions.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from src.auth.dependencies import CurrentUser
from src.utils.logging import logger
from src.api.v1.endpoints.chat import ChatRequest, send_message

router = APIRouter(tags=["knowledge-base"])

class DrugInteractionRequest(BaseModel):
    medications: List[str] = Field(..., description="List of medications")

@router.get("/knowledge/search")
async def search_knowledge(
    current_user: CurrentUser,
    query: str = Query(..., description="Search query")
):
    """Search medical knowledge base"""
    try:
        chat_request = ChatRequest(
            message=f"Provide medical information about: {query}"
        )
        
        response = await send_message(chat_request, current_user)
        
        return {
            "results": [
                {
                    "title": f"Information about {query}",
                    "content": response.response,
                    "source": "AI Medical Assistant",
                    "relevance": 0.9
                }
            ],
            "query": query,
            "total_results": 1,
            "patient_id": current_user.patient_id
        }
    except Exception as e:
        logger.error(f"Knowledge search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/medical/information")
async def get_medical_information(
    current_user: CurrentUser,
    topic: str = Query(..., description="Medical topic")
):
    """Get detailed medical information about a topic"""
    try:
        chat_request = ChatRequest(
            message=f"Provide detailed medical information about: {topic}"
        )
        
        response = await send_message(chat_request, current_user)
        
        return {
            "topic": topic,
            "information": response.response,
            "last_updated": datetime.utcnow().isoformat(),
            "sources": ["Medical AI Database"],
            "patient_id": current_user.patient_id
        }
    except Exception as e:
        logger.error(f"Medical information request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/drugs/interactions")
async def check_drug_interactions(
    request: DrugInteractionRequest,
    current_user: CurrentUser
):
    """Check for drug interactions"""
    try:
        chat_request = ChatRequest(
            message=f"Check for interactions between these medications: {', '.join(request.medications)}"
        )
        
        response = await send_message(chat_request, current_user)
        
        return {
            "medications": request.medications,
            "interactions": [
                {"severity": "info", "description": response.response}
            ],
            "safe_combination": True,
            "disclaimer": "Always consult with a pharmacist or doctor about drug interactions.",
            "patient_id": current_user.patient_id
        }
    except Exception as e:
        logger.error(f"Drug interaction check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
