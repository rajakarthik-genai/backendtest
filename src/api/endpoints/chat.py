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

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message")
async def send_message(request: ChatRequest) -> ChatResponse:
    """
    Send a chat message and get a response.
    
    Non-streaming endpoint for simple request-response interactions.
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Log user action
        log_user_action(
            request.user_id,
            "chat_message",
            {"session_id": session_id, "message_length": len(request.message)}
        )
        
        # Get orchestrator and process message
        orchestrator = await get_orchestrator()
        
        response = await orchestrator.process_user_message(
            user_id=request.user_id,
            session_id=session_id,
            message=request.message
        )
        
        # Store conversation in memory
        redis_client = get_redis()
        
        # Store user message
        redis_client.store_chat_message(
            request.user_id,
            session_id,
            {
                "role": "user",
                "content": request.message,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Store assistant response
        redis_client.store_chat_message(
            request.user_id,
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
async def stream_chat(request: ChatRequest):
    """
    Stream chat responses using Server-Sent Events (SSE).
    
    Enables real-time streaming of agent responses for better UX.
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Log user action
        log_user_action(
            request.user_id,
            "chat_stream",
            {"session_id": session_id, "message_length": len(request.message)}
        )
        
        # Store user message immediately
        redis_client = get_redis()
        redis_client.store_chat_message(
            request.user_id,
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
                    user_id=request.user_id,
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
                    request.user_id,
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
    user_id: str,
    limit: int = 50
):
    """
    Retrieve chat history for a specific session.
    
    Args:
        session_id: Chat session identifier
        user_id: User identifier for access control
        limit: Maximum number of messages to return
    """
    try:
        redis_client = get_redis()
        
        # Get chat history from Redis
        history = redis_client.get_chat_history(
            user_id,
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
    user_id: str
):
    """
    Clear chat history for a specific session.
    
    Args:
        session_id: Chat session identifier
        user_id: User identifier for access control
    """
    try:
        redis_client = get_redis()
        
        # Delete chat history
        success = redis_client.delete_user_data(user_id)
        
        if success:
            log_user_action(user_id, "chat_history_cleared", {"session_id": session_id})
            return {"message": "Chat history cleared successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear chat history")
        
    except Exception as e:
        logger.error(f"Failed to clear chat history: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear chat history")


@router.get("/sessions")
async def get_user_sessions(user_id: str):
    """
    Get all chat sessions for a user.
    
    Args:
        user_id: User identifier
    """
    try:
        # This would typically query a sessions database
        # For now, return a placeholder response
        return {
            "user_id": user_id,
            "sessions": [],
            "message": "Session management not fully implemented"
        }
        
    except Exception as e:
        logger.error(f"Failed to get user sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sessions")
