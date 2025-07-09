"""
OpenAI-compatible chat completions endpoint for CrewAI agent integration.

This endpoint provides an OpenAI-like interface that CrewAI agents can use
while internally routing through our medical assistant orchestrator.
"""

from fastapi import APIRouter, HTTPException, Request
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
import asyncio
import json
from src.agents.orchestrator_agent import get_orchestrator
from src.auth.dependencies import CurrentUser
from src.utils.logging import logger
import uuid

router = APIRouter(prefix="/v1", tags=["openai-compat"])


class ChatMessage(BaseModel):
    """OpenAI-compatible chat message."""
    role: str = Field(..., description="Message role: system, user, or assistant")
    content: str = Field(..., description="Message content")
    name: Optional[str] = Field(None, description="Optional message name")


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible chat completion request."""
    model: str = Field(..., description="Model name (ignored, uses our orchestrator)")
    messages: List[ChatMessage] = Field(..., description="List of chat messages")
    temperature: Optional[float] = Field(0.7, description="Sampling temperature")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    stream: Optional[bool] = Field(False, description="Whether to stream responses")
    user: Optional[str] = Field(None, description="User identifier")


class ChatCompletionChoice(BaseModel):
    """OpenAI-compatible completion choice."""
    index: int
    message: ChatMessage
    finish_reason: str


class ChatCompletionResponse(BaseModel):
    """OpenAI-compatible chat completion response."""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Dict[str, int]


@router.post("/chat/completions")
async def create_chat_completion(
    request: ChatCompletionRequest,
    current_user: CurrentUser
):
    """
    OpenAI-compatible chat completions endpoint.
    
    Routes requests through our medical assistant orchestrator while
    maintaining OpenAI API compatibility for CrewAI agents.
    """
    try:
        # Extract user message (last user message in conversation)
        user_message = None
        for msg in reversed(request.messages):
            if msg.role == "user":
                user_message = msg.content
                break
        
        if not user_message:
            raise HTTPException(
                status_code=400,
                detail="No user message found in conversation"
            )
        
        # Get user ID from authentication
        user_id = current_user.user_id
        
        # Use provided user ID if available (for agent identification)
        if request.user:
            session_id = f"crewai_{request.user}"
        else:
            session_id = f"openai_compat_{uuid.uuid4().hex[:8]}"
        
        # Get orchestrator and process message
        orchestrator = await get_orchestrator()
        
        if request.stream:
            # Handle streaming response
            return await _handle_streaming_completion(
                orchestrator, user_id, session_id, user_message, request
            )
        else:
            # Handle regular completion
            response = await orchestrator.process_user_message(
                user_id=user_id,
                session_id=session_id,
                message=user_message
            )
            
            # Convert to OpenAI format
            completion_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
            
            if response.get("success", False):
                content = response.get("response", "I apologize, but I couldn't process your request.")
                finish_reason = "stop"
            else:
                content = f"Error: {response.get('error', 'Unknown error occurred')}"
                finish_reason = "stop"
            
            return ChatCompletionResponse(
                id=completion_id,
                created=int(asyncio.get_event_loop().time()),
                model=request.model,
                choices=[
                    ChatCompletionChoice(
                        index=0,
                        message=ChatMessage(
                            role="assistant",
                            content=content
                        ),
                        finish_reason=finish_reason
                    )
                ],
                usage={
                    "prompt_tokens": len(user_message.split()),
                    "completion_tokens": len(content.split()),
                    "total_tokens": len(user_message.split()) + len(content.split())
                }
            )
            
    except Exception as e:
        logger.error(f"Chat completion failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Chat completion failed: {str(e)}"
        )


async def _handle_streaming_completion(
    orchestrator,
    user_id: str,
    session_id: str,
    user_message: str,
    request: ChatCompletionRequest
):
    """Handle streaming chat completions."""
    from fastapi.responses import StreamingResponse
    import json
    
    async def generate_stream():
        try:
            completion_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
            
            # Send initial chunk
            initial_chunk = {
                'id': completion_id,
                'object': 'chat.completion.chunk',
                'created': int(asyncio.get_event_loop().time()),
                'model': request.model,
                'choices': [{
                    'index': 0,
                    'delta': {'role': 'assistant'},
                    'finish_reason': None
                }]
            }
            yield f"data: {json.dumps(initial_chunk)}\n\n"
            
            # Stream response from orchestrator
            async for chunk in orchestrator.stream_response(
                user_id=user_id,
                session_id=session_id,
                message=user_message
            ):
                if chunk.get("type") == "content_chunk":
                    content = chunk.get("content", "")
                    
                    content_chunk = {
                        'id': completion_id,
                        'object': 'chat.completion.chunk',
                        'created': int(asyncio.get_event_loop().time()),
                        'model': request.model,
                        'choices': [{
                            'index': 0,
                            'delta': {'content': content},
                            'finish_reason': None
                        }]
                    }
                    yield f"data: {json.dumps(content_chunk)}\n\n"
                
                elif chunk.get("type") == "complete":
                    # Send final chunk
                    final_chunk = {
                        'id': completion_id,
                        'object': 'chat.completion.chunk',
                        'created': int(asyncio.get_event_loop().time()),
                        'model': request.model,
                        'choices': [{
                            'index': 0,
                            'delta': {},
                            'finish_reason': 'stop'
                        }]
                    }
                    yield f"data: {json.dumps(final_chunk)}\n\n"
                    
                    yield "data: [DONE]\n\n"
                    break
                    
        except Exception as e:
            logger.error(f"Streaming completion failed: {e}")
            # Send error chunk
            error_chunk = {
                'error': {
                    'message': str(e),
                    'type': 'server_error'
                }
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/models")
async def list_models():
    """
    OpenAI-compatible models endpoint.
    Returns a list of available models for compatibility.
    """
    return {
        "object": "list",
        "data": [
            {
                "id": "meditwin-orchestrator",
                "object": "model",
                "created": 1677649963,
                "owned_by": "meditwin",
                "permission": [],
                "root": "meditwin-orchestrator",
                "parent": None
            }
        ]
    }
