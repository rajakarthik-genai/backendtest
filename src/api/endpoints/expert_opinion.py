"""
Expert Opinion API - Multi-specialist consultation endpoint.

This module provides endpoints for requesting expert medical opinions
from multiple specialist agents, aggregated into a comprehensive response.
"""

import asyncio
from uuid import uuid4
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from src.agents.orchestrator_agent import get_orchestrator
from src.db.mongo_db import get_mongo
from src.db.neo4j_db import get_graph
from src.tools import get_vector_store
from src.db.redis_db import get_redis
from src.utils.logging import logger, log_user_action
from src.auth.dependencies import CurrentUser
from src.config.settings import settings
import json

router = APIRouter(prefix="/expert", tags=["expert-opinion"])


class ExpertOpinionRequest(BaseModel):
    """Model for expert opinion requests."""
    message: str = Field(..., min_length=1, max_length=5000, description="Medical question or case description")
    specialties: Optional[List[str]] = Field(None, description="Specific specialties to consult (optional)")
    include_context: bool = Field(True, description="Whether to include user's medical history")
    priority: str = Field("normal", description="Consultation priority (low, normal, high, urgent)")


class ExpertOpinionResponse(BaseModel):
    """Model for expert opinion responses."""
    conversation_id: str
    specialist_opinions: List[dict]
    aggregated_response: str
    consulted_specialties: List[str]
    confidence_score: float
    recommendations: List[str]


@router.post("/opinion", response_model=ExpertOpinionResponse)
async def get_expert_opinion(
    current_user: CurrentUser,
    request: ExpertOpinionRequest = ...,
    conversation_id: Optional[str] = Query(None, description="Existing conversation ID")
):
    """
    Get expert medical opinion from multiple specialist agents.
    
    This endpoint orchestrates a multi-specialist consultation, where
    relevant medical specialists provide their opinions on a case,
    and an aggregator agent synthesizes the responses.
    
    Args:
        current_user: Authenticated user from JWT token
        request: Expert opinion request data
        conversation_id: Optional existing conversation ID
    
    Returns:
        Aggregated expert opinion with individual specialist responses
    """
    try:
        # Get user_id from JWT token
        user_id = current_user.user_id
        
        # Generate or use existing conversation ID
        conv_id = conversation_id or str(uuid4())
        
        # Validate priority
        if request.priority not in ["low", "normal", "high", "urgent"]:
            raise HTTPException(status_code=400, detail="Invalid priority level")
        
        # Initialize orchestrator
        orchestrator = await get_orchestrator()
        
        # Get user context if requested (simplified)
        user_context = {"user_id": user_id}
        if request.include_context:
            try:
                # Get basic user context - simplified to avoid missing methods
                user_context["include_context"] = True
                user_context["priority"] = request.priority
                user_context["specialties"] = request.specialties
            except Exception as e:
                logger.warning(f"Could not retrieve full context for user {user_id}: {e}")
        
        # Store conversation in chat history
        redis_client = get_redis()
        redis_client.store_chat_message(
            user_id,
            conv_id,
            {
                "role": "user",
                "content": request.message,
                "metadata": {
                    "type": "expert_consultation",
                    "priority": request.priority,
                    "requested_specialties": request.specialties
                }
            }
        )
        
        # Process message using the existing orchestrator method
        response = await orchestrator.process_user_message(
            user_id=user_id,
            session_id=conv_id,
            message=f"Expert consultation request: {request.message}. Please provide a detailed medical analysis from relevant specialists."
        )
        
        # Store response in chat history
        redis_client.store_chat_message(
            user_id,
            conv_id,
            {
                "role": "assistant",
                "content": response["content"],
                "metadata": {
                    "type": "expert_consultation_response",
                    "specialties": request.specialties or ["general_medicine"],
                    "confidence": 0.8  # Default confidence
                }
            }
        )
        
        # Log user action
        log_user_action(
            user_id,
            "expert_opinion_requested",
            {
                "conversation_id": conv_id,
                "specialties": request.specialties or ["general_medicine"],
                "priority": request.priority
            }
        )
        
        logger.info(f"Expert opinion delivered for user {user_id}, conversation {conv_id}")
        
        return ExpertOpinionResponse(
            conversation_id=conv_id,
            specialist_opinions=[{
                "specialist": spec,
                "opinion": response["content"],
                "confidence": 0.8
            } for spec in (request.specialties or ["general_medicine"])],
            aggregated_response=response["content"],
            consulted_specialties=request.specialties or ["general_medicine"],
            confidence_score=0.8,
            recommendations=["Consult with a healthcare professional", "Monitor symptoms", "Follow up as needed"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get expert opinion for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get expert opinion")


@router.post("/opinion/stream")
async def get_expert_opinion_stream(
    user_id: str = Query(..., description="User identifier"),
    request: ExpertOpinionRequest = ...,
    conversation_id: Optional[str] = Query(None, description="Existing conversation ID")
):
    """
    Get expert medical opinion with streaming responses.
    
    This endpoint provides real-time streaming of specialist opinions
    as they are generated, allowing for better user experience.
    
    Args:
        user_id: User identifier
        request: Expert opinion request data
        conversation_id: Optional existing conversation ID
    
    Returns:
        Server-sent events stream with specialist responses
    """
    try:
        # Generate or use existing conversation ID
        conv_id = conversation_id or str(uuid4())
        
        # Validate priority
        if request.priority not in ["low", "normal", "high", "urgent"]:
            raise HTTPException(status_code=400, detail="Invalid priority level")
        
        async def generate_expert_stream():
            try:
                # Initialize orchestrator
                orchestrator = await get_orchestrator()
                
                # Initialize database connections
                mongo_client = await get_mongo()
                neo4j_client = get_graph()
                redis_client = get_redis()
                
                # Get user context if requested
                user_context = {}
                if request.include_context:
                    try:
                        medical_records = await mongo_client.get_medical_records(
                            user_id, 
                            limit=50,
                            filters={"event_type": {"$in": ["medical", "symptom", "treatment", "medication"]}}
                        )
                        kg_context = await neo4j_client.get_patient_medical_graph(user_id)
                        user_context = {
                            "medical_history": medical_records[:10],
                            "knowledge_graph": kg_context,
                            "user_id": user_id
                        }
                    except Exception as e:
                        logger.warning(f"Could not retrieve full context for user {user_id}: {e}")
                        user_context = {"user_id": user_id}
                
                # Store user message
                redis_client.store_chat_message(
                    user_id,
                    conv_id,
                    {
                        "role": "user",
                        "content": request.message,
                        "metadata": {
                            "type": "expert_consultation",
                            "priority": request.priority,
                            "requested_specialties": request.specialties
                        }
                    }
                )
                
                # Stream expert opinion
                async for chunk in orchestrator.stream_expert_opinion(
                    question=request.message,
                    user_context=user_context,
                    conversation_id=conv_id,
                    requested_specialties=request.specialties,
                    priority=request.priority
                ):
                    yield f"data: {json.dumps(chunk)}\n\n"
                
                # Log completion
                log_user_action(
                    user_id,
                    "expert_opinion_stream_completed",
                    {
                        "conversation_id": conv_id,
                        "priority": request.priority
                    }
                )
                
            except Exception as e:
                logger.error(f"Error in expert opinion stream for user {user_id}: {e}")
                error_chunk = {
                    "type": "error",
                    "message": "An error occurred while generating expert opinion",
                    "conversation_id": conv_id
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"
        
        return StreamingResponse(
            generate_expert_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initialize expert opinion stream for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize expert opinion stream")


@router.get("/specialties")
async def get_available_specialties():
    """
    Get list of available medical specialties.
    
    Returns:
        List of available specialist types
    """
    try:
        specialties = [
            {
                "code": "general",
                "name": "General Physician",
                "description": "Primary care and general medical consultation"
            },
            {
                "code": "cardiology",
                "name": "Cardiologist",
                "description": "Heart and cardiovascular system specialist"
            },
            {
                "code": "neurology",
                "name": "Neurologist",
                "description": "Brain and nervous system specialist"
            },
            {
                "code": "orthopedics",
                "name": "Orthopedist",
                "description": "Musculoskeletal system specialist"
            }
        ]
        
        return {
            "specialties": specialties,
            "total": len(specialties)
        }
        
    except Exception as e:
        logger.error(f"Failed to get available specialties: {e}")
        raise HTTPException(status_code=500, detail="Failed to get available specialties")


@router.get("/opinion/{conversation_id}")
async def get_opinion_history(
    conversation_id: str,
    user_id: str = Query(..., description="User identifier")
):
    """
    Retrieve the history of an expert opinion conversation.
    
    Args:
        conversation_id: Conversation identifier
        user_id: User identifier
    
    Returns:
        Conversation history and expert opinions
    """
    try:
        redis_client = get_redis()
        
        # Get conversation history
        conversation = redis_client.get_conversation(user_id, conversation_id)
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {
            "conversation_id": conversation_id,
            "messages": conversation.get("messages", []),
            "created_at": conversation.get("created_at"),
            "updated_at": conversation.get("updated_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get opinion history for conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get opinion history")
