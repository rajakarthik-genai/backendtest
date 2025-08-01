"""
Expert Consultation Crew for multi-specialist medical consultations.
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from src.utils.logging import logger


class ExpertConsultationCrew:
    """Crew for coordinating multi-specialist medical consultations."""
    
    def __init__(self):
        self.name = "ExpertConsultationCrew"
        self.specialists = [
            "cardiology", "endocrinology", "neurology", "orthopedics", 
            "dermatology", "gastroenterology", "pulmonology", "nephrology",
            "rheumatology", "oncology", "psychiatry", "pediatrics",
            "geriatrics", "emergency_medicine", "general_medicine"
        ]
        logger.info(f"Initialized {self.name} with {len(self.specialists)} specialists")
    
    async def process_consultation(
        self,
        patient_id: str,
        conversation_id: str,
        message: str,
        specialties: Optional[List[str]] = None,
        context: Dict[str, Any] = None,
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """Process a consultation request with multiple specialists."""
        try:
            logger.info(f"Processing consultation for patient {patient_id[:8]} with specialties: {specialties}")
            
            # Determine which specialists to consult
            if not specialties:
                specialties = await self._determine_relevant_specialties(message, context)
            
            # Get individual specialist opinions
            specialist_opinions = []
            for specialty in specialties:
                opinion = await self._get_specialist_opinion(
                    specialty, message, context, patient_id, priority
                )
                specialist_opinions.append(opinion)
            
            # Aggregate opinions
            aggregated_response = await self._aggregate_opinions(specialist_opinions, message)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence(specialist_opinions)
            
            return {
                "specialist_opinions": specialist_opinions,
                "aggregated_response": aggregated_response,
                "consulted_specialties": specialties,
                "confidence_score": confidence_score,
                "conversation_id": conversation_id,
                "summary": {
                    "total_specialists": len(specialist_opinions),
                    "priority": priority,
                    "processed_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to process consultation: {e}")
            return {
                "specialist_opinions": [],
                "aggregated_response": "I apologize, but I encountered an error while processing your consultation request. Please try again or contact support.",
                "consulted_specialties": specialties or [],
                "confidence_score": 0.0,
                "conversation_id": conversation_id,
                "error": str(e)
            }
    
    async def _determine_relevant_specialties(self, message: str, context: Dict[str, Any]) -> List[str]:
        """Use LLM to dynamically determine relevant specialties."""
        from openai import AsyncOpenAI
        from src.core.config import settings
        
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        specialty_prompt = f"""
You are a medical triage specialist. Analyze the patient query and determine which medical specialties should be consulted.

Available specialties: {', '.join(self.specialists)}

Patient Query: "{message}"

Context: {json.dumps(context.get('user_profile', {}), indent=2) if context else 'None'}

Return ONLY a JSON array of 1-3 most relevant specialties, e.g., ["cardiology", "neurology"]
If unsure, include "general_medicine".
"""
        
        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": specialty_prompt}],
                temperature=0.1,
                max_tokens=100
            )
            
            result = response.choices[0].message.content.strip()
            specialties = json.loads(result)
            
            # Validate specialties
            valid_specialties = [s for s in specialties if s in self.specialists]
            return valid_specialties[:3] if valid_specialties else ["general_medicine"]
            
        except Exception as e:
            logger.error(f"LLM specialty selection failed: {e}")
            return ["general_medicine"]
    
    async def _get_specialist_opinion(
        self,
        specialty: str,
        message: str,
        context: Dict[str, Any],
        patient_id: str,
        priority: str
    ) -> Dict[str, Any]:
        """Get opinion from a specific medical specialist."""
        try:
            # Simulate specialist analysis
            await asyncio.sleep(0.1)  # Simulate processing time
            
            # Generate specialist-specific response
            opinion = await self._generate_specialist_opinion(specialty, message, context)
            
            return {
                "specialist": specialty,
                "opinion": opinion,
                "confidence": 0.8,
                "priority": priority,
                "timestamp": datetime.utcnow().isoformat(),
                "specialist_credentials": f"Board-certified {specialty.replace('_', ' ')} specialist"
            }
            
        except Exception as e:
            logger.error(f"Failed to get {specialty} opinion: {e}")
            return {
                "specialist": specialty,
                "opinion": f"I apologize, but I encountered an error while analyzing this case from a {specialty} perspective.",
                "confidence": 0.0,
                "priority": priority,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    async def _generate_specialist_opinion(self, specialty: str, message: str, context: Dict[str, Any]) -> str:
        """Generate LLM-driven specialist opinion."""
        from openai import AsyncOpenAI
        from src.core.config import settings
        
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Build context string
        context_str = ""
        if context:
            if context.get('user_profile'):
                context_str += f"Patient Profile: {json.dumps(context['user_profile'], indent=2)}\n"
            if context.get('medical_history'):
                context_str += f"Medical History: {context['medical_history'][:500]}\n"
            if context.get('current_body_part_status'):
                context_str += f"Current Health Status: {context['current_body_part_status']}\n"
        
        specialist_prompt = f"""
You are a board-certified {specialty.replace('_', ' ')} specialist providing a medical consultation.

Patient Query: "{message}"

{context_str if context_str else 'No additional context available.'}

Provide a professional medical opinion from your specialty perspective. Include:
1. Assessment of the case from your specialty viewpoint
2. Relevant considerations and risk factors
3. Recommended next steps or referrals
4. Any red flags or urgent concerns

Keep response concise (2-3 paragraphs) and professional. Always recommend consulting healthcare providers for proper diagnosis and treatment.
"""
        
        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": specialist_prompt}],
                temperature=0.3,
                max_tokens=400
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"LLM opinion generation failed for {specialty}: {e}")
            return f"From a {specialty.replace('_', ' ')} perspective, this case requires careful consideration. I recommend consulting with a qualified healthcare provider for proper evaluation and treatment planning."
    
    async def _aggregate_opinions(self, specialist_opinions: List[Dict[str, Any]], original_message: str) -> str:
        """Use LLM to intelligently aggregate specialist opinions."""
        from openai import AsyncOpenAI
        from src.core.config import settings
        
        try:
            if not specialist_opinions:
                return "I apologize, but I was unable to obtain specialist opinions for your case. Please try again or consult with a healthcare provider directly."
            
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            
            # Prepare opinions for aggregation
            opinions_text = "\n\n".join([
                f"**{op['specialist'].replace('_', ' ').title()} (Confidence: {op['confidence']}):**\n{op['opinion']}"
                for op in specialist_opinions
            ])
            
            aggregation_prompt = f"""
You are a medical case coordinator synthesizing multiple specialist opinions into a comprehensive assessment.

Original Patient Query: "{original_message}"

Specialist Opinions:
{opinions_text}

Synthesize these opinions into a cohesive, comprehensive response that:
1. Identifies common themes and consensus points
2. Highlights any conflicting opinions and explains why
3. Provides clear, actionable next steps
4. Maintains appropriate medical disclaimers
5. Prioritizes urgent concerns if any

Structure your response with clear sections and maintain a professional, reassuring tone.
"""
            
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": aggregation_prompt}],
                temperature=0.2,
                max_tokens=800
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"LLM aggregation failed: {e}")
            return "I apologize, but I encountered an error while aggregating the specialist opinions. Please consult with a healthcare provider directly."
    
    def _calculate_confidence(self, specialist_opinions: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence score based on specialist opinions."""
        if not specialist_opinions:
            return 0.0
        
        # Calculate average confidence from specialists
        total_confidence = sum(opinion.get("confidence", 0.0) for opinion in specialist_opinions)
        average_confidence = total_confidence / len(specialist_opinions)
        
        # Adjust based on number of specialists consulted
        if len(specialist_opinions) >= 3:
            confidence_boost = 0.1
        elif len(specialist_opinions) >= 2:
            confidence_boost = 0.05
        else:
            confidence_boost = 0.0
        
        return min(1.0, average_confidence + confidence_boost) 