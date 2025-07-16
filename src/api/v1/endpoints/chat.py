"""
Chat endpoints for real-time conversation with medical agents.

Features:
- Streaming chat responses (SSE)
- Multi-agent orchestration
- Chat history management
- User isolation and security
"""

import json
import uuid
from datetime import datetime
from typing import AsyncGenerator, Dict, Any

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from src.utils.schema import ChatRequest, ChatResponse
from src.utils.logging import logger, log_user_action
from src.agents.orchestrator_agent import get_orchestrator
from src.chat.short_term import get_short_term_memory
from src.db.redis_db import get_redis
from src.auth.dependencies import AuthenticatedPatientId, CurrentUser
from src.auth.models import User

router = APIRouter(tags=["chat"])


@router.post("/message")
async def send_message(
    request: ChatRequest, 
    current_user: CurrentUser
) -> ChatResponse:
    """
    Send a chat message and get a response.
    
    Non-streaming endpoint for simple request-response interactions.
    """
    try:
        # Get patient_id from JWT token
        patient_id = current_user.patient_id
        
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Log user action
        log_user_action(
            patient_id,
            "chat_message",
            {"session_id": session_id, "message_length": len(request.message)}
        )
        
        # Get orchestrator and process message
        orchestrator = await get_orchestrator()
        response = await orchestrator.process_user_message(
            patient_id=patient_id,
            session_id=session_id,
            message=request.message
        )
        
        # Store conversation in memory
        redis_client = get_redis()
        
        # Store user message
        redis_client.store_chat_message(
            patient_id,
            session_id,
            {
                "role": "user",
                "content": request.message,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Store assistant response
        redis_client.store_chat_message(
            patient_id,
            session_id,
            {
                "role": "assistant", 
                "content": response["content"],
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": response.get("metadata", {})
            }
        )
        
        return ChatResponse(
            response=response["content"],
            session_id=session_id,
            metadata=response.get("metadata", {})
        )
        
    except Exception as e:
        logger.error(f"Chat message failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to process message")


@router.post("/stream")
async def stream_chat(
    request: ChatRequest,
    current_user: CurrentUser
):
    """
    Stream chat responses using Server-Sent Events (SSE).
    
    Enables real-time streaming of agent responses for better UX.
    """
    try:
        # Get patient_id from JWT token
        patient_id = current_user.patient_id
        
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Log user action
        log_user_action(
            patient_id,
            "chat_stream",
            {"session_id": session_id, "message_length": len(request.message)}
        )
        
        # Store user message immediately
        redis_client = get_redis()
        redis_client.store_chat_message(
            patient_id,
            session_id,
            {
                "role": "user",
                "content": request.message,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        async def event_generator() -> AsyncGenerator[str, None]:
            """Generate SSE events for streaming response."""
            try:
                orchestrator = await get_orchestrator()
                
                # Send initial metadata
                yield f"data: {json.dumps({'type': 'metadata', 'session_id': session_id})}\n\n"
                
                full_response = ""
                
                # Stream response chunks
                async for chunk in orchestrator.stream_response(
                    patient_id=patient_id,
                    session_id=session_id,
                    message=request.message
                ):
                    if chunk.get("type") == "content":
                        content = chunk.get("content", "")
                        full_response += content
                        
                        # Send content chunk
                        yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                    
                    elif chunk.get("type") == "metadata":
                        # Send metadata updates
                        yield f"data: {json.dumps(chunk)}\n\n"
                
                # Store complete response
                redis_client.store_chat_message(
                    patient_id,
                    session_id,
                    {
                        "role": "assistant",
                        "content": full_response,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                # Send completion signal
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': 'Internal server error'})}\n\n"
        
        return EventSourceResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*"
            }
        )
        
    except Exception as e:
        logger.error(f"Stream setup failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to setup stream")


@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    current_user: CurrentUser,
    limit: int = 50
):
    """
    Retrieve chat history for a specific session.
    
    Args:
        session_id: Chat session identifier
        current_user: Authenticated user from JWT token
        limit: Maximum number of messages to return
    """
    try:
        # Get patient_id from JWT token
        patient_id = current_user.patient_id
        
        redis_client = get_redis()
        
        # Get chat history from Redis
        history = redis_client.get_chat_history(
            patient_id,
            session_id,
            limit
        )
        
        return {
            "session_id": session_id,
            "messages": history,
            "total_messages": len(history)
        }
        
    except Exception as e:
        logger.error(f"Failed to get chat history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat history")


@router.delete("/history/{session_id}")
async def clear_chat_history(
    session_id: str,
    current_user: CurrentUser
):
    """
    Clear chat history for a specific session.
    
    Args:
        session_id: Chat session identifier
        current_user: Authenticated user from JWT token
    """
    try:
        # Get patient_id from JWT token
        patient_id = current_user.patient_id
        
        redis_client = get_redis()
        
        # Delete chat history
        success = redis_client.delete_user_data(user_id)
        
        if success:
            log_user_action(patient_id, "chat_history_cleared", {"session_id": session_id})
            return {"message": "Chat history cleared successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear chat history")
        
    except Exception as e:
        logger.error(f"Failed to clear chat history: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear chat history")


@router.get("/sessions")
async def get_user_sessions(current_user: CurrentUser):
    """
    Get all chat sessions for a user.
    
    Args:
        current_user: Authenticated user from JWT token
    """
    try:
        # Get patient_id from JWT token
        patient_id = current_user.patient_id
        
        # This would typically query a sessions database
        # For now, return a placeholder response
        return {
            "patient_id": patient_id,
            "sessions": [],
            "message": "Session management not fully implemented"
        }
        
    except Exception as e:
        logger.error(f"Failed to get user sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sessions")


@router.post("/chat")
async def basic_chat(
    request: ChatRequest, 
    current_user: CurrentUser
) -> ChatResponse:
    """
    Basic chat endpoint for frontend compatibility.
    This is an alias for the /message endpoint.
    """
    return await send_message(request, current_user)
