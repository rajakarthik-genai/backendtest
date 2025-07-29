"""
Chat Agent - Conversational medical assistant for chat endpoints.

This agent handles natural conversation flow, maintains context,
and provides appropriate medical guidance through chat interactions.
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, AsyncGenerator
from openai import AsyncOpenAI

from src.core.config import settings
from src.utils.logging import logger
from src.agents.orchestrator_agent import get_orchestrator
from src.chat.long_term import get_long_term_memory
from src.chat.short_term import get_short_term_memory


class ChatAgent:
    """
    Conversational medical assistant for chat interactions.
    
    Handles natural conversation flow, context management,
    and appropriate medical guidance through chat.
    """
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        """Get the chat agent system prompt."""
        return """You are MediTwin Chat, a conversational medical assistant designed to provide helpful, accurate, and empathetic healthcare guidance.

CORE IDENTITY:
- Friendly, professional medical assistant
- Knowledgeable about general health topics
- Empathetic and supportive in communication
- Safety-focused with appropriate medical disclaimers

CONVERSATION STYLE:
- Natural, conversational tone
- Ask clarifying questions when needed
- Show empathy for patient concerns
- Explain medical concepts in simple terms
- Maintain professional boundaries

CAPABILITIES:
- General health information and education
- Symptom discussion and guidance
- Medication information (general)
- Lifestyle and wellness advice
- Mental health support and resources
- Preventive care recommendations

SAFETY PROTOCOLS:
- Always recommend consulting healthcare providers for diagnosis/treatment
- Identify emergency situations requiring immediate medical attention
- Never provide specific diagnoses or prescribe medications
- Acknowledge limitations and refer to specialists when appropriate
- Maintain patient privacy and confidentiality

EMERGENCY RECOGNITION:
- Chest pain, difficulty breathing, severe bleeding
- Signs of stroke (FAST assessment)
- Severe allergic reactions
- Suicidal ideation or self-harm
- Severe trauma or injuries
- Loss of consciousness or altered mental status

CONVERSATION FLOW:
1. Greet warmly and ask how you can help
2. Listen actively to patient concerns
3. Ask relevant follow-up questions
4. Provide appropriate information and guidance
5. Suggest next steps (self-care, provider visit, emergency care)
6. Offer additional support or resources

LIMITATIONS:
- Cannot diagnose medical conditions
- Cannot prescribe medications
- Cannot replace professional medical care
- Cannot access patient medical records directly
- Cannot provide emergency medical treatment

REFERRAL GUIDELINES:
- Urgent symptoms → Emergency care immediately
- Complex symptoms → Healthcare provider consultation
- Specialist concerns → Appropriate specialist referral
- Mental health issues → Mental health professional
- Chronic conditions → Primary care provider

Remember: You are a supportive guide, not a replacement for professional medical care. Always prioritize patient safety and appropriate care escalation."""

    async def process_chat_message(
        self,
        patient_id: str,
        session_id: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a chat message and return appropriate response.
        
        Args:
            patient_id: Patient identifier
            session_id: Chat session identifier
            message: User's message
            context: Optional conversation context
            
        Returns:
            Chat response with content and metadata
        """
        try:
            # Check for emergency keywords
            if self._is_emergency(message):
                return await self._handle_emergency_response(message)
            
            # Check if this needs specialist consultation
            if self._needs_specialist_consultation(message):
                return await self._route_to_specialists(patient_id, session_id, message, context)
            
            # Handle as general chat
            return await self._handle_general_chat(patient_id, session_id, message, context)
            
        except Exception as e:
            logger.error(f"Chat processing failed: {e}")
            return {
                "content": "I apologize, but I encountered an error processing your message. Please try again or contact support if the issue persists.",
                "type": "error",
                "metadata": {"error": str(e)}
            }
    
    async def stream_chat_response(
        self,
        patient_id: str,
        session_id: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream chat response for real-time interaction.
        
        Args:
            patient_id: Patient identifier
            session_id: Chat session identifier
            message: User's message
            context: Optional conversation context
            
        Yields:
            Response chunks for streaming
        """
        try:
            # Check for emergency
            if self._is_emergency(message):
                emergency_response = await self._handle_emergency_response(message)
                yield {
                    "type": "content",
                    "content": emergency_response["content"],
                    "metadata": emergency_response.get("metadata", {})
                }
                return
            
            # Check if needs specialist consultation
            if self._needs_specialist_consultation(message):
                yield {"type": "metadata", "content": "Consulting medical specialists..."}
                
                orchestrator = await get_orchestrator()
                async for chunk in orchestrator.stream_response(patient_id, session_id, message):
                    yield chunk
                return
            
            # Stream general chat response
            async for chunk in self._stream_general_chat(patient_id, session_id, message, context):
                yield chunk
                
        except Exception as e:
            logger.error(f"Chat streaming failed: {e}")
            yield {
                "type": "error",
                "content": "I encountered an error. Please try again.",
                "error": str(e)
            }
    
    def _is_emergency(self, message: str) -> bool:
        """Check if message indicates medical emergency."""
        emergency_keywords = [
            "chest pain", "can't breathe", "difficulty breathing", "choking",
            "severe bleeding", "unconscious", "stroke", "heart attack",
            "suicide", "kill myself", "overdose", "severe allergic reaction",
            "anaphylaxis", "severe trauma", "broken bone", "head injury",
            "seizure", "convulsion", "emergency", "911", "ambulance"
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in emergency_keywords)
    
    def _needs_specialist_consultation(self, message: str) -> bool:
        """Check if message needs specialist consultation."""
        specialist_indicators = [
            "diagnosis", "diagnose", "what do I have", "medical opinion",
            "specialist", "doctor", "treatment plan", "medication",
            "test results", "lab results", "imaging", "x-ray", "mri",
            "symptoms", "pain", "condition", "disease", "illness"
        ]
        
        message_lower = message.lower()
        return any(indicator in message_lower for indicator in specialist_indicators)
    
    async def _handle_emergency_response(self, message: str) -> Dict[str, Any]:
        """Handle emergency situations with immediate guidance."""
        return {
            "content": """🚨 **MEDICAL EMERGENCY DETECTED** 🚨

If you are experiencing a medical emergency, please:

**CALL 911 IMMEDIATELY** or go to your nearest emergency room.

For immediate assistance:
- **US/Canada**: 911
- **UK**: 999
- **EU**: 112

**Do not wait** - seek immediate medical attention.

If you're having thoughts of self-harm:
- **National Suicide Prevention Lifeline**: 988
- **Crisis Text Line**: Text HOME to 741741

I'm an AI assistant and cannot provide emergency medical care. Please contact emergency services immediately.""",
            "type": "emergency",
            "metadata": {
                "emergency_detected": True,
                "timestamp": datetime.utcnow().isoformat(),
                "requires_immediate_action": True
            }
        }
    
    async def _route_to_specialists(
        self,
        patient_id: str,
        session_id: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Route message to specialist consultation."""
        try:
            orchestrator = await get_orchestrator()
            response = await orchestrator.process_user_message(patient_id, session_id, message)
            
            return {
                "content": response.get("content", ""),
                "type": "specialist_consultation",
                "metadata": {
                    "routed_to_specialists": True,
                    "timestamp": datetime.utcnow().isoformat(),
                    **response.get("metadata", {})
                }
            }
            
        except Exception as e:
            logger.error(f"Specialist routing failed: {e}")
            return {
                "content": "I'd like to connect you with our medical specialists for a more detailed consultation, but I'm experiencing technical difficulties. Please try again or contact your healthcare provider.",
                "type": "error",
                "metadata": {"routing_error": str(e)}
            }
    
    async def _handle_general_chat(
        self,
        patient_id: str,
        session_id: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle general conversational chat."""
        try:
            # Get conversation history
            stm = await get_short_term_memory()
            chat_history = await stm.get_context(patient_id, session_id)
            
            # Build conversation messages
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add context if available
            if context and context.get("user_profile"):
                context_str = f"Patient context: {json.dumps(context['user_profile'], indent=2)}"
                messages.append({"role": "system", "content": context_str})
            
            # Add recent chat history
            if chat_history.get("recent_messages"):
                for msg in chat_history["recent_messages"][-5:]:  # Last 5 messages
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Generate response
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            return {
                "content": content,
                "type": "general_chat",
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "model_used": "gpt-4o",
                    "conversation_type": "general"
                }
            }
            
        except Exception as e:
            logger.error(f"General chat failed: {e}")
            return {
                "content": "I'm here to help with your health questions. Could you please rephrase your question or let me know how I can assist you?",
                "type": "fallback",
                "metadata": {"error": str(e)}
            }
    
    async def _stream_general_chat(
        self,
        patient_id: str,
        session_id: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream general chat response."""
        try:
            # Get conversation history
            stm = await get_short_term_memory()
            chat_history = await stm.get_context(patient_id, session_id)
            
            # Build messages
            messages = [{"role": "system", "content": self.system_prompt}]
            
            if context and context.get("user_profile"):
                context_str = f"Patient context: {json.dumps(context['user_profile'], indent=2)}"
                messages.append({"role": "system", "content": context_str})
            
            if chat_history.get("recent_messages"):
                for msg in chat_history["recent_messages"][-5:]:
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })
            
            messages.append({"role": "user", "content": message})
            
            # Stream response
            stream = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.7,
                max_tokens=500,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield {
                        "type": "content",
                        "content": chunk.choices[0].delta.content,
                        "metadata": {"streaming": True}
                    }
            
            yield {
                "type": "complete",
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "conversation_type": "general"
                }
            }
            
        except Exception as e:
            logger.error(f"General chat streaming failed: {e}")
            yield {
                "type": "error",
                "content": "I encountered an error while responding. Please try again.",
                "error": str(e)
            }


# Factory function
def get_chat_agent() -> ChatAgent:
    """Get a chat agent instance."""
    return ChatAgent()

# Default instance
chat_agent = ChatAgent()