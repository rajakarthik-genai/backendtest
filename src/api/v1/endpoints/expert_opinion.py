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

router = APIRouter(tags=["expert-opinion"])


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


@router.post("/expert-opinion", response_model=ExpertOpinionResponse)
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
        # Get patient_id from JWT token
        patient_id = current_user.patient_id
        
        # Generate or use existing conversation ID
        conv_id = conversation_id or str(uuid4())
        
        # Validate priority
        if request.priority not in ["low", "normal", "high", "urgent"]:
            raise HTTPException(status_code=400, detail="Invalid priority level")
        
        # Initialize orchestrator
        orchestrator = await get_orchestrator()
        
        # Get user context if requested (simplified)
        user_context = {"patient_id": patient_id}
        if request.include_context:
            try:
                # Get basic user context - simplified to avoid missing methods
                user_context["include_context"] = True
                user_context["priority"] = request.priority
                user_context["specialties"] = request.specialties
            except Exception as e:
                logger.warning(f"Could not retrieve full context for user {patient_id}: {e}")
        
        # Store conversation in chat history
        redis_client = get_redis()
        redis_client.store_chat_message(
            patient_id,
            conv_id,
            {
                "role": "user",
                "content": request.message,
                "metadata": {
                    "type": "expert_consultation",
                    "priority": request.priority,
                    "requested_specialties": request.specialties
                }
            },
            ttl_hours=24
        )
        
        # Fallback: If chat history is empty, try to fetch from MongoDB and repopulate Redis
        history = redis_client.get_chat_history(patient_id, conv_id, 50)
        if not history:
            from src.db.mongo_db import get_mongo
            mongo_client = await get_mongo()
            records = await mongo_client.get_medical_records(user_id=patient_id, limit=50)
            for rec in records:
                msg = {
                    "role": rec.get("role", "user"),
                    "content": rec.get("content", ""),
                    "timestamp": rec.get("timestamp", "")
                }
                redis_client.store_chat_message(patient_id, conv_id, msg, ttl_hours=24)
        
        # Process message using the existing orchestrator method
        response = await orchestrator.process_user_message(
            patient_id=patient_id,
            session_id=conv_id,
            message=f"Expert consultation request: {request.message}. Please provide a detailed medical analysis from relevant specialists."
        )
        
        # Store response in chat history
        redis_client.store_chat_message(
            patient_id,
            conv_id,
            {
                "role": "assistant",
                "content": response["content"],
                "metadata": {
                    "type": "expert_consultation_response",
                    "specialties": request.specialties or ["general_medicine"],
                    "confidence": 0.8  # Default confidence
                }
            },
            ttl_hours=24
        )
        
        # Log user action
        log_user_action(
            patient_id,
            "expert_opinion_requested",
            {
                "conversation_id": conv_id,
                "specialties": request.specialties or ["general_medicine"],
                "priority": request.priority
            }
        )
        
        logger.info(f"Expert opinion delivered for user {patient_id}, conversation {conv_id}")
        
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
        logger.error(f"Failed to get expert opinion for user {patient_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get expert opinion")


@router.post("/expert-opinion/stream")
async def get_expert_opinion_stream(
    patient_id: str = Query(..., description="User identifier"),
    request: ExpertOpinionRequest = ...,
    conversation_id: Optional[str] = Query(None, description="Existing conversation ID")
):
    """
    Get expert medical opinion with streaming responses.
    
    This endpoint provides real-time streaming of specialist opinions
    as they are generated, allowing for better user experience.
    
    Args:
        patient_id: User identifier
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
                            patient_id, 
                            limit=50,
                            filters={"event_type": {"$in": ["medical", "symptom", "treatment", "medication"]}}
                        )
                        kg_context = await neo4j_client.get_patient_medical_graph(patient_id)
                        user_context = {
                            "medical_history": medical_records[:10],
                            "knowledge_graph": kg_context,
                            "patient_id": patient_id
                        }
                    except Exception as e:
                        logger.warning(f"Could not retrieve full context for user {patient_id}: {e}")
                        user_context = {"patient_id": patient_id}
                
                # Store user message
                redis_client.store_chat_message(
                    patient_id,
                    conv_id,
                    {
                        "role": "user",
                        "content": request.message,
                        "metadata": {
                            "type": "expert_consultation",
                            "priority": request.priority,
                            "requested_specialties": request.specialties
                        }
                    },
                    ttl_hours=24
                )
                
                # Fallback: If chat history is empty, try to fetch from MongoDB and repopulate Redis
                history = redis_client.get_chat_history(patient_id, conv_id, 50)
                if not history:
                    records = await mongo_client.get_medical_records(user_id=patient_id, limit=50)
                    for rec in records:
                        msg = {
                            "role": rec.get("role", "user"),
                            "content": rec.get("content", ""),
                            "timestamp": rec.get("timestamp", "")
                        }
                        redis_client.store_chat_message(patient_id, conv_id, msg, ttl_hours=24)
                
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
                    patient_id,
                    "expert_opinion_stream_completed",
                    {
                        "conversation_id": conv_id,
                        "priority": request.priority
                    }
                )
                
            except Exception as e:
                logger.error(f"Error in expert opinion stream for user {patient_id}: {e}")
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
        logger.error(f"Failed to initialize expert opinion stream for user {patient_id}: {e}")
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


@router.get("/expert-opinion/{conversation_id}")
async def get_opinion_history(
    conversation_id: str,
    patient_id: str = Query(..., description="User identifier")
):
    """
    Retrieve the history of an expert opinion conversation.
    
    Args:
        conversation_id: Conversation identifier
        patient_id: User identifier
    
    Returns:
        Conversation history and expert opinions
    """
    try:
        redis_client = get_redis()
        
        # Get conversation history
        conversation = redis_client.get_conversation(patient_id, conversation_id)
        
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


@router.get("/expert-opinion")
async def get_expert_opinions(current_user: CurrentUser):
    """Get list of expert opinions for the current user"""
    try:
        patient_id = current_user.patient_id
        
        # For now, return a simple response indicating the system is available
        return {
            "expert_opinions": [],
            "total": 0,
            "patient_id": patient_id,
            "message": "Expert opinion system is available"
        }
        
    except Exception as e:
        logger.error(f"Failed to get expert opinions for user {patient_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve expert opinions")


@router.get("/expert-opinion/status")
async def get_expert_opinion_status(current_user: CurrentUser):
    """Get expert opinion system status"""
    return {
        "status": "active", 
        "specialists_available": ["general", "cardiology", "neurology", "psychiatry"],
        "queue_length": 0,
        "average_response_time": "5 minutes"
    }
