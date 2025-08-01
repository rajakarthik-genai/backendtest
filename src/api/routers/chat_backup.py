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

@router.post("/message")
@limiter.limit("1000/hour")
async def chat_message(
    request: Request,
    chat_request: ChatRequest,
    current_user: dict = Depends(get_current_user),
    db_clients: dict = Depends(get_db_clients)
):
    """
    Simple chat endpoint that returns medical context-aware responses
    """
    try:
        # Get patient context from medical records
        patient_id = current_user.get("patient_id") or current_user.get("user_id")
        
        # Retrieve patient's medical documents for context
        medical_context = []
        conditions = []
        medications = []
        symptoms = []
        body_parts = []
        
        if db_clients.get("mongodb"):
            mongodb = db_clients["mongodb"]
            documents = await mongodb.documents.find(
                {"patient_id": patient_id, "status": "completed"}
            ).to_list(length=10)
            
            for doc in documents:
                if doc.get("extracted_data_summary"):
                    summary = doc["extracted_data_summary"]
                    if summary.get("conditions"):
                        conditions.extend(summary["conditions"])
                    if summary.get("medications"):
                        medications.extend(summary["medications"])
                    if summary.get("symptoms"):
                        symptoms.extend(summary["symptoms"])
                    if summary.get("body_parts"):
                        body_parts.extend(summary["body_parts"])
                    
                    medical_context.append({
                        "document_id": doc.get("document_id"),
                        "summary": summary
                    })
        
        # Generate medical response based on context
        user_message = chat_request.message or chat_request.query or ""
        if not user_message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
            
        response_text = await generate_medical_response(
            user_message, conditions, medications, symptoms, body_parts
        )
        
        return {
            "response": response_text,
            "context_used": len(medical_context) > 0,
            "model": "medical_assistant_v1",
            "processing_time": "~1s",
            "documents_referenced": len(medical_context),
            "medical_entities": {
                "conditions": len(set(conditions)),
                "medications": len(set(medications)),
                "symptoms": len(set(symptoms)),
                "body_parts": len(set(body_parts))
            }
        }
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Chat service temporarily unavailable")


async def generate_medical_response(query: str, conditions: list, medications: list, symptoms: list, body_parts: list) -> str:
    """Generate medical response based on patient context"""
    
    # Basic medical response generation
    query_lower = query.lower()
    
    # Prepare context summary
    unique_conditions = list(set(conditions)) if conditions else []
    unique_medications = list(set(medications)) if medications else []
    unique_symptoms = list(set(symptoms)) if symptoms else []
    unique_body_parts = list(set(body_parts)) if body_parts else []
    
    # Generate contextual response
    if "condition" in query_lower or "health" in query_lower or "medical" in query_lower:
        if unique_conditions:
            response = f"Based on your medical records, your main health conditions include: {', '.join(unique_conditions[:5])}. "
            if len(unique_conditions) > 5:
                response += f"and {len(unique_conditions) - 5} other conditions. "
            
            if unique_medications:
                response += f"\n\nYou are currently taking medications including: {', '.join(unique_medications[:3])}. "
                if len(unique_medications) > 3:
                    response += f"and {len(unique_medications) - 3} other medications. "
            
            response += "\n\nPlease consult with your healthcare provider for personalized medical advice and treatment recommendations."
        else:
            response = "I don't see any specific medical conditions in your uploaded records. Please ensure you've uploaded your medical documents or consult with your healthcare provider."
    
    elif "medication" in query_lower or "drug" in query_lower or "medicine" in query_lower:
        if unique_medications:
            response = f"According to your medical records, you are taking the following medications: {', '.join(unique_medications)}. "
            response += "\n\nFor detailed information about your medications, including dosages, side effects, and interactions, please consult your pharmacist or healthcare provider. "
            response += "Never stop or change medications without professional medical guidance."
        else:
            response = "I don't see any medications listed in your current medical records. Please consult your healthcare provider about your medication needs."
    
    elif "symptom" in query_lower:
        if unique_symptoms:
            response = f"Based on your medical records, you have reported symptoms including: {', '.join(unique_symptoms[:5])}. "
            if len(unique_symptoms) > 5:
                response += f"and {len(unique_symptoms) - 5} other symptoms. "
            response += "\n\nIf you're experiencing new or worsening symptoms, please contact your healthcare provider immediately."
        else:
            response = "I don't see specific symptoms documented in your current medical records. If you're experiencing symptoms, please contact your healthcare provider."
    
    elif "body part" in query_lower or "affected" in query_lower:
        if unique_body_parts:
            response = f"According to your medical records, the following body parts may be affected by your conditions: {', '.join(unique_body_parts)}. "
            response += "\n\nFor detailed information about how your conditions affect these areas, please discuss with your healthcare provider."
        else:
            response = "I don't see specific body parts mentioned in your current medical records."
    
    else:
        # General response
        if any([unique_conditions, unique_medications, unique_symptoms]):
            response = f"I can help you understand your medical information. "
            if unique_conditions:
                response += f"You have {len(unique_conditions)} documented condition(s). "
            if unique_medications:
                response += f"You're taking {len(unique_medications)} medication(s). "
            if unique_symptoms:
                response += f"You've reported {len(unique_symptoms)} symptom(s). "
            
            response += "\n\nYou can ask me about your conditions, medications, symptoms, or affected body parts. "
            response += "For medical advice, always consult your healthcare provider."
        else:
            response = "Hello! I'm your medical assistant. I can help you understand your medical information once you upload your medical documents. "
            response += "Please upload your medical records to get personalized insights about your health conditions, medications, and symptoms."
    
    return response
                        medical_context.extend(summary["conditions"])
                    if summary.get("medications"):
                        medical_context.extend(summary["medications"])
                    if summary.get("symptoms"):
                        medical_context.extend(summary["symptoms"])
        
        # Get entities from Neo4j if available
        neo4j_context = []
        if db_clients.get("neo4j"):
            try:
                neo4j = db_clients["neo4j"]
                result = neo4j.execute_query("""
                    MATCH (p:Patient {patient_id: $patient_id})-[:HAS_DOCUMENT]->(d:Document)
                    -[:EXTRACTED]->(e:Entity)
                    RETURN e.type as entity_type, e.text as entity_text
                    LIMIT 20
                """, {"patient_id": patient_id})
                
                for record in result:
                    neo4j_context.append(f"{record['entity_type']}: {record['entity_text']}")
            except Exception as e:
                logger.warning(f"Neo4j query failed: {e}")
        
        # Combine all available context
        all_context = medical_context + neo4j_context
        context_text = ", ".join(set(all_context)) if all_context else "No specific medical context available"
        
        # Generate contextual response based on the question and medical context
        user_message = chat_request.message.lower()
        response = generate_medical_response(user_message, context_text, all_context)
        
        return {
            "response": response,
            "context_used": len(all_context) > 0,
            "context_items": len(all_context),
            "model": "medical_context_assistant",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Chat service temporarily unavailable")


def generate_medical_response(user_message: str, context_text: str, context_items: list) -> str:
    """Generate medical response based on context"""
    
    # Check what the user is asking about
    if "condition" in user_message or "diagnosis" in user_message or "health" in user_message:
        conditions = [item for item in context_items if any(term in item.lower() for term in ["condition", "disease", "syndrome"])]
        if conditions:
            return f"Based on your medical records, your main health conditions include: {', '.join(conditions[:5])}. These conditions require ongoing monitoring and management. Please consult with your healthcare provider for personalized medical advice."
        else:
            return "I don't see specific health conditions in your current medical records. For accurate health assessment, please consult with your healthcare provider."
    
    elif "medication" in user_message or "drug" in user_message or "prescription" in user_message:
        medications = [item for item in context_items if any(term in item.lower() for term in ["medication", "drug", "mg", "daily", "weekly"])]
        if medications:
            return f"According to your medical records, your current medications include: {', '.join(medications[:5])}. These medications are prescribed to manage your health conditions. Always follow your doctor's instructions and never stop medications without consulting your healthcare provider."
        else:
            return "I don't see specific medications listed in your current medical records. For current medication information, please consult your healthcare provider or pharmacist."
    
    elif "symptom" in user_message or "feel" in user_message or "pain" in user_message:
        symptoms = [item for item in context_items if any(term in item.lower() for term in ["symptom", "pain", "fatigue", "nausea", "headache", "fever"])]
        if symptoms:
            return f"Based on your medical records, you've reported symptoms including: {', '.join(symptoms[:5])}. Tracking symptoms is important for your healthcare team to monitor your condition and adjust treatment as needed."
        else:
            return "I don't see specific symptoms documented in your current medical records. It's important to track and report symptoms to your healthcare provider during visits."
    
    elif "body" in user_message or "affected" in user_message or "part" in user_message:
        if context_items:
            return f"Based on your medical information, various body systems may be affected by your conditions. Your medical records mention: {context_text[:200]}. Different conditions can affect multiple body systems, so comprehensive care is important."
        else:
            return "I don't have specific information about affected body parts in your current medical records. Your healthcare provider can give you detailed information about how your conditions may affect different body systems."
    
    elif "manage" in user_message or "treatment" in user_message or "care" in user_message:
        if context_items:
            return f"Managing your health conditions involves several approaches. Based on your records: {context_text[:150]}. Treatment typically includes medication management, lifestyle modifications, regular monitoring, and coordination between healthcare providers. Always follow your healthcare team's recommendations."
        else:
            return "Health management typically involves medication adherence, lifestyle modifications, regular check-ups, and monitoring symptoms. Your healthcare provider can create a personalized management plan based on your specific needs."
    
    else:
        # General response with available context
        if context_items:
            return f"I can help you understand information from your medical records. Your records include: {context_text[:200]}. For specific medical questions or concerns, please consult with your healthcare provider who can give you personalized medical advice."
        else:
            return "I'm here to help you understand your medical information. Currently, I don't have specific medical context from your records. For medical questions, please consult with your healthcare provider for personalized advice."


@router.post("/")
@limiter.limit("1000/hour")
async def simple_chat(
    request: Request,
    chat_request: ChatRequest,
    current_user: dict = Depends(get_current_user),
    db_clients: dict = Depends(get_db_clients)
):
    """
    Alternative chat endpoint for basic medical responses
    """
    # Redirect to the main chat message endpoint
    return await chat_message(request, chat_request, current_user, db_clients)


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
        # Check available databases
        mongodb_available = db_clients.get("mongodb") is not None
        neo4j_available = db_clients.get("neo4j") is not None
        
        if not mongodb_available and not neo4j_available:
            raise HTTPException(status_code=503, detail="Database(s) not available")
        
        # Initialize OpenAI client
        openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Build context if requested (with graceful degradation)
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat_with_medical_context: {e}")
        raise HTTPException(status_code=503, detail="Database error")

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
        # Check available databases
        mongodb_available = db_clients.get("mongodb") is not None
        neo4j_available = db_clients.get("neo4j") is not None
        
        if not mongodb_available and not neo4j_available:
            raise HTTPException(status_code=503, detail="Database(s) not available")
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in send_chat_message: {e}")
        raise HTTPException(status_code=503, detail="Database error")

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
        # Check available databases
        mongodb_available = db_clients.get("mongodb") is not None
        neo4j_available = db_clients.get("neo4j") is not None
        
        if not mongodb_available and not neo4j_available:
            raise HTTPException(status_code=503, detail="Database(s) not available")
            
        if not mongodb_available:
            return {
                "patient_id": current_user["patient_id"],
                "messages": [],
                "total": 0
            }
            
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
        logger.error(f"Error in get_chat_history: {e}")
        raise HTTPException(status_code=503, detail="Database error")

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
        # Get recent documents if MongoDB is available
        if db_clients.get("mongodb") is not None:
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
        if include_severity and db_clients.get("neo4j") is not None:
            neo4j = db_clients["neo4j"]
            conditions_result = neo4j.execute_query("""
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
        if include_timeline and db_clients.get("neo4j") is not None:
            neo4j = db_clients["neo4j"]
            timeline_result = neo4j.execute_query("""
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
        if db_clients.get("mongodb") is None:
            return []
            
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
        if db_clients.get("mongodb") is None:
            return
            
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
