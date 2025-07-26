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
                specialties = self._determine_relevant_specialties(message, context)
            
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
    
    def _determine_relevant_specialties(self, message: str, context: Dict[str, Any]) -> List[str]:
        """Determine which specialties are relevant based on the message and context."""
        message_lower = message.lower()
        relevant_specialties = []
        
        # Simple keyword-based specialty selection
        specialty_keywords = {
            "cardiology": ["heart", "cardiac", "chest pain", "cardiovascular", "blood pressure", "hypertension"],
            "endocrinology": ["diabetes", "thyroid", "hormone", "insulin", "blood sugar", "endocrine"],
            "neurology": ["brain", "headache", "seizure", "stroke", "nervous system", "neurological"],
            "orthopedics": ["bone", "joint", "fracture", "arthritis", "muscle", "skeletal"],
            "dermatology": ["skin", "rash", "acne", "dermatological", "lesion", "mole"],
            "gastroenterology": ["stomach", "digestive", "nausea", "vomiting", "abdominal", "gastrointestinal"],
            "pulmonology": ["lung", "breathing", "respiratory", "cough", "asthma", "pneumonia"],
            "nephrology": ["kidney", "renal", "urinary", "dialysis", "nephrological"],
            "rheumatology": ["arthritis", "rheumatoid", "autoimmune", "joint pain", "inflammation"],
            "oncology": ["cancer", "tumor", "oncology", "malignant", "chemotherapy"],
            "psychiatry": ["mental", "depression", "anxiety", "psychiatric", "mood", "behavior"],
            "pediatrics": ["child", "pediatric", "infant", "baby", "adolescent"],
            "geriatrics": ["elderly", "aging", "geriatric", "senior", "old age"],
            "emergency_medicine": ["emergency", "urgent", "acute", "trauma", "critical"],
            "general_medicine": ["general", "primary care", "overall health", "wellness"]
        }
        
        for specialty, keywords in specialty_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                relevant_specialties.append(specialty)
        
        # If no specific specialties found, default to general medicine
        if not relevant_specialties:
            relevant_specialties = ["general_medicine"]
        
        # Limit to top 3 most relevant
        return relevant_specialties[:3]
    
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
            opinion = self._generate_specialist_opinion(specialty, message, context)
            
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
    
    def _generate_specialist_opinion(self, specialty: str, message: str, context: Dict[str, Any]) -> str:
        """Generate a specialist-specific opinion."""
        message_lower = message.lower()
        
        # Generate specialty-specific responses
        if specialty == "cardiology":
            if any(word in message_lower for word in ["chest pain", "heart", "cardiac"]):
                return "From a cardiology perspective, chest pain requires immediate evaluation. I recommend seeking emergency medical attention to rule out acute coronary syndrome. Key considerations include the nature, duration, and associated symptoms of the pain."
            else:
                return "From a cardiology standpoint, I don't see any immediate cardiac concerns in this case. However, regular cardiovascular health monitoring is always recommended."
        
        elif specialty == "neurology":
            if any(word in message_lower for word in ["headache", "brain", "seizure", "stroke"]):
                return "From a neurological perspective, this case requires careful evaluation. I would recommend a thorough neurological examination and potentially imaging studies to assess for any underlying neurological conditions."
            else:
                return "From a neurological standpoint, I don't identify any immediate neurological concerns. Regular neurological health monitoring is recommended."
        
        elif specialty == "endocrinology":
            if any(word in message_lower for word in ["diabetes", "thyroid", "hormone", "blood sugar"]):
                return "From an endocrinology perspective, this case suggests potential endocrine system involvement. I recommend comprehensive metabolic testing and hormone level evaluation to assess endocrine function."
            else:
                return "From an endocrinology standpoint, I don't see any immediate endocrine concerns. Regular metabolic health monitoring is recommended."
        
        elif specialty == "pulmonology":
            if any(word in message_lower for word in ["breathing", "lung", "cough", "respiratory"]):
                return "From a pulmonology perspective, respiratory symptoms require careful evaluation. I recommend pulmonary function testing and potentially chest imaging to assess respiratory health."
            else:
                return "From a pulmonology standpoint, I don't identify any immediate respiratory concerns. Regular respiratory health monitoring is recommended."
        
        else:
            # General response for other specialties
            return f"From a {specialty.replace('_', ' ')} perspective, this case requires careful consideration. I recommend a thorough evaluation and appropriate diagnostic testing to ensure comprehensive care."
    
    async def _aggregate_opinions(self, specialist_opinions: List[Dict[str, Any]], original_message: str) -> str:
        """Aggregate multiple specialist opinions into a comprehensive response."""
        try:
            if not specialist_opinions:
                return "I apologize, but I was unable to obtain specialist opinions for your case. Please try again or consult with a healthcare provider directly."
            
            # Build aggregated response
            response_parts = [
                "Based on the consultation with multiple medical specialists, here is our comprehensive assessment:",
                "",
                "**Specialist Opinions:**"
            ]
            
            for opinion in specialist_opinions:
                specialist_name = opinion["specialist"].replace("_", " ").title()
                response_parts.append(f"- **{specialist_name}**: {opinion['opinion']}")
            
            response_parts.extend([
                "",
                "**Overall Assessment:**",
                "The specialists have provided their perspectives on your case. While each specialist focuses on their area of expertise, the consensus suggests that your symptoms warrant appropriate medical evaluation.",
                "",
                "**Recommendations:**",
                "1. Schedule an appointment with your primary care physician",
                "2. Consider specialist referrals based on the identified concerns",
                "3. Follow up on any recommended diagnostic tests",
                "4. Maintain regular health monitoring",
                "",
                "**Important Note:** This consultation is for informational purposes only and should not replace professional medical advice. Please consult with qualified healthcare providers for proper diagnosis and treatment."
            ])
            
            return "\n".join(response_parts)
            
        except Exception as e:
            logger.error(f"Failed to aggregate opinions: {e}")
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