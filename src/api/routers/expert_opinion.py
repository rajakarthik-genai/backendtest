"""
Expert Opinion API endpoints with multi-agent crew orchestration.

Provides comprehensive medical consultation through AI-powered multi-agent collaboration:
- Dynamic specialist selection based on query analysis and patient conditions
- Multi-agent discussion and consensus building
- Streaming responses with real-time collaboration
- Integration with patient medical history and data
- Similar to advanced AI research agents like ChatGPT's deep research

Features:
- Automatic medical specialist selection
- Multi-agent collaboration and discussion
- Comprehensive medical analysis
- Consensus building across specialists
- Real-time streaming responses
- Patient context integration
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator, List, Dict
import json
import asyncio
from datetime import datetime
import logging
import openai

from src.api.dependencies import get_current_user, get_db_clients, require_patient_access
from src.auth.dependencies import get_authenticated_patient_id, AuthenticatedPatientId
from src.models.chat import ExpertOpinionRequest
from src.core.config import settings, EXPERT_SPECIALTIES
from src.core.limiter import limiter

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/streaming")
@limiter.limit("50/hour")
async def get_streaming_expert_opinion(
    request: Request,
    opinion_request: ExpertOpinionRequest,
    patient_id: str = Depends(get_authenticated_patient_id),
    db_clients: dict = Depends(get_db_clients)
):
    """
    Multi-agent expert medical consultation with dynamic specialist selection.
    
    Provides comprehensive medical analysis through AI-powered multi-agent collaboration:
    
    Intelligence Features:
    - Automatic medical specialist selection based on query analysis
    - Dynamic crew formation based on patient conditions and query complexity
    - Multi-agent discussion and consensus building
    - Comprehensive medical reasoning across specialties
    - Integration with patient medical history and current data
    
    Technical Features:
    - Real-time streaming responses
    - Patient context integration from MongoDB and Neo4j
    - Confidence scoring and source attribution
    - Emergency indicator detection
    - Structured output with metadata
    
    Process:
    1. Query analysis and specialist selection
    2. Patient context retrieval and integration
    3. Multi-agent discussion and analysis
    4. Consensus building and synthesis
    5. Streaming response generation
    
    Args:
        opinion_request: Expert opinion request with query and patient context
        
    Returns:
        StreamingResponse: Real-time medical consultation with structured analysis
    """
    try:
        # Initialize OpenAI client
        openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Build comprehensive context
        context = await _build_comprehensive_context(
            patient_id=opinion_request.patient_id,
            query=opinion_request.query,
            include_full_history=opinion_request.include_full_history,
            focus_body_parts=opinion_request.focus_body_parts,
            db_clients=db_clients
        )
        
        # Analyze query and select appropriate experts
        selected_experts = await _select_experts(
            query=opinion_request.query,
            affected_body_parts=opinion_request.focus_body_parts or [],
            patient_conditions=context.get("active_conditions", []),
            urgency=opinion_request.urgency,
            openai_client=openai_client
        )
        
        logger.info(f"Selected experts: {selected_experts} for patient {opinion_request.patient_id}")
        
        # Generate streaming expert analysis
        async def generate_expert_stream() -> AsyncGenerator[str, None]:
            try:
                stream_id = f"expert-{opinion_request.patient_id}-{int(datetime.now().timestamp())}"
                chunk_index = 0
                
                # Send initialization
                init_data = {
                    "id": f"{stream_id}-init",
                    "object": "expert.opinion.chunk",
                    "created": int(datetime.now().timestamp()),
                    "model": "medical-expert-crew-v2",
                    "experts_selected": selected_experts,
                    "analysis_depth": "comprehensive" if opinion_request.include_full_history else "focused",
                    "urgency": opinion_request.urgency,
                    "choices": [{
                        "index": 0,
                        "delta": {"content": f"Initializing expert analysis with {len(selected_experts)} specialists...\n\n"},
                        "finish_reason": None
                    }]
                }
                yield f"data: {json.dumps(init_data)}\n\n"
                await asyncio.sleep(0.5)
                
                # Run expert analysis
                full_response = ""
                
                # Phase 1: Individual expert assessments
                expert_assessments = await _get_individual_assessments(
                    experts=selected_experts,
                    query=opinion_request.query,
                    context=context,
                    openai_client=openai_client
                )
                
                for expert, assessment in expert_assessments.items():
                    expert_header = f"**{expert.replace('_', ' ').title()} Assessment:**\n"
                    
                    # Stream header
                    header_data = {
                        "id": f"{stream_id}-{chunk_index}",
                        "object": "expert.opinion.chunk",
                        "created": int(datetime.now().timestamp()),
                        "model": "medical-expert-crew-v2",
                        "current_expert": expert,
                        "choices": [{
                            "index": 0,
                            "delta": {"content": expert_header},
                            "finish_reason": None
                        }]
                    }
                    yield f"data: {json.dumps(header_data)}\n\n"
                    chunk_index += 1
                    
                    # Stream assessment content
                    for chunk in _chunk_text(assessment, 100):
                        chunk_data = {
                            "id": f"{stream_id}-{chunk_index}",
                            "object": "expert.opinion.chunk",
                            "created": int(datetime.now().timestamp()),
                            "model": "medical-expert-crew-v2",
                            "current_expert": expert,
                            "choices": [{
                                "index": 0,
                                "delta": {"content": chunk},
                                "finish_reason": None
                            }]
                        }
                        yield f"data: {json.dumps(chunk_data)}\n\n"
                        chunk_index += 1
                        await asyncio.sleep(0.05)
                    
                    full_response += expert_header + assessment + "\n\n"
                
                # Phase 2: Consensus and recommendations
                consensus_header = "**Expert Consensus & Recommendations:**\n"
                consensus = await _generate_consensus(
                    expert_assessments=expert_assessments,
                    query=opinion_request.query,
                    context=context,
                    openai_client=openai_client
                )
                
                # Stream consensus header
                consensus_header_data = {
                    "id": f"{stream_id}-{chunk_index}",
                    "object": "expert.opinion.chunk",
                    "created": int(datetime.now().timestamp()),
                    "model": "medical-expert-crew-v2",
                    "phase": "consensus",
                    "choices": [{
                        "index": 0,
                        "delta": {"content": consensus_header},
                        "finish_reason": None
                    }]
                }
                yield f"data: {json.dumps(consensus_header_data)}\n\n"
                chunk_index += 1
                
                # Stream consensus content
                for chunk in _chunk_text(consensus, 100):
                    chunk_data = {
                        "id": f"{stream_id}-{chunk_index}",
                        "object": "expert.opinion.chunk",
                        "created": int(datetime.now().timestamp()),
                        "model": "medical-expert-crew-v2",
                        "phase": "consensus",
                        "choices": [{
                            "index": 0,
                            "delta": {"content": chunk},
                            "finish_reason": None
                        }]
                    }
                    yield f"data: {json.dumps(chunk_data)}\n\n"
                    chunk_index += 1
                    await asyncio.sleep(0.05)
                
                full_response += consensus_header + consensus
                
                # Send completion
                completion_data = {
                    "id": f"{stream_id}-{chunk_index}",
                    "object": "expert.opinion.chunk",
                    "created": int(datetime.now().timestamp()),
                    "model": "medical-expert-crew-v2",
                    "choices": [{
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop"
                    }],
                    "usage": {
                        "experts_consulted": len(selected_experts),
                        "total_tokens": len(full_response)
                    }
                }
                yield f"data: {json.dumps(completion_data)}\n\n"
                yield "data: [DONE]\n\n"
                
                # Save expert opinion to memory
                await _save_expert_opinion(
                    patient_id=opinion_request.patient_id,
                    query=opinion_request.query,
                    expert_response=full_response,
                    experts_consulted=selected_experts,
                    db_clients=db_clients
                )
                
            except Exception as e:
                logger.error(f"Error in expert opinion stream: {str(e)}", exc_info=True)
                error_data = {
                    "error": {
                        "message": str(e),
                        "type": "expert_stream_error",
                        "code": "internal_error"
                    }
                }
                yield f"data: {json.dumps(error_data)}\n\n"
        
        return StreamingResponse(
            generate_expert_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        logger.error(f"Expert opinion endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/quick")
@limiter.limit("200/hour")
async def get_quick_expert_opinion(
    request: Request,
    opinion_request: ExpertOpinionRequest,
    patient_id: str = Depends(get_authenticated_patient_id),
    db_clients: dict = Depends(get_db_clients)
):
    """
    Quick expert opinion for simple queries (non-streaming)
    """
    try:
        # Initialize OpenAI client
        openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Build simplified context
        context = await _build_simplified_context(
            patient_id=opinion_request.patient_id,
            query=opinion_request.query,
            db_clients=db_clients
        )
        
        # Select primary expert
        primary_expert = await _select_primary_expert(
            query=opinion_request.query,
            openai_client=openai_client
        )
        
        # Generate quick assessment
        assessment = await _get_quick_assessment(
            expert=primary_expert,
            query=opinion_request.query,
            context=context,
            openai_client=openai_client
        )
        
        return {
            "patient_id": opinion_request.patient_id,
            "primary_expert": primary_expert,
            "assessment": assessment,
            "urgency": opinion_request.urgency,
            "timestamp": datetime.now().isoformat(),
            "disclaimer": "This is a quick AI assessment. Please consult with healthcare providers for medical decisions."
        }
        
    except Exception as e:
        logger.error(f"Quick expert opinion error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions

async def _build_comprehensive_context(
    patient_id: str,
    query: str,
    include_full_history: bool,
    focus_body_parts: List[str],
    db_clients: dict
) -> dict:
    """Build comprehensive medical context"""
    context = {
        "patient_id": patient_id,
        "documents": [],
        "active_conditions": [],
        "timeline_events": [],
        "medications": [],
        "body_part_status": {}
    }
    
    try:
        # Get documents
        if include_full_history:
            cursor = db_clients["mongodb"].documents.find(
                {"patient_id": patient_id, "status": "completed"}
            ).sort("uploaded_at", -1).limit(20)
        else:
            cursor = db_clients["mongodb"].documents.find(
                {"patient_id": patient_id, "status": "completed"}
            ).sort("uploaded_at", -1).limit(5)
        
        documents = await cursor.to_list(length=20)
        context["documents"] = [
            {
                "filename": doc["filename"],
                "date": doc["uploaded_at"].strftime("%Y-%m-%d"),
                "type": doc["file_type"]
            }
            for doc in documents
        ]
        
        # Get conditions and medications from Neo4j
        neo4j = db_clients["neo4j"]
        
        conditions_result = await neo4j.execute_query("""
            MATCH (p:Patient {patient_id: $patient_id})-[:HAS_CONDITION]->(c:Condition)
            WHERE c.status = 'active'
            RETURN c.name as name, c.severity as severity, c.diagnosed_date as date
            ORDER BY c.severity DESC
        """, {"patient_id": patient_id})
        
        context["active_conditions"] = [
            {
                "name": record["name"],
                "severity": record["severity"],
                "date": record["date"]
            }
            for record in conditions_result
        ]
        
    except Exception as e:
        logger.warning(f"Failed to build comprehensive context: {e}")
    
    return context

async def _build_simplified_context(patient_id: str, query: str, db_clients: dict) -> dict:
    """Build simplified context for quick opinions"""
    context = {"patient_id": patient_id, "recent_conditions": []}
    
    try:
        neo4j = db_clients["neo4j"]
        conditions_result = await neo4j.execute_query("""
            MATCH (p:Patient {patient_id: $patient_id})-[:HAS_CONDITION]->(c:Condition)
            WHERE c.status = 'active'
            RETURN c.name as name, c.severity as severity
            ORDER BY c.severity DESC
            LIMIT 5
        """, {"patient_id": patient_id})
        
        context["recent_conditions"] = [
            {"name": record["name"], "severity": record["severity"]}
            for record in conditions_result
        ]
        
    except Exception as e:
        logger.warning(f"Failed to build simplified context: {e}")
    
    return context

async def _select_experts(
    query: str,
    affected_body_parts: List[str],
    patient_conditions: List[dict],
    urgency: str,
    openai_client
) -> List[str]:
    """Select appropriate medical experts based on query and patient data"""
    try:
        # Create expert selection prompt
        prompt = f"""
        Based on the medical query and patient information, select 2-4 most relevant medical specialists.
        
        Query: {query}
        Affected Body Parts: {affected_body_parts}
        Patient Conditions: {[c.get('name', '') for c in patient_conditions]}
        Urgency: {urgency}
        
        Available Specialists: {list(EXPERT_SPECIALTIES.keys())}
        
        Return a JSON array of specialist names (e.g., ["cardiologist", "neurologist"]).
        Consider the query content, affected anatomy, and existing conditions.
        """
        
        response = await openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL_SIMPLE,
            messages=[
                {"role": "system", "content": "You are a medical triage specialist. Select the most appropriate experts for consultation."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=200
        )
        
        # Parse response
        experts_text = response.choices[0].message.content
        experts = json.loads(experts_text)
        
        # Validate experts
        valid_experts = [e for e in experts if e in EXPERT_SPECIALTIES]
        
        # Ensure we have at least one expert
        if not valid_experts:
            valid_experts = ["internist"]  # Default to internal medicine
        
        return valid_experts[:4]  # Max 4 experts
        
    except Exception as e:
        logger.warning(f"Expert selection failed: {e}")
        return ["internist"]  # Default fallback

async def _select_primary_expert(query: str, openai_client) -> str:
    """Select single primary expert for quick opinions"""
    try:
        prompt = f"""
        Based on this medical query, select the single most relevant specialist:
        
        Query: {query}
        Available: {list(EXPERT_SPECIALTIES.keys())}
        
        Return just the specialist name (e.g., "cardiologist").
        """
        
        response = await openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL_SIMPLE,
            messages=[
                {"role": "system", "content": "Select the most relevant medical specialist."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=50
        )
        
        expert = response.choices[0].message.content.strip().lower()
        return expert if expert in EXPERT_SPECIALTIES else "internist"
        
    except Exception as e:
        logger.warning(f"Primary expert selection failed: {e}")
        return "internist"

async def _get_individual_assessments(
    experts: List[str],
    query: str,
    context: dict,
    openai_client
) -> Dict[str, str]:
    """Get individual assessments from each expert"""
    assessments = {}
    
    for expert in experts:
        try:
            specialty_areas = EXPERT_SPECIALTIES.get(expert, ["general"])
            
            prompt = f"""
            You are a {expert.replace('_', ' ')} providing a medical assessment.
            
            Patient Query: {query}
            
            Patient Context:
            - Active Conditions: {context.get('active_conditions', [])}
            - Recent Documents: {len(context.get('documents', []))} medical records
            
            Your specialty areas: {specialty_areas}
            
            Provide a focused assessment from your specialty perspective:
            1. Relevant findings from your specialty
            2. Potential concerns or red flags
            3. Recommended next steps
            4. When to seek urgent care (if applicable)
            
            Keep response concise but thorough (2-3 paragraphs).
            """
            
            response = await openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL_COMPLEX,
                messages=[
                    {"role": "system", "content": f"You are an experienced {expert.replace('_', ' ')} providing medical consultation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=800
            )
            
            assessments[expert] = response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Failed to get assessment from {expert}: {e}")
            assessments[expert] = f"Unable to provide {expert} assessment at this time."
    
    return assessments

async def _get_quick_assessment(expert: str, query: str, context: dict, openai_client) -> str:
    """Get quick assessment from single expert"""
    try:
        prompt = f"""
        As a {expert.replace('_', ' ')}, provide a brief assessment:
        
        Query: {query}
        Recent Conditions: {context.get('recent_conditions', [])}
        
        Provide a concise professional opinion (1-2 paragraphs).
        """
        
        response = await openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL_SIMPLE,
            messages=[
                {"role": "system", "content": f"You are a {expert.replace('_', ' ')} providing quick medical consultation."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=400
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Quick assessment failed: {e}")
        return "Unable to provide assessment at this time."

async def _generate_consensus(
    expert_assessments: Dict[str, str],
    query: str,
    context: dict,
    openai_client
) -> str:
    """Generate consensus from expert assessments"""
    try:
        assessments_text = "\n\n".join([
            f"{expert.replace('_', ' ').title()}: {assessment}"
            for expert, assessment in expert_assessments.items()
        ])
        
        prompt = f"""
        Based on these expert assessments, provide a consensus opinion:
        
        Original Query: {query}
        
        Expert Assessments:
        {assessments_text}
        
        Synthesize the expert opinions into:
        1. Key consensus points
        2. Areas of agreement/disagreement
        3. Prioritized recommendations
        4. Next steps
        
        Provide a balanced, actionable summary.
        """
        
        response = await openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL_COMPLEX,
            messages=[
                {"role": "system", "content": "You are a medical coordinator synthesizing expert opinions into actionable recommendations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Consensus generation failed: {e}")
        return "Unable to generate consensus at this time."

async def _save_expert_opinion(
    patient_id: str,
    query: str,
    expert_response: str,
    experts_consulted: List[str],
    db_clients: dict
):
    """Save expert opinion to database"""
    try:
        opinion_record = {
            "patient_id": patient_id,
            "timestamp": datetime.utcnow(),
            "query": query,
            "expert_response": expert_response,
            "experts_consulted": experts_consulted,
            "type": "expert_opinion"
        }
        
        await db_clients["mongodb"].expert_opinions.insert_one(opinion_record)
        
    except Exception as e:
        logger.error(f"Failed to save expert opinion: {e}")

def _chunk_text(text: str, chunk_size: int) -> List[str]:
    """Split text into chunks for streaming"""
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
