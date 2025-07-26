"""
Expert Opinion endpoints for multi-specialist medical consultations.
"""

import json
import uuid
from datetime import datetime
from typing import AsyncGenerator, Dict, Any, Optional, List

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.utils.logging import logger, log_user_action
from src.agents.orchestrator_agent import get_orchestrator
from src.agents.crew_agents.expert_crew import ExpertConsultationCrew
from src.chat.short_term import get_short_term_memory
from src.chat.long_term import get_long_term_memory
from src.db.redis_db import get_redis
from src.db.mongo_db import get_mongo
from src.db.neo4j_db import get_graph
from src.db.milvus_db import get_milvus
from src.auth.dependencies import CurrentUser

router = APIRouter(tags=["expert_opinion"])


class ExpertOpinionRequest(BaseModel):
    """Model for expert opinion requests."""
    message: str = Field(..., min_length=1, max_length=5000, description="Medical question or case description")
    specialties: Optional[List[str]] = Field(None, description="Specific specialties to consult (optional)")
    include_context: bool = Field(True, description="Whether to include user's medical history")
    priority: str = Field("normal", description="Consultation priority (low, normal, high, urgent)")


class ExpertOpinionResponse(BaseModel):
    """Model for expert opinion responses."""
    conversation_id: str = Field(description="Conversation identifier")
    specialist_opinions: List[Dict[str, Any]] = Field(description="Individual specialist opinions")
    aggregated_response: str = Field(description="Aggregated expert response")
    consulted_specialties: List[str] = Field(description="Specialties consulted")
    confidence_score: float = Field(description="Overall confidence score")


@router.post("/consultation", response_class=StreamingResponse)
async def get_expert_consultation(
    request: ExpertOpinionRequest,
    current_user: CurrentUser,
    conversation_id: Optional[str] = Query(None, description="Existing conversation ID")
):
    """
    Get expert medical consultation from multiple specialists.
    
    Features:
    - Multi-specialist crew collaboration
    - Streaming responses
    - Patient context integration
    - Knowledge graph and document search
    - Aggregated expert opinions
    """
    try:
        patient_id = current_user.patient_id
        conv_id = conversation_id or f"expert_{patient_id}_{int(datetime.utcnow().timestamp())}"
        
        # Validate priority
        if request.priority not in ["low", "normal", "high", "urgent"]:
            raise HTTPException(status_code=400, detail="Invalid priority level")
        
        # Gather comprehensive patient context
        context = await gather_expert_context(patient_id, request.message, conv_id)
        
        # Initialize expert crew
        crew = ExpertConsultationCrew()
        
        # Process consultation with streaming
        async def generate_expert_response():
            try:
                # Send initial response
                yield f"data: {json.dumps({'type': 'start', 'conversation_id': conv_id})}\n\n"
                
                # Process with expert crew
                result = await crew.process_consultation(
                    patient_id=patient_id,
                    conversation_id=conv_id,
                    message=request.message,
                    specialties=request.specialties,
                    context=context,
                    priority=request.priority
                )
                
                # Stream individual specialist opinions
                for specialist_opinion in result.get("specialist_opinions", []):
                    yield f"data: {json.dumps({'type': 'specialist_opinion', 'data': specialist_opinion})}\n\n"
                
                # Stream aggregated response
                aggregated = result.get("aggregated_response", "")
                chunk_size = 50
                for i in range(0, len(aggregated), chunk_size):
                    chunk = aggregated[i:i + chunk_size]
                    yield f"data: {json.dumps({'type': 'aggregated_chunk', 'content': chunk})}\n\n"
                
                # Send completion with summary
                yield f"data: {json.dumps({'type': 'complete', 'conversation_id': conv_id, 'summary': result.get('summary', {})})}\n\n"
                
                # Store consultation in memory
                await store_expert_consultation(patient_id, conv_id, request.message, result, context)
                
            except Exception as e:
                logger.error(f"Expert consultation streaming error: {e}")
                error_msg = f"data: {json.dumps({'type': 'error', 'message': 'An error occurred during expert consultation.'})}\n\n"
                yield error_msg
        
        return StreamingResponse(
            generate_expert_response(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except Exception as e:
        logger.error(f"Expert consultation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to process expert consultation")


@router.get("/specialties")
async def get_available_specialties():
    """
    Get list of available medical specialties for consultation.
    """
    try:
        specialties = [
            "cardiology",
            "endocrinology",
            "neurology",
            "orthopedics",
            "dermatology",
            "gastroenterology",
            "pulmonology",
            "nephrology",
            "rheumatology",
            "oncology",
            "psychiatry",
            "pediatrics",
            "geriatrics",
            "emergency_medicine",
            "general_medicine"
        ]
        
        return {
            "specialties": specialties,
            "total_count": len(specialties),
            "description": "Available medical specialties for expert consultation"
        }
        
    except Exception as e:
        logger.error(f"Failed to get specialties: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve specialties")


@router.get("/consultation/{conversation_id}")
async def get_consultation_history(
    conversation_id: str,
    current_user: CurrentUser
):
    """
    Get history of a specific expert consultation.
    """
    try:
        patient_id = current_user.patient_id
        
        # Get consultation from memory
        redis_client = get_redis()
        consultation = redis_client.get_expert_consultation(patient_id, conversation_id)
        
        if not consultation:
            raise HTTPException(status_code=404, detail="Consultation not found")
        
        return {
            "conversation_id": conversation_id,
            "consultation": consultation,
            "patient_id": patient_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get consultation history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve consultation history")


async def gather_expert_context(patient_id: str, message: str, conversation_id: str) -> Dict[str, Any]:
    """Gather comprehensive context for expert consultation."""
    context = {
        "patient_id": patient_id,
        "conversation_id": conversation_id,
        "timestamp": datetime.utcnow().isoformat(),
        "short_term_memory": [],
        "long_term_memory": [],
        "medical_records": [],
        "similar_documents": [],
        "knowledge_graph": [],
        "medical_entities": [],
        "body_parts_affected": [],
        "timeline_events": []
    }
    
    try:
        # 1. Get conversation history
        short_term = get_short_term_memory()
        context["short_term_memory"] = short_term.get_session_history(patient_id, conversation_id, limit=20)
        
        # 2. Get long-term medical history
        long_term = get_long_term_memory()
        context["long_term_memory"] = long_term.get_relevant_history(patient_id, message, limit=10)
        
        # 3. Get medical records from documents
        try:
            mongo_client = await get_mongo()
            medical_records = await mongo_client.get_medical_records(patient_id, limit=50)
            context["medical_records"] = medical_records
        except Exception as e:
            logger.warning(f"Medical records retrieval failed: {e}")
        
        # 4. Similarity search in documents
        try:
            milvus_client = get_milvus()
            similar_docs = await milvus_client.search_similar_documents(patient_id, message, limit=5)
            context["similar_documents"] = similar_docs
        except Exception as e:
            logger.warning(f"Similarity search failed: {e}")
        
        # 5. Knowledge graph search
        try:
            neo4j_client = get_graph()
            knowledge_results = neo4j_client.search_medical_knowledge(patient_id, message, limit=10)
            context["knowledge_graph"] = knowledge_results
        except Exception as e:
            logger.warning(f"Knowledge graph search failed: {e}")
        
        # 6. Extract medical entities
        try:
            from src.agents.medical_entity_extractor import extract_entities
            entities = extract_entities(message)
            context["medical_entities"] = entities
        except Exception as e:
            logger.warning(f"Entity extraction failed: {e}")
        
        # 7. Get body parts affected
        try:
            body_parts = neo4j_client.get_body_parts_for_query(patient_id, message)
            context["body_parts_affected"] = body_parts
        except Exception as e:
            logger.warning(f"Body parts analysis failed: {e}")
        
        # 8. Get timeline events
        try:
            timeline_events = neo4j_client.get_timeline_events(patient_id, message, limit=20)
            context["timeline_events"] = timeline_events
        except Exception as e:
            logger.warning(f"Timeline retrieval failed: {e}")
        
    except Exception as e:
        logger.error(f"Expert context gathering failed: {e}")
    
    return context


async def store_expert_consultation(patient_id: str, conversation_id: str, user_message: str, result: Dict[str, Any], context: Dict[str, Any]):
    """Store expert consultation in memory systems."""
    try:
        # Store in Redis
        redis_client = get_redis()
        consultation_data = {
            "conversation_id": conversation_id,
            "patient_id": patient_id,
            "user_message": user_message,
            "specialist_opinions": result.get("specialist_opinions", []),
            "aggregated_response": result.get("aggregated_response", ""),
            "consulted_specialties": result.get("consulted_specialties", []),
            "confidence_score": result.get("confidence_score", 0.0),
            "timestamp": datetime.utcnow().isoformat(),
            "context_used": context
        }
        
        redis_client.store_expert_consultation(patient_id, conversation_id, consultation_data)
        
        # Store in MongoDB for persistence
        mongo_client = await get_mongo()
        await mongo_client.store_medical_record(
            patient_id,
            {
                "conversation_id": conversation_id,
                "type": "expert_consultation",
                "user_message": user_message,
                "specialist_opinions": result.get("specialist_opinions", []),
                "aggregated_response": result.get("aggregated_response", ""),
                "consulted_specialties": result.get("consulted_specialties", []),
                "confidence_score": result.get("confidence_score", 0.0),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to store expert consultation: {e}")


@router.get("/health")
async def get_expert_opinion_health():
    """Health check for expert opinion service."""
    return {
        "status": "healthy",
        "service": "expert_opinion",
        "version": "1.0.0",
        "features": [
            "Multi-specialist consultation",
            "Streaming responses",
            "Crew collaboration",
            "Patient context integration",
            "Knowledge graph search",
            "Document similarity search",
            "Medical entity extraction",
            "Aggregated expert opinions"
        ]
    }
