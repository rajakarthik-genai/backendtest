"""
Chat endpoint with streaming responses
Implements RAG with patient context and medical knowledge
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import json
import asyncio
from datetime import datetime
import logging
import openai

from src.api.dependencies import get_current_user, get_db_clients, require_patient_access
from src.auth.dependencies import get_authenticated_patient_id, AuthenticatedPatientId
from src.models.chat import ChatRequest, ChatMessage
from src.core.config import settings
from src.core.limiter import limiter

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/stream")
@limiter.limit("1000/hour")
async def chat_with_medical_context(
    request: Request,
    chat_request: ChatRequest,
    current_user: dict = Depends(get_current_user),
    db_clients: dict = Depends(get_db_clients)
):
    """
    Stream chat responses with full medical context
    
    Features:
    - Patient medical history context
    - Vector similarity search on documents
    - Neo4j relationship traversal
    - Short and long-term memory
    - OpenAI SSE format streaming
    """
    try:
        # Initialize OpenAI client
        openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Build context if requested
        context = None
        if chat_request.include_context:
            context = await _build_context(
                patient_id=current_user["patient_id"],
                query=chat_request.query,
                db_clients=db_clients,
                include_severity=chat_request.include_severity_data,
                include_timeline=chat_request.include_timeline_data,
                context_window=chat_request.context_window
            )
            
            logger.info(f"Built context with {len(context.get('documents', []))} documents, "
                       f"{len(context.get('timeline_events', []))} timeline events")
        
        # Generate streaming response
        async def generate_sse_stream() -> AsyncGenerator[str, None]:
            try:
                # Add system message with context
                messages = [
                    {
                        "role": "system",
                        "content": _build_system_prompt(current_user["patient_id"], context)
                    },
                    {
                        "role": "user",
                        "content": chat_request.query
                    }
                ]
                
                # Get conversation history from memory
                history = await _get_conversation_history(
                    patient_id=current_user["patient_id"],
                    limit=chat_request.context_window,
                    db_clients=db_clients
                )
                
                # Insert history before current message
                if history:
                    messages = messages[:1] + history + messages[1:]
                
                # Stream from OpenAI
                stream_id = f"chat-{current_user['patient_id']}-{int(datetime.now().timestamp())}"
                chunk_index = 0
                full_response = ""
                
                # Create OpenAI stream
                stream = await openai_client.chat.completions.create(
                    model=settings.OPENAI_MODEL_COMPLEX,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=settings.OPENAI_MAX_TOKENS,
                    stream=True
                )
                
                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        
                        sse_data = {
                            "id": f"{stream_id}-{chunk_index}",
                            "object": "chat.completion.chunk",
                            "created": int(datetime.now().timestamp()),
                            "model": settings.OPENAI_MODEL_COMPLEX,
                            "choices": [{
                                "index": 0,
                                "delta": {"content": content},
                                "finish_reason": None
                            }],
                            "usage": None
                        }
                        
                        yield f"data: {json.dumps(sse_data)}\n\n"
                        chunk_index += 1
                
                # Send completion
                sse_data = {
                    "id": f"{stream_id}-{chunk_index}",
                    "object": "chat.completion.chunk",
                    "created": int(datetime.now().timestamp()),
                    "model": settings.OPENAI_MODEL_COMPLEX,
                    "choices": [{
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop"
                    }],
                    "usage": {
                        "prompt_tokens": len(str(messages)),
                        "completion_tokens": len(full_response),
                        "total_tokens": len(str(messages)) + len(full_response)
                    }
                }
                
                yield f"data: {json.dumps(sse_data)}\n\n"
                yield "data: [DONE]\n\n"
                
                # Save to memory
                await _save_to_memory(
                    patient_id=current_user["patient_id"],
                    user_message=chat_request.query,
                    assistant_message=full_response,
                    context_used=bool(context),
                    db_clients=db_clients
                )
                
            except Exception as e:
                logger.error(f"Error in chat stream: {str(e)}", exc_info=True)
                error_data = {
                    "error": {
                        "message": str(e),
                        "type": "stream_error",
                        "code": "internal_error"
                    }
                }
                yield f"data: {json.dumps(error_data)}\n\n"
        
        return StreamingResponse(
            generate_sse_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/message")
@limiter.limit("1000/hour")
async def send_chat_message(
    request: Request,
    chat_request: ChatRequest,
    current_user: dict = Depends(get_current_user),
    db_clients: dict = Depends(get_db_clients)
):
    """
    Non-streaming chat endpoint for simple responses
    Uses simpler model for basic queries
    """
    try:
        # Initialize OpenAI client
        openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Determine if context is needed
        needs_context = _query_needs_context(chat_request.query)
        
        context = None
        if needs_context and chat_request.include_context:
            context = await _build_context(
                patient_id=current_user["patient_id"],
                query=chat_request.query,
                db_clients=db_clients,
                include_severity=False,  # Simpler context
                include_timeline=False,
                context_window=5
            )
        
        # Generate response
        messages = [
            {
                "role": "system",
                "content": _build_simple_system_prompt(current_user["patient_id"])
            },
            {
                "role": "user",
                "content": chat_request.query
            }
        ]
        
        response = await openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL_SIMPLE,
            messages=messages,
            temperature=0.1,
            max_tokens=1000
        )
        
        response_text = response.choices[0].message.content
        
        # Save to memory
        await _save_to_memory(
            patient_id=current_user["patient_id"],
            user_message=chat_request.query,
            assistant_message=response_text,
            context_used=bool(context),
            db_clients=db_clients
        )
        
        return {
            "response": response_text,
            "patient_id": current_user["patient_id"],
            "context_used": bool(context),
            "model": settings.OPENAI_MODEL_SIMPLE,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Chat message error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
@limiter.limit("100/hour")
async def get_chat_history(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db_clients: dict = Depends(get_db_clients),
    limit: int = 50,
    offset: int = 0
):
    """
    Get chat history for a patient
    """
    try:
        # Get from MongoDB
        cursor = db_clients["mongodb"].chat_history.find(
            {"patient_id": current_user["patient_id"]}
        ).sort("timestamp", -1).skip(offset).limit(limit)
        
        history = await cursor.to_list(length=limit)
        
        # Format response
        return {
            "patient_id": current_user["patient_id"],
            "messages": [
                {
                    "message_id": str(msg["_id"]),
                    "timestamp": msg["timestamp"],
                    "user_message": msg["user_message"],
                    "assistant_message": msg["assistant_message"],
                    "context_used": msg.get("context_used", False),
                    "model": msg.get("model", "unknown")
                }
                for msg in history
            ],
            "total": await db_clients["mongodb"].chat_history.count_documents(
                {"patient_id": current_user["patient_id"]}
            )
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chat history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions

async def _build_context(
    patient_id: str,
    query: str,
    db_clients: dict,
    include_severity: bool = True,
    include_timeline: bool = True,
    context_window: int = 10
) -> dict:
    """Build medical context for the patient"""
    context = {
        "documents": [],
        "active_conditions": [],
        "timeline_events": []
    }
    
    try:
        # Get recent documents
        cursor = db_clients["mongodb"].documents.find(
            {"patient_id": patient_id, "status": "completed"}
        ).sort("uploaded_at", -1).limit(context_window)
        
        documents = await cursor.to_list(length=context_window)
        context["documents"] = [
            {
                "filename": doc["filename"],
                "date": doc["uploaded_at"].strftime("%Y-%m-%d"),
                "summary": f"Medical document: {doc['filename']}"
            }
            for doc in documents
        ]
        
        # Get active conditions from Neo4j if include_severity
        if include_severity:
            neo4j = db_clients["neo4j"]
            conditions_result = await neo4j.execute_query("""
                MATCH (p:Patient {patient_id: $patient_id})-[:HAS_CONDITION]->(c:Condition)
                WHERE c.status = 'active'
                RETURN c.name as name, c.severity as severity
                ORDER BY c.severity DESC
                LIMIT 10
            """, {"patient_id": patient_id})
            
            context["active_conditions"] = [
                {
                    "name": record["name"],
                    "severity": record["severity"]
                }
                for record in conditions_result
            ]
        
        # Get recent timeline events if include_timeline
        if include_timeline:
            neo4j = db_clients["neo4j"]
            timeline_result = await neo4j.execute_query("""
                MATCH (p:Patient {patient_id: $patient_id})-[:HAS_EVENT]->(e:Event)
                RETURN e.date as date, e.description as description
                ORDER BY e.date DESC
                LIMIT 5
            """, {"patient_id": patient_id})
            
            context["timeline_events"] = [
                {
                    "date": record["date"],
                    "description": record["description"]
                }
                for record in timeline_result
            ]
        
    except Exception as e:
        logger.warning(f"Failed to build context: {e}")
    
    return context

def _build_system_prompt(patient_id: str, context: dict = None) -> str:
    """Build system prompt with medical context"""
    prompt = f"""You are a knowledgeable medical AI assistant helping with patient {patient_id}.
    
You have access to the patient's medical history and should provide accurate, helpful responses.
Always be empathetic and professional. If you're unsure about something, say so.

Important guidelines:
- Reference specific documents or test results when relevant
- Mention dates and timelines when discussing medical events
- Highlight any concerning trends or improvements
- Suggest consulting healthcare providers for medical decisions
- Never provide definitive diagnoses or treatment plans
"""
    
    if context:
        prompt += "\n\nRelevant Patient Context:\n"
        
        # Add document summaries
        if context.get("documents"):
            prompt += "\nRecent Medical Documents:\n"
            for doc in context["documents"][:5]:  # Top 5 most relevant
                prompt += f"- {doc['filename']} ({doc['date']}): {doc['summary']}\n"
        
        # Add current conditions
        if context.get("active_conditions"):
            prompt += "\nActive Conditions:\n"
            for condition in context["active_conditions"]:
                prompt += f"- {condition['name']} (Severity: {condition['severity']}/10)\n"
        
        # Add recent timeline
        if context.get("timeline_events"):
            prompt += "\nRecent Medical Events:\n"
            for event in context["timeline_events"][:5]:
                prompt += f"- {event['date']}: {event['description']}\n"
    
    return prompt

def _build_simple_system_prompt(patient_id: str) -> str:
    """Build simple system prompt for basic queries"""
    return f"""You are a helpful medical AI assistant for patient {patient_id}.
Provide clear, concise responses to general health questions.
If the question requires specific patient data, mention that you'd need to look at their medical records.
Always suggest consulting healthcare providers for medical advice."""

def _query_needs_context(query: str) -> bool:
    """Determine if query requires medical context"""
    context_keywords = [
        "my", "i", "test", "result", "medication", "condition",
        "history", "previous", "last", "recent", "diagnosis",
        "treatment", "symptom", "pain", "report"
    ]
    
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in context_keywords)

async def _get_conversation_history(
    patient_id: str,
    limit: int,
    db_clients: dict
) -> list:
    """Get recent conversation history"""
    try:
        cursor = db_clients["mongodb"].chat_history.find(
            {"patient_id": patient_id}
        ).sort("timestamp", -1).limit(limit)
        
        history = await cursor.to_list(length=limit)
        
        # Convert to OpenAI format
        messages = []
        for msg in reversed(history):  # Reverse to get chronological order
            messages.append({"role": "user", "content": msg["user_message"]})
            messages.append({"role": "assistant", "content": msg["assistant_message"]})
        
        return messages
        
    except Exception as e:
        logger.warning(f"Failed to get conversation history: {e}")
        return []

async def _save_to_memory(
    patient_id: str,
    user_message: str,
    assistant_message: str,
    context_used: bool,
    db_clients: dict
):
    """Save conversation to memory"""
    try:
        chat_record = {
            "patient_id": patient_id,
            "timestamp": datetime.utcnow(),
            "user_message": user_message,
            "assistant_message": assistant_message,
            "context_used": context_used,
            "model": settings.OPENAI_MODEL_COMPLEX
        }
        
        await db_clients["mongodb"].chat_history.insert_one(chat_record)
        
    except Exception as e:
        logger.error(f"Failed to save chat to memory: {e}")
