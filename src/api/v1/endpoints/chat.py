"""
Chat endpoints for personalized medical conversations with streaming responses.
"""

import json
import uuid
from datetime import datetime
from typing import AsyncGenerator, Dict, Any, Optional

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel, Field

from src.utils.logging import logger, log_user_action
from src.agents.orchestrator_agent import get_orchestrator
from src.chat.short_term import get_short_term_memory
from src.chat.long_term import get_long_term_memory
from src.db.redis_db import get_redis
from src.db.mongo_db import get_mongo
from src.db.neo4j_db import get_graph
from src.db.milvus_db import get_milvus
from src.auth.dependencies import CurrentUser

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    """Model for chat requests."""
    message: str = Field(..., min_length=1, max_length=5000, description="User message")
    session_id: Optional[str] = Field(None, description="Chat session ID")


class ChatResponse(BaseModel):
    """Model for chat responses."""
    session_id: str = Field(description="Chat session ID")
    message: str = Field(description="AI response")
    timestamp: str = Field(description="Response timestamp")
    context_used: Dict[str, Any] = Field(description="Context information used")


@router.post("/message", response_class=StreamingResponse)
async def chat_message(
    request: ChatRequest,
    current_user: CurrentUser
):
    """
    Send a message and get a personalized streaming response.
    
    Uses:
    - Short-term memory (current session)
    - Long-term memory (historical conversations)
    - Similarity search (document content)
    - Neo4j relationship search (medical knowledge graph)
    - Patient-specific context
    """
    try:
        patient_id = current_user.patient_id
        session_id = request.session_id or f"session_{patient_id}_{int(datetime.utcnow().timestamp())}"
        
        # Get all context sources
        context = await gather_patient_context(patient_id, request.message, session_id)
        
        # Get orchestrator for processing
        orchestrator = await get_orchestrator()
        
        # Process message with context
        async def generate_response():
            try:
                # Send initial response
                yield f"data: {json.dumps({'type': 'start', 'session_id': session_id})}\n\n"
                
                # Process with orchestrator
                response = await orchestrator.process_user_message(
                    patient_id=patient_id,
                    session_id=session_id,
                    message=request.message,
                    context=context
                )
                
                # Stream the response in chunks
                content = response.get("content", "I'm sorry, I couldn't process your request.")
                
                # Split into chunks for streaming
                chunk_size = 50
                for i in range(0, len(content), chunk_size):
                    chunk = content[i:i + chunk_size]
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                
                # Send completion signal
                yield f"data: {json.dumps({'type': 'complete', 'session_id': session_id})}\n\n"
                
                # Store in memory
                await store_chat_memory(patient_id, session_id, request.message, content, context)
                
            except Exception as e:
                logger.error(f"Chat streaming error: {e}")
                error_msg = f"data: {json.dumps({'type': 'error', 'message': 'An error occurred while processing your request.'})}\n\n"
                yield error_msg
        
        return StreamingResponse(
            generate_response(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except Exception as e:
        logger.error(f"Chat message processing failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to process message")


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str, current_user: CurrentUser):
    """
    Get chat history for a specific session.
    """
    try:
        patient_id = current_user.patient_id
        
        # Get short-term memory for this session
        short_term = get_short_term_memory()
        history = short_term.get_session_history(patient_id, session_id)
        
        return {
            "session_id": session_id,
            "messages": history,
            "total_messages": len(history)
        }
        
    except Exception as e:
        logger.error(f"Failed to get chat history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat history")


async def gather_patient_context(patient_id: str, message: str, session_id: str) -> Dict[str, Any]:
    """Gather all relevant context for the patient."""
    context = {
        "patient_id": patient_id,
        "session_id": session_id,
        "timestamp": datetime.utcnow().isoformat(),
        "short_term_memory": [],
        "long_term_memory": [],
        "similar_documents": [],
        "knowledge_graph": [],
        "medical_entities": []
    }
    
    try:
        # 1. Get short-term memory (current session)
        short_term = get_short_term_memory()
        context["short_term_memory"] = short_term.get_session_history(patient_id, session_id, limit=10)
        
        # 2. Get long-term memory (historical conversations)
        long_term = get_long_term_memory()
        context["long_term_memory"] = long_term.get_relevant_history(patient_id, message, limit=5)
        
        # 3. Similarity search in documents
        try:
            milvus_client = get_milvus()
            similar_docs = await milvus_client.search_similar_documents(patient_id, message, limit=3)
            context["similar_documents"] = similar_docs
        except Exception as e:
            logger.warning(f"Similarity search failed: {e}")
        
        # 4. Neo4j knowledge graph search
        try:
            neo4j_client = get_graph()
            knowledge_results = neo4j_client.search_medical_knowledge(patient_id, message, limit=5)
            context["knowledge_graph"] = knowledge_results
        except Exception as e:
            logger.warning(f"Knowledge graph search failed: {e}")
        
        # 5. Extract medical entities from message
        try:
            from src.agents.medical_entity_extractor import extract_entities
            entities = extract_entities(message)
            context["medical_entities"] = entities
        except Exception as e:
            logger.warning(f"Entity extraction failed: {e}")
        
    except Exception as e:
        logger.error(f"Context gathering failed: {e}")
    
    return context


async def store_chat_memory(patient_id: str, session_id: str, user_message: str, ai_response: str, context: Dict[str, Any]):
    """Store chat interaction in memory systems."""
    try:
        # Store in short-term memory
        short_term = get_short_term_memory()
        short_term.store_message(patient_id, session_id, "user", user_message)
        short_term.store_message(patient_id, session_id, "assistant", ai_response)
        
        # Store in long-term memory
        long_term = get_long_term_memory()
        long_term.store_interaction(patient_id, user_message, ai_response, context)
        
        # Store in Redis for persistence
        redis_client = get_redis()
        redis_client.store_chat_message(patient_id, session_id, {
            "role": "user",
            "content": user_message,
            "timestamp": datetime.utcnow().isoformat()
        })
        redis_client.store_chat_message(patient_id, session_id, {
            "role": "assistant", 
            "content": ai_response,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to store chat memory: {e}")


@router.get("/health")
async def get_chat_health():
    """Health check for chat service."""
    return {
        "status": "healthy",
        "service": "chat",
        "version": "1.0.0",
        "features": [
            "Streaming responses",
            "Short-term memory",
            "Long-term memory", 
            "Similarity search",
            "Knowledge graph integration",
            "Medical entity extraction"
        ]
    }
