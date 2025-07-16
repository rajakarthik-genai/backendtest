"""
Main orchestrator agent for coordinating medical specialist agents.

Features:
- Routes user queries to appropriate specialist agents
- Coordinates multi-agent responses
- Streams aggregated results to users
- Manages conversation context and memory
"""

import json
import uuid
from datetime import datetime
from typing import AsyncGenerator, Dict, List, Any, Optional

from src.config.settings import settings
from src.utils.logging import logger, log_user_action
from src.agents.expert_router import get_expert_router
from src.agents.aggregator_agent import get_aggregator
from src.chat.short_term import get_short_term_memory
from src.chat.long_term import get_long_term_memory
from src.db.redis_db import get_redis
from src.db.mongo_db import get_mongo
from src.prompts import get_agent_prompt


class OrchestratorAgent:
    """
    Main orchestrator that coordinates specialist medical agents.
    
    Workflow:
    1. Analyzes user query for medical domains
    2. Routes to appropriate specialist agents
    3. Aggregates multiple responses if needed
    4. Streams results back to user
    """

    def __init__(self):
        """Initialize the orchestrator with system prompt."""
        self.system_prompt = self._get_system_prompt()
        self.model = settings.openai_model_chat
        self.session_contexts = {}  # Cache for session contexts
    
    def _get_system_prompt(self) -> str:
        """Get the orchestrator system prompt."""
        try:
            return get_agent_prompt("orchestrator")
        except Exception as e:
            logger.warning(f"Failed to load orchestrator prompt: {e}")
            # Fallback prompt
            return """You are the Orchestrator Agent, central coordinator for medical specialist agents.
            
Your role:
- Analyze user queries to determine which medical specialists are needed
- Route queries to cardiologist, neurologist, orthopedist, or general physician
- Coordinate responses and invoke aggregator when multiple specialists respond
- Never provide direct medical advice - always route to specialists

Available functions: cardiologist(query), neurologist(query), orthopedist(query), general_physician(query), aggregator(answers)
"""

    async def process_user_message(
        self,
        patient_id: str,
        session_id: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Process a user message and return a complete response.
        
        Used for non-streaming endpoints.
        """
        try:
            # Get conversation context
            context = await self._get_conversation_context(patient_id, session_id)
            
            # Route to appropriate specialists
            router = await get_expert_router()
            specialists = await router.select_specialists(message, context)
            
            logger.info(f"Selected specialists: {[s['type'] for s in specialists]}")
            
            # Gather specialist responses
            specialist_responses = []
            for specialist_info in specialists:
                try:
                    specialist = specialist_info['agent']
                    response = await specialist.analyze_query(
                        patient_id=patient_id,
                        query=message,
                        context=context
                    )
                    specialist_responses.append({
                        "specialist_type": specialist_info['type'],
                        "response": response,
                        "confidence": specialist_info.get('confidence', 0.8)
                    })
                except Exception as e:
                    logger.error(f"Specialist {specialist_info['type']} failed: {e}")
                    continue
            
            # Aggregate responses
            aggregator = await get_aggregator()
            final_response = await aggregator.synthesize_response(
                user_query=message,
                specialist_responses=specialist_responses,
                context=context
            )
            
            # Log interaction
            log_user_action(
                patient_id,
                "orchestrator_response",
                {
                    "session_id": session_id,
                    "specialists_used": len(specialist_responses),
                    "response_length": len(final_response.get("content", ""))
                }
            )
            
            return final_response
            
        except Exception as e:
            logger.error(f"Orchestrator processing failed: {e}")
            return {
                "content": "I apologize, but I encountered an error processing your request. Please try again.",
                "metadata": {"error": True, "message": str(e)}
            }
    
    async def stream_response(
        self,
        patient_id: str,
        session_id: str,
        message: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream response chunks for real-time user experience.
        
        Yields chunks with type and content for progressive display.
        """
        try:
            # Send initial status
            yield {
                "type": "metadata",
                "content": "Analyzing your query...",
                "session_id": session_id
            }
            
            # Get conversation context
            context = await self._get_conversation_context(patient_id, session_id)
            
            # Route to specialists
            yield {
                "type": "metadata", 
                "content": "Selecting medical specialists..."
            }
            
            router = await get_expert_router()
            specialists = await router.select_specialists(message, context)
            
            specialist_names = [s['type'].replace('_', ' ').title() for s in specialists]
            yield {
                "type": "metadata",
                "content": f"Consulting: {', '.join(specialist_names)}"
            }
            
            # Stream specialist responses
            specialist_responses = []
            
            for i, specialist_info in enumerate(specialists):
                try:
                    specialist_type = specialist_info['type']
                    specialist = specialist_info['agent']
                    
                    yield {
                        "type": "metadata",
                        "content": f"Getting insights from {specialist_type.replace('_', ' ').title()}..."
                    }
                    
                    # Get specialist response
                    response = await specialist.analyze_query(
                        patient_id=patient_id,
                        query=message,
                        context=context
                    )
                    
                    specialist_responses.append({
                        "specialist_type": specialist_type,
                        "response": response,
                        "confidence": specialist_info.get('confidence', 0.8)
                    })
                    
                    # Stream partial insights
                    yield {
                        "type": "partial_insight",
                        "content": f"**{specialist_type.replace('_', ' ').title()}**: {response.get('summary', '')[:100]}...",
                        "specialist": specialist_type
                    }
                    
                except Exception as e:
                    logger.error(f"Specialist {specialist_info.get('type', 'unknown')} failed: {e}")
                    yield {
                        "type": "metadata",
                        "content": f"Specialist consultation failed, continuing with others..."
                    }
                    continue
            
            # Aggregate and stream final response
            yield {
                "type": "metadata",
                "content": "Synthesizing medical insights..."
            }
            
            aggregator = await get_aggregator()
            
            # Stream aggregated response
            async for chunk in aggregator.stream_synthesis(
                user_query=message,
                specialist_responses=specialist_responses,
                context=context
            ):
                yield chunk
            
            # Log interaction
            log_user_action(
                patient_id,
                "orchestrator_stream",
                {
                    "session_id": session_id,
                    "specialists_used": len(specialist_responses),
                    "streaming": True
                }
            )
            
        except Exception as e:
            logger.error(f"Orchestrator streaming failed: {e}")
            yield {
                "type": "error",
                "content": "I apologize, but I encountered an error. Please try again.",
                "error": str(e)
            }
    
    async def _get_conversation_context(
        self,
        patient_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Gather conversation context including history and user medical data.
        
        Args:
            patient_id: User identifier
            session_id: Session identifier
            
        Returns:
            Context dictionary with history, medical data, etc.
        """
        try:
            # Check cache first
            cache_key = f"{user_id}:{session_id}"
            if cache_key in self.session_contexts:
                cached_context = self.session_contexts[cache_key]
                # Return cached context if recent (within 5 minutes)
                if (datetime.utcnow() - cached_context["timestamp"]).seconds < 300:
                    return cached_context["context"]
            
            # Get chat history
            redis_client = get_redis()
            chat_history = redis_client.get_chat_history(user_id, session_id, limit=10)
            
            # Get short-term memory
            stm = await get_short_term_memory()
            short_term_context = await stm.get_context(user_id, session_id)
            
            # Get long-term memory (medical history)
            ltm = await get_long_term_memory()
            medical_context = await ltm.get_user_context(user_id)
            
            # Get recent medical records
            mongo_client = await get_mongo()
            recent_records = await mongo_client.get_medical_records(user_id, limit=10)
            
            # Get current body part severities from Neo4j
            try:
                neo4j_client = get_graph()
                body_part_severities = neo4j_client.get_body_part_severities(user_id)
                # Filter to only show non-normal severities
                active_conditions = {
                    bp: severity for bp, severity in body_part_severities.items()
                    if severity and severity.lower() not in ['na', 'normal']
                }
            except Exception as e:
                logger.warning(f"Could not retrieve body part severities: {e}")
                active_conditions = {}
            
            # Build context
            context = {
                "patient_id": patient_id,
                "session_id": session_id,
                "chat_history": chat_history,
                "short_term_memory": short_term_context,
                "user_profile": medical_context.get("user_profile", {}),
                "medical_history": medical_context.get("medical_history", []),
                "preferences": medical_context.get("preferences", {}),
                "current_body_part_status": active_conditions,
                "recent_records": recent_records,
                "timestamp": datetime.utcnow()
            }
            
            # Cache context
            self.session_contexts[cache_key] = {
                "context": context,
                "timestamp": datetime.utcnow()
            }
            
            # Clean old cache entries (keep only last 100)
            if len(self.session_contexts) > 100:
                oldest_key = min(
                    self.session_contexts.keys(),
                    key=lambda k: self.session_contexts[k]["timestamp"]
                )
                del self.session_contexts[oldest_key]
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to get conversation context: {e}")
            return {
                "patient_id": patient_id,
                "session_id": session_id,
                "chat_history": [],
                "short_term_memory": {},
                "medical_history": {},
                "recent_records": [],
                "timestamp": datetime.utcnow(),
                "error": str(e)
            }
    
    async def clear_session_cache(self, patient_id: str, session_id: str = None):
        """Clear cached session context."""
        if session_id:
            cache_key = f"{user_id}:{session_id}"
            self.session_contexts.pop(cache_key, None)
        else:
            # Clear all sessions for user
            keys_to_remove = [
                k for k in self.session_contexts.keys() 
                if k.startswith(f"{user_id}:")
            ]
            for key in keys_to_remove:
                del self.session_contexts[key]


# Global orchestrator instance for module-level access
_orchestrator: Optional[OrchestratorAgent] = None

async def get_orchestrator() -> OrchestratorAgent:
    """Get the global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = OrchestratorAgent()
    return _orchestrator

# Global instance for backward compatibility
orchestrator_agent = OrchestratorAgent()
