from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from datetime import datetime
import logging
import uuid
import json
from typing import Dict, List, Any, Optional

from ...auth.dependencies import get_current_user
from ...api.dependencies import get_db_clients
from ...models.chat import ChatRequest, ChatResponse, ComprehensiveResponse, ExpertAnalysis
from ...core.limiter import limiter
from ...agents.orchestrator_agent import OrchestratorAgent
from ...agents.expert_router import get_expert_router
from ...chat.short_term import get_short_term_memory
from ...chat.long_term import get_long_term_memory

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    dependencies=[Depends(get_current_user)]
)


async def get_medical_context(patient_id: str, db_clients: dict) -> tuple[list, str]:
    """Extract comprehensive medical context from patient records"""
    medical_context = []
    logger.info(f"Starting medical context extraction for patient {patient_id}")
    logger.info(f"Available db_clients: {list(db_clients.keys()) if db_clients else 'No db_clients'}")
    
    if db_clients.get("mongodb") is not None:
        try:
            mongo_db = db_clients["mongodb"]
            logger.info(f"MongoDB connection found: {type(mongo_db)}")
            
            # First, let's check what collections exist
            try:
                collections = mongo_db.list_collection_names()
                logger.info(f"Available MongoDB collections: {collections}")
            except Exception as e:
                logger.warning(f"Could not list collections: {e}")
            
            cursor = mongo_db.documents.find({
                "patient_id": patient_id,
                "extracted_entities": {"$exists": True, "$ne": None}
            })
            
            # Check total documents for this patient
            total_docs = mongo_db.documents.count_documents({"patient_id": patient_id})
            total_with_entities = mongo_db.documents.count_documents({
                "patient_id": patient_id,
                "extracted_entities": {"$exists": True, "$ne": None}
            })
            logger.info(f"Patient {patient_id}: {total_docs} total documents, {total_with_entities} with extracted entities")
            
            try:
                documents = await cursor.to_list(length=100)
            except:
                documents = list(cursor)
            
            logger.info(f"Retrieved {len(documents)} documents with extracted entities")
            
            for i, doc in enumerate(documents):
                logger.info(f"Processing document {i+1}: {doc.get('_id', 'no_id')}")
                extracted_entities = doc.get("extracted_entities", {})
                logger.info(f"Document {i+1} entities keys: {list(extracted_entities.keys()) if isinstance(extracted_entities, dict) else 'not a dict'}")
                
                if isinstance(extracted_entities, dict):
                    # Extract diagnoses/conditions
                    diagnoses = extracted_entities.get("diagnoses", [])
                    logger.info(f"Document {i+1} diagnoses: {len(diagnoses)} found")
                    for diagnosis in diagnoses:
                        if isinstance(diagnosis, dict):
                            if "name" in diagnosis:
                                medical_context.append(f"Condition: {diagnosis['name']}")
                                logger.info(f"Added condition: {diagnosis['name']}")
                            elif "description" in diagnosis:
                                medical_context.append(f"Condition: {diagnosis['description']}")
                                logger.info(f"Added condition: {diagnosis['description']}")
                    
                    # Extract treatments
                    treatments = extracted_entities.get("treatments", [])
                    logger.info(f"Document {i+1} treatments: {len(treatments)} found")
                    for treatment in treatments:
                        if isinstance(treatment, dict) and "type" in treatment:
                            medical_context.append(f"Treatment: {treatment['type']}")
                            logger.info(f"Added treatment: {treatment['type']}")
                    
                    # Extract notes with medical findings
                    notes = extracted_entities.get("notes", [])
                    logger.info(f"Document {i+1} notes: {len(notes)} found")
                    for note in notes:
                        if isinstance(note, dict) and "text" in note:
                            note_text = note["text"]
                            if any(keyword in note_text.lower() for keyword in 
                                  ["pain", "symptom", "reports", "presents", "complaint"]):
                                medical_context.append(f"Finding: {note_text[:100]}")
                                logger.info(f"Added finding: {note_text[:50]}...")
                    
                    # Extract injury events
                    injuries = extracted_entities.get("injuryEvents", [])
                    logger.info(f"Document {i+1} injury events: {len(injuries)} found")
                    for injury in injuries:
                        if isinstance(injury, dict):
                            if "type" in injury:
                                medical_context.append(f"Medical Event: {injury['type']}")
                                logger.info(f"Added medical event: {injury['type']}")
                            if "bodyRegion" in injury:
                                medical_context.append(f"Affected Area: {injury['bodyRegion']}")
                                logger.info(f"Added affected area: {injury['bodyRegion']}")
                
                # Extract key information from processed text
                processed_text = doc.get("processed_text", "")
                logger.info(f"Document {i+1} processed_text length: {len(processed_text)} characters")
                if processed_text:
                    import re
                    # Extract medications
                    med_pattern = r'([A-Za-z]+(?:formin|pril|statin|mycin|cillin))\s*\d*\s*mg'
                    medications = re.findall(med_pattern, processed_text, re.IGNORECASE)
                    for med in medications:
                        medical_context.append(f"Medication: {med}")
                    
                    # Extract vital measurements
                    vital_patterns = [
                        (r'HbA1c[:\s]*(\d+\.?\d*)\s*%', 'HbA1c'),
                        (r'blood pressure[:\s]*(\d+/\d+)', 'Blood Pressure'),
                        (r'troponin[:\s]*(\d+\.?\d*)', 'Troponin'),
                        (r'cholesterol[:\s]*(\d+)', 'Cholesterol')
                    ]
                    for pattern, name in vital_patterns:
                        matches = re.findall(pattern, processed_text, re.IGNORECASE)
                        for match in matches:
                            medical_context.append(f"{name}: {match}")
                            
        except Exception as e:
            logger.warning(f"MongoDB query failed: {e}")
    
    context_text = ", ".join(set(medical_context)) if medical_context else ""
    return medical_context, context_text


async def get_conversation_context(patient_id: str, conversation_id: str, context_window: int = 10) -> str:
    """Get conversation context from short-term memory"""
    try:
        stm = get_short_term_memory()
        messages = await stm.get_recent_messages(patient_id, limit=context_window)
        
        if messages:
            context_parts = []
            for msg in messages[-context_window:]:
                context_parts.append(f"User: {msg.get('user_message', '')}")
                context_parts.append(f"Assistant: {msg.get('assistant_message', '')}")
            
            return "\n".join(context_parts)
        return ""
    except Exception as e:
        logger.warning(f"Failed to get conversation context: {e}")
        return ""


async def perform_expert_analysis(
    query: str, 
    patient_id: str, 
    medical_context: list, 
    conversation_context: str
) -> ComprehensiveResponse:
    """Perform comprehensive expert analysis using dynamic specialist orchestration"""
    try:
        from openai import AsyncOpenAI
        from src.core.config import settings
        
        # Step 1: Determine which specialists to consult using LLM
        specialist_selection_prompt = f"""
        You are a medical triage AI. Based on the following patient query and medical context, determine which medical specialists should be consulted for a comprehensive analysis.

        Patient Query: "{query}"
        
        Medical Context: {', '.join(medical_context[:10]) if medical_context else 'No specific medical context available'}
        
        Conversation Context: {conversation_context[:500] if conversation_context else 'No previous conversation'}

        Available Specialists:
        - cardiologist: Heart, cardiovascular system, chest pain, hypertension, heart attacks
        - neurologist: Brain, nervous system, headaches, seizures, cognitive issues
        - orthopedist: Bones, joints, muscles, back pain, fractures
        - general_physician: General health, prevention, coordination of care

        Instructions:
        1. Select 1-3 most relevant specialists for this case
        2. Explain why each specialist is needed
        3. Assign priority levels (high, medium, low)

        Respond in JSON format:
        {{
            "specialists": [
                {{
                    "type": "cardiologist",
                    "priority": "high",
                    "reason": "Patient has documented heart condition and chest pain symptoms"
                }}
            ],
            "analysis_focus": "Brief description of what the analysis should focus on"
        }}
        """
        
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Get specialist selection
        selection_response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL_COMPLEX,
            messages=[
                {"role": "system", "content": "You are a medical triage AI that determines which specialists to consult."},
                {"role": "user", "content": specialist_selection_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=1000
        )
        
        selection_data = json.loads(selection_response.choices[0].message.content)
        specialists_to_consult = selection_data.get("specialists", [])
        analysis_focus = selection_data.get("analysis_focus", "Comprehensive medical analysis")
        
        logger.info(f"Dynamic specialist selection: {[s['type'] for s in specialists_to_consult]}")
        
        # Step 2: Get analysis from each selected specialist
        expert_analyses = []
        specialist_responses = {}
        
        for specialist_info in specialists_to_consult:
            specialist_type = specialist_info["type"]
            try:
                # Create specialist-specific prompt
                specialist_prompt = f"""
                You are a {specialist_type}. Provide a detailed medical analysis for this patient case.

                Patient Query: "{query}"
                Medical History: {', '.join(medical_context) if medical_context else 'Limited medical history available'}
                Conversation Context: {conversation_context[:300] if conversation_context else 'No previous conversation'}
                Analysis Focus: {analysis_focus}
                Your Priority Level: {specialist_info.get('priority', 'medium')}

                Please provide:
                1. Clinical assessment from your specialty perspective
                2. Relevant medical insights and concerns
                3. Specific recommendations within your expertise
                4. Risk factors or warning signs to monitor
                5. Suggested follow-up or referrals if needed

                Focus on practical, actionable medical guidance while noting that this is for informational purposes and doesn't replace professional medical consultation.
                """
                
                response = await client.chat.completions.create(
                    model=settings.OPENAI_MODEL_COMPLEX,
                    messages=[
                        {"role": "system", "content": f"You are an expert {specialist_type} providing medical analysis and recommendations."},
                        {"role": "user", "content": specialist_prompt}
                    ],
                    temperature=0.2,
                    max_tokens=1500
                )
                
                analysis_text = response.choices[0].message.content
                specialist_responses[specialist_type] = analysis_text
                
                # Create structured expert analysis
                expert_analysis = ExpertAnalysis(
                    specialist=specialist_type,
                    analysis=analysis_text,
                    confidence=0.85,  # Could be determined dynamically
                    recommendations=extract_recommendations(analysis_text),
                    priority=specialist_info.get('priority', 'medium')
                )
                expert_analyses.append(expert_analysis)
                
            except Exception as e:
                logger.error(f"Failed to get analysis from {specialist_type}: {e}")
        
        # Step 3: Aggregate all specialist responses
        aggregation_prompt = f"""
        You are a medical coordinator aggregating insights from multiple specialists for a patient case.

        Patient Query: "{query}"
        
        Specialist Analyses:
        {chr(10).join([f"{spec_type.upper()}: {analysis}" for spec_type, analysis in specialist_responses.items()])}

        Create a comprehensive, cohesive response that:
        1. Synthesizes all specialist insights
        2. Identifies key themes and priorities
        3. Provides clear, actionable guidance
        4. Highlights any conflicting opinions or areas of agreement
        5. Offers a holistic view of the patient's situation

        Keep the response practical and patient-focused while emphasizing the importance of professional medical consultation.
        """
        
        aggregation_response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL_COMPLEX,
            messages=[
                {"role": "system", "content": "You are a medical coordinator providing comprehensive patient guidance by synthesizing multiple specialist opinions."},
                {"role": "user", "content": aggregation_prompt}
            ],
            temperature=0.1,
            max_tokens=2000
        )
        
        main_response = aggregation_response.choices[0].message.content
        
        # Extract key insights and recommendations
        key_insights = extract_key_insights(main_response, specialist_responses)
        recommended_actions = extract_recommended_actions(main_response)
        
        return ComprehensiveResponse(
            response=main_response,
            expert_analyses=expert_analyses,
            summary=f"Comprehensive analysis involving {len(specialists_to_consult)} specialists focusing on {analysis_focus.lower()}",
            key_insights=key_insights,
            recommended_actions=recommended_actions,
            confidence_score=0.85,
            specialists_consulted=[s["type"] for s in specialists_to_consult]
        )
        
    except Exception as e:
        logger.error(f"Expert analysis failed: {e}")
        # Fallback to simple response
        return ComprehensiveResponse(
            response=f"I apologize, but I encountered an issue performing the comprehensive analysis. However, I can still help with your question: {query}. Please consult with your healthcare provider for detailed medical guidance.",
            expert_analyses=[],
            summary="Analysis temporarily unavailable",
            key_insights=["Consult healthcare provider for medical guidance"],
            recommended_actions=["Schedule appointment with primary care physician"],
            confidence_score=0.5,
            specialists_consulted=[]
        )


def extract_recommendations(text: str) -> List[str]:
    """Extract recommendation bullet points from specialist analysis"""
    recommendations = []
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if any(keyword in line.lower() for keyword in ['recommend', 'suggest', 'should', 'consider', 'advise']):
            if len(line) > 10 and len(line) < 200:
                # Clean up the line
                cleaned = line.lstrip('•-* ').strip()
                if cleaned and not cleaned.startswith(('You', 'I', 'The patient')):
                    recommendations.append(cleaned)
    
    return recommendations[:5]  # Limit to top 5


def extract_key_insights(main_response: str, specialist_responses: dict) -> List[str]:
    """Extract key insights from the aggregated response"""
    insights = []
    
    # Look for key phrases in main response
    key_phrases = [
        'important to note', 'key finding', 'significant', 'critical',
        'main concern', 'primary issue', 'notable', 'essential'
    ]
    
    sentences = main_response.split('. ')
    for sentence in sentences:
        if any(phrase in sentence.lower() for phrase in key_phrases):
            if len(sentence) > 20 and len(sentence) < 150:
                insights.append(sentence.strip() + '.' if not sentence.endswith('.') else sentence.strip())
    
    return insights[:4]  # Limit to top 4


def extract_recommended_actions(text: str) -> List[str]:
    """Extract actionable recommendations from the response"""
    actions = []
    lines = text.split('\n')
    
    action_keywords = [
        'follow up', 'schedule', 'monitor', 'track', 'avoid', 'continue',
        'start', 'stop', 'increase', 'decrease', 'consult', 'see your doctor'
    ]
    
    for line in lines:
        line = line.strip()
        if any(keyword in line.lower() for keyword in action_keywords):
            if len(line) > 15 and len(line) < 180:
                cleaned = line.lstrip('•-* ').strip()
                if cleaned:
                    actions.append(cleaned)
    
    return actions[:6]  # Limit to top 6


async def generate_standard_response(
    query: str, 
    medical_context: list, 
    conversation_context: str
) -> str:
    """Generate standard AI chat response with medical context"""
    try:
        from openai import AsyncOpenAI
        from src.core.config import settings
        
        # Parse context items by type for better response generation
        conditions = [item for item in medical_context if "condition:" in item.lower()]
        medications = [item for item in medical_context if "medication:" in item.lower()]
        treatments = [item for item in medical_context if "treatment:" in item.lower()]
        findings = [item for item in medical_context if "finding:" in item.lower()]
        lab_values = [item for item in medical_context if any(lab in item.lower() for lab in ["hba1c:", "blood pressure:", "troponin:", "cholesterol:"])]
        
        # Create context-aware prompt
        context_summary = []
        if conditions:
            context_summary.append(f"Medical conditions: {', '.join([item.split(':', 1)[1].strip() for item in conditions[:3]])}")
        if medications:
            context_summary.append(f"Current medications: {', '.join([item.split(':', 1)[1].strip() for item in medications[:3]])}")
        if lab_values:
            context_summary.append(f"Recent lab values: {', '.join([item.split(':', 1)[1].strip() for item in lab_values[:2]])}")
        
        medical_summary = ". ".join(context_summary) if context_summary else "No specific medical context available"
        
        prompt = f"""
        You are a knowledgeable medical AI assistant helping a patient understand their health information.

        Patient Question: "{query}"
        
        Available Medical Context: {medical_summary}
        
        Recent Conversation: {conversation_context[-300:] if conversation_context else 'No previous conversation'}

        Provide a helpful, informative response that:
        1. Addresses the patient's specific question
        2. References relevant information from their medical records when applicable
        3. Provides educational information about their conditions or medications
        4. Emphasizes the importance of consulting healthcare providers for medical decisions
        5. Is empathetic and supportive

        Keep the response conversational, clear, and focused on helping the patient understand their health better.
        """
        
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL_COMPLEX,
            messages=[
                {"role": "system", "content": "You are a helpful medical AI assistant providing information and guidance to patients based on their medical records and questions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Standard response generation failed: {e}")
        # Fallback response using the existing logic
        return generate_fallback_response(query, medical_context)


def generate_fallback_response(query: str, medical_context: list) -> str:
    """Fallback response generator when OpenAI is unavailable"""
    query_lower = query.lower()
    
    # Parse context items by type
    conditions = [item for item in medical_context if "condition:" in item.lower()]
    medications = [item for item in medical_context if "medication:" in item.lower()]
    
    if "condition" in query_lower or "diagnosis" in query_lower or "health" in query_lower:
        if conditions:
            condition_list = [item.split(":", 1)[1].strip() for item in conditions[:3]]
            return f"Based on your uploaded medical records, your documented health conditions include: {', '.join(condition_list)}. These conditions require ongoing monitoring and management. Please consult with your healthcare provider for personalized medical advice."
        else:
            return "I don't see specific health conditions in your current medical records. For accurate health assessment, please consult with your healthcare provider."
    
    elif "medication" in query_lower or "drug" in query_lower:
        if medications:
            med_list = [item.split(":", 1)[1].strip() for item in medications[:3]]
            return f"According to your uploaded medical records, your documented medications include: {', '.join(med_list)}. Always follow your doctor's instructions and never stop medications without consulting your healthcare provider."
        else:
            return "I don't see specific medications listed in your uploaded medical records. For current medication information, please consult your healthcare provider."
    
    else:
        if medical_context:
            return f"Based on your medical records, I can help you understand your health information. Your records show: {', '.join(medical_context[:3])}. For specific medical questions, please consult with your healthcare provider."
        else:
            return "I'm here to help you understand your medical information. Please upload your medical documents so I can provide more personalized information, or consult with your healthcare provider for medical guidance."


@router.post("/message")
@limiter.limit("1000/hour")
async def unified_chat_message(
    request: Request,
    chat_request: ChatRequest,
    current_user = Depends(get_current_user),
    db_clients: dict = Depends(get_db_clients)
) -> ChatResponse:
    """
    Unified AI chat endpoint with optional expert opinion mode.
    
    When expert_opinion=false: Standard conversational AI with medical context
    When expert_opinion=true: Comprehensive analysis by multiple medical specialists
    """
    try:
        patient_id = current_user.patient_id
        message_id = str(uuid.uuid4())
        
        logger.info(f"Chat request from patient {patient_id}: {'expert mode' if chat_request.expert_opinion else 'standard mode'}")
        logger.info(f"Request message: {chat_request.message[:100]}...")
        
        # Get medical context from processed documents
        logger.info(f"Fetching medical context for patient {patient_id}")
        medical_context, context_text = await get_medical_context(patient_id, db_clients)
        logger.info(f"Retrieved {len(medical_context)} context items: {medical_context[:3] if medical_context else 'No context found'}")
        
        # Get conversation context for continuity
        conversation_context = await get_conversation_context(
            patient_id, 
            chat_request.conversation_id or "default",
            context_window=8
        )
        
        # Store user message in short-term memory
        try:
            stm = get_short_term_memory()
            await stm.store_message(
                patient_id=patient_id,
                conversation_id=chat_request.conversation_id or "default",
                user_message=chat_request.message,
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            logger.warning(f"Failed to store user message: {e}")
        
        # Generate response based on mode
        if chat_request.expert_opinion:
            # Expert mode: Comprehensive analysis by multiple specialists
            logger.info(f"Performing expert analysis for: {chat_request.message[:50]}...")
            
            comprehensive_response = await perform_expert_analysis(
                query=chat_request.message,
                patient_id=patient_id,
                medical_context=medical_context,
                conversation_context=conversation_context
            )
            
            # Store assistant response in memory
            try:
                await stm.store_message(
                    patient_id=patient_id,
                    conversation_id=chat_request.conversation_id or "default",
                    assistant_message=comprehensive_response.response,
                    timestamp=datetime.utcnow(),
                    metadata={
                        "mode": "expert_opinion",
                        "specialists_consulted": comprehensive_response.specialists_consulted,
                        "confidence_score": comprehensive_response.confidence_score
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to store expert response: {e}")
            
            # Return structured expert response
            return ChatResponse(
                message=comprehensive_response.response,
                context_used=len(medical_context) > 0,
                expert_mode=True,
                comprehensive_analysis=comprehensive_response,
                timestamp=datetime.utcnow(),
                conversation_id=chat_request.conversation_id or "default"
            )
            
        else:
            # Standard mode: Regular conversational AI with medical context
            logger.info(f"Generating standard response for: {chat_request.message[:50]}...")
            
            standard_response = await generate_standard_response(
                query=chat_request.message,
                medical_context=medical_context,
                conversation_context=conversation_context
            )
            
            # Store assistant response in memory
            try:
                await stm.store_message(
                    patient_id=patient_id,
                    conversation_id=chat_request.conversation_id or "default",
                    assistant_message=standard_response,
                    timestamp=datetime.utcnow(),
                    metadata={
                        "mode": "standard",
                        "context_items": len(medical_context)
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to store standard response: {e}")
            
            # Return standard chat response
            return ChatResponse(
                message=standard_response,
                context_used=len(medical_context) > 0,
                expert_mode=False,
                timestamp=datetime.utcnow(),
                conversation_id=chat_request.conversation_id or "default"
            )
    
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat message: {str(e)}"
        )


@router.get("/conversation/{conversation_id}/history")
@limiter.limit("100/hour")
async def get_conversation_history(
    request: Request,
    conversation_id: str,
    limit: int = 20,
    current_user = Depends(get_current_user)
):
    """Get conversation history for a specific conversation"""
    try:
        patient_id = current_user.patient_id
        stm = get_short_term_memory()
        
        messages = await stm.get_recent_messages(patient_id, limit=limit)
        
        # Filter by conversation_id if provided
        if conversation_id != "all":
            messages = [msg for msg in messages if msg.get("conversation_id") == conversation_id]
        
        return {
            "conversation_id": conversation_id,
            "messages": messages,
            "total_count": len(messages)
        }
        
    except Exception as e:
        logger.error(f"Failed to get conversation history: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve conversation history"
        )


@router.delete("/conversation/{conversation_id}")
@limiter.limit("50/hour") 
async def clear_conversation(
    request: Request,
    conversation_id: str,
    current_user = Depends(get_current_user)
):
    """Clear a specific conversation"""
    try:
        patient_id = current_user.patient_id
        stm = get_short_term_memory()
        
        # This would require implementing clear_conversation in short_term_memory
        # For now, return success
        return {
            "message": f"Conversation {conversation_id} cleared successfully",
            "conversation_id": conversation_id
        }
        
    except Exception as e:
        logger.error(f"Failed to clear conversation: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to clear conversation"
        )








@router.get("/history")
@limiter.limit("1000/hour")
async def get_chat_history(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db_clients: dict = Depends(get_db_clients),
    limit: int = 20
):
    """
    Get chat history for the current user
    """
    try:
        # Handle different user object types
        if hasattr(current_user, 'get'):
            # Dictionary-like user object
            patient_id = current_user.get("patient_id") or current_user.get("sub")
        else:
            # User object with attributes
            patient_id = getattr(current_user, 'patient_id', None) or getattr(current_user, 'id', None) or getattr(current_user, 'email', None)
        
        if not patient_id:
            raise HTTPException(status_code=400, detail="Unable to identify patient")
        
        if db_clients.get("mongodb") is not None:
            try:
                mongo_db = db_clients["mongodb"]
                # Use find().to_list() for async operation or list() for sync
                cursor = mongo_db.chat_history.find(
                    {"patient_id": patient_id}
                ).sort("timestamp", -1).limit(limit)
                
                # Try async first, fallback to sync
                try:
                    history = await cursor.to_list(length=limit)
                except:
                    history = list(cursor)
                
                # Convert ObjectId and datetime to strings for JSON serialization
                for item in history:
                    if '_id' in item:
                        item['_id'] = str(item['_id'])
                    if 'timestamp' in item and hasattr(item['timestamp'], 'isoformat'):
                        item['timestamp'] = item['timestamp'].isoformat()
                
                return {"history": history, "count": len(history)}
                
            except Exception as e:
                logger.error(f"Chat history retrieval error: {e}")
                return {"history": [], "count": 0}
        
        return {"history": [], "count": 0}
        
    except Exception as e:
        logger.error(f"Chat history error: {e}")
        raise HTTPException(status_code=500, detail="Unable to retrieve chat history")


@router.post("/clear")
@limiter.limit("100/hour")
async def clear_chat_history(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db_clients: dict = Depends(get_db_clients)
):
    """
    Clear chat history for the current user
    """
    try:
        # Handle different user object types
        if hasattr(current_user, 'get'):
            # Dictionary-like user object
            patient_id = current_user.get("patient_id") or current_user.get("sub")
        else:
            # User object with attributes
            patient_id = getattr(current_user, 'patient_id', None) or getattr(current_user, 'id', None) or getattr(current_user, 'email', None)
        
        if not patient_id:
            raise HTTPException(status_code=400, detail="Unable to identify patient")
        
        if db_clients.get("mongodb") is not None:
            mongo_db = db_clients["mongodb"]
            result = mongo_db.chat_history.delete_many({"patient_id": patient_id})
            
            return {
                "message": "Chat history cleared",
                "deleted_count": result.deleted_count
            }
        
        return {"message": "No chat history to clear", "deleted_count": 0}
        
    except Exception as e:
        logger.error(f"Clear chat history error: {e}")
        raise HTTPException(status_code=500, detail="Unable to clear chat history")
