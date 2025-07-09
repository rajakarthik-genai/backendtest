"""
OpenAI-Compatible Chat API - For CrewAI integration.

This module provides an OpenAI-compatible chat completions endpoint
that allows CrewAI agents to interact with the medical assistant backend
using standard OpenAI API format.
"""

import time
import uuid
from typing import Dict, Any, List, AsyncGenerator
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from src.utils.schema import OpenAIChatRequest, OpenAIChatResponse, OpenAIChatMessage
from src.agents.orchestrator_agent import OrchestratorAgent
from src.auth.dependencies import CurrentUser
from src.utils.logging import logger
import json

router = APIRouter(prefix="/v1", tags=["openai-compatible"])


@router.post("/chat/completions")
async def chat_completions(
    request: OpenAIChatRequest,
    current_user: CurrentUser = None
):
    """
    OpenAI-compatible chat completions endpoint for CrewAI integration.
    
    This endpoint mimics OpenAI's chat completions API format to enable
    seamless integration with CrewAI agents and other OpenAI-compatible tools.
    """
    try:
        # Extract user ID from request or use authenticated user
        user_id = request.user or (current_user.user_id if current_user else "anonymous")
        
        # Generate session ID for this conversation
        session_id = str(uuid.uuid4())
        
        # Get the last user message
        user_message = None
        for message in reversed(request.messages):
            if message.role == "user":
                user_message = message.content
                break
        
        if not user_message:
            raise HTTPException(status_code=400, detail="No user message found")
        
        # Initialize orchestrator
        orchestrator = OrchestratorAgent()
        
        if request.stream:
            # Stream response
            return StreamingResponse(
                stream_chat_response(orchestrator, user_id, session_id, user_message, request),
                media_type="text/plain"
            )
        else:
            # Non-streaming response
            response = await orchestrator.process_user_message(
                user_id=user_id,
                session_id=session_id,
                message=user_message
            )
            
            # Format as OpenAI response
            return OpenAIChatResponse(
                id=f"chatcmpl-{uuid.uuid4()}",
                object="chat.completion",
                created=int(time.time()),
                model=request.model,
                choices=[{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response.get("response", "Sorry, I couldn't process your request.")
                    },
                    "finish_reason": "stop"
                }],
                usage={
                    "prompt_tokens": len(user_message.split()),
                    "completion_tokens": len(response.get("response", "").split()),
                    "total_tokens": len(user_message.split()) + len(response.get("response", "").split())
                }
            )
            
    except Exception as e:
        logger.error(f"Chat completions failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chat completion failed: {str(e)}")


async def stream_chat_response(
    orchestrator: OrchestratorAgent,
    user_id: str,
    session_id: str,
    message: str,
    request: OpenAIChatRequest
) -> AsyncGenerator[str, None]:
    """
    Stream chat response in OpenAI format.
    """
    try:
        # Generate response ID
        response_id = f"chatcmpl-{uuid.uuid4()}"
        
        # Send initial chunk
        initial_chunk = {
            "id": response_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": request.model,
            "choices": [{
                "index": 0,
                "delta": {"role": "assistant"},
                "finish_reason": None
            }]
        }
        yield f"data: {json.dumps(initial_chunk)}\n\n"
        
        # Stream response from orchestrator
        async for chunk in orchestrator.stream_response(user_id, session_id, message):
            if chunk.get("type") == "content_chunk":
                content = chunk.get("content", "")
                if content:
                    stream_chunk = {
                        "id": response_id,
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": request.model,
                        "choices": [{
                            "index": 0,
                            "delta": {"content": content},
                            "finish_reason": None
                        }]
                    }
                    yield f"data: {json.dumps(stream_chunk)}\n\n"
            
            elif chunk.get("type") == "status":
                # Handle status updates (tool calls, etc.)
                status_chunk = {
                    "id": response_id,
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": request.model,
                    "choices": [{
                        "index": 0,
                        "delta": {"content": f"\\n[{chunk.get('message', '')}]\\n"},
                        "finish_reason": None
                    }]
                }
                yield f"data: {json.dumps(status_chunk)}\n\n"
        
        # Send final chunk
        final_chunk = {
            "id": response_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": request.model,
            "choices": [{
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }]
        }
        yield f"data: {json.dumps(final_chunk)}\n\n"
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"Streaming failed: {e}")
        error_chunk = {
            "error": {
                "message": str(e),
                "type": "server_error"
            }
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"


@router.get("/models")
async def list_models():
    """
    List available models (OpenAI-compatible).
    """
    return {
        "object": "list",
        "data": [
            {
                "id": "gpt-3.5-turbo",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "meditwin",
                "permission": [],
                "root": "gpt-3.5-turbo"
            },
            {
                "id": "gpt-4",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "meditwin",
                "permission": [],
                "root": "gpt-4"
            }
        ]
    }


@router.get("/health")
async def health_check():
    """
    Health check endpoint for service monitoring.
    """
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0"
    }
