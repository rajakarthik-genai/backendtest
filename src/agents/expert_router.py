"""
Expert Router - Intelligent routing of medical questions to appropriate specialists.

This module implements smart routing logic to determine which medical specialists
should be consulted for a given question, using keyword analysis and medical
context understanding.
"""

import re
import asyncio
from typing import List, Dict, Set, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from src.utils.logging import logger
from src.agents.base_specialist import SpecialtyType, BaseSpecialist
from src.agents.general_physician_agent import GeneralPhysicianAgent
from src.agents.cardiologist_agent import CardiologistAgent
from src.agents.neurologist_agent import NeurologistAgent
from src.agents.orthopedist_agent import OrthopedistAgent


@dataclass
class SpecialtyMatch:
    """Represents a match between a question and a medical specialty."""
    specialty: SpecialtyType
    confidence: float
    matched_keywords: List[str]
    reasoning: str


class ExpertRouter:
    """
    Intelligent router for determining appropriate medical specialists.
    
    Uses keyword analysis, medical terminology recognition, and contextual
    understanding to route questions to the most relevant specialists.
    """
    
    def __init__(self):
        """Initialize the expert router with specialty keywords and patterns."""
        self.specialty_keywords = self._initialize_specialty_keywords()
        self.body_part_mapping = self._initialize_body_part_mapping()
        self.symptom_mapping = self._initialize_symptom_mapping()
        self.emergency_keywords = self._initialize_emergency_keywords()
        
        # Initialize specialist agents
        self.specialists = {
            SpecialtyType.GENERAL: GeneralPhysicianAgent(),
            SpecialtyType.CARDIOLOGY: CardiologistAgent(),
            SpecialtyType.NEUROLOGY: NeurologistAgent(),
            SpecialtyType.ORTHOPEDICS: OrthopedistAgent(),
        }
    
    def _initialize_specialty_keywords(self) -> Dict[SpecialtyType, List[str]]:
        """Initialize specialty-specific keywords and terms."""
        return {
            SpecialtyType.CARDIOLOGY: [
                # Primary cardiovascular terms
                "heart", "cardiac", "cardio", "cardiovascular",
                "chest pain", "angina", "palpitation", "palpitations",
                "arrhythmia", "atrial fibrillation", "bradycardia", "tachycardia",
                "hypertension", "blood pressure", "hypotension",
                "myocardial infarction", "heart attack", "MI",
                "coronary", "atherosclerosis", "stenosis",
                "heart failure", "cardiomyopathy", "ejection fraction",
                "valve", "mitral", "aortic", "tricuspid", "pulmonary",
                "ecg", "electrocardiogram", "echocardiogram", "echo",
                "stress test", "cardiac catheterization", "angiogram",
                "stent", "bypass", "pace", "pacemaker", "defibrillator",
                "cholesterol", "lipid", "statin", "triglyceride"
            ],
            
            SpecialtyType.NEUROLOGY: [
                # Neurological terms
                "brain", "neurological", "neuro", "nervous system",
                "headache", "migraine", "tension headache", "cluster headache",
                "seizure", "epilepsy", "convulsion", "fits",
                "stroke", "tia", "transient ischemic attack", "cerebrovascular",
                "memory", "dementia", "alzheimer", "cognitive", "confusion",
                "parkinson", "tremor", "movement disorder", "dystonia",
                "multiple sclerosis", "ms", "demyelinating",
                "neuropathy", "peripheral neuropathy", "carpal tunnel",
                "dizziness", "vertigo", "balance", "ataxia",
                "weakness", "paralysis", "hemiplegia", "paraplegia",
                "numbness", "tingling", "sensation", "sensory",
                "mri brain", "ct brain", "eeg", "lumbar puncture",
                "neuralgia", "sciatica", "radiculopathy"
            ],
            
            SpecialtyType.ORTHOPEDICS: [
                # Musculoskeletal terms
                "bone", "joint", "muscle", "tendon", "ligament",
                "fracture", "break", "broken", "crack", "stress fracture",
                "sprain", "strain", "tear", "rupture",
                "arthritis", "osteoarthritis", "rheumatoid arthritis",
                "back pain", "spine", "spinal", "disc", "herniated",
                "knee", "hip", "shoulder", "elbow", "wrist", "ankle",
                "foot", "hand", "neck", "lumbar", "cervical", "thoracic",
                "acl", "mcl", "meniscus", "rotator cuff",
                "osteoporosis", "osteomyelitis", "bursitis", "tendinitis",
                "scoliosis", "kyphosis", "lordosis",
                "x-ray", "mri joint", "ct bone", "bone scan",
                "physical therapy", "orthopedic", "sports injury",
                "replacement", "prosthesis", "implant", "hardware"
            ],
            
            SpecialtyType.GENERAL: [
                # General medicine terms
                "fever", "temperature", "infection", "flu", "cold",
                "cough", "sore throat", "runny nose", "congestion",
                "nausea", "vomiting", "diarrhea", "constipation",
                "abdominal pain", "stomach", "gastro", "bowel",
                "fatigue", "tired", "exhaustion", "energy",
                "weight loss", "weight gain", "appetite",
                "diabetes", "blood sugar", "glucose", "insulin",
                "thyroid", "hormone", "endocrine", "metabolism",
                "annual exam", "checkup", "screening", "prevention",
                "vaccination", "immunization", "travel medicine",
                "medication", "drug", "prescription", "side effect"
            ]
        }
    
    def _initialize_body_part_mapping(self) -> Dict[str, List[SpecialtyType]]:
        """Map body parts to relevant specialties."""
        return {
            "heart": [SpecialtyType.CARDIOLOGY, SpecialtyType.GENERAL],
            "chest": [SpecialtyType.CARDIOLOGY, SpecialtyType.GENERAL],
            "brain": [SpecialtyType.NEUROLOGY],
            "head": [SpecialtyType.NEUROLOGY, SpecialtyType.GENERAL],
            "neck": [SpecialtyType.ORTHOPEDICS, SpecialtyType.NEUROLOGY],
            "spine": [SpecialtyType.ORTHOPEDICS, SpecialtyType.NEUROLOGY],
            "back": [SpecialtyType.ORTHOPEDICS, SpecialtyType.NEUROLOGY],
            "knee": [SpecialtyType.ORTHOPEDICS],
            "hip": [SpecialtyType.ORTHOPEDICS],
            "shoulder": [SpecialtyType.ORTHOPEDICS],
            "elbow": [SpecialtyType.ORTHOPEDICS],
            "wrist": [SpecialtyType.ORTHOPEDICS],
            "ankle": [SpecialtyType.ORTHOPEDICS],
            "foot": [SpecialtyType.ORTHOPEDICS],
            "hand": [SpecialtyType.ORTHOPEDICS],
            "leg": [SpecialtyType.ORTHOPEDICS, SpecialtyType.NEUROLOGY],
            "arm": [SpecialtyType.ORTHOPEDICS, SpecialtyType.NEUROLOGY]
        }
    
    def _initialize_symptom_mapping(self) -> Dict[str, List[SpecialtyType]]:
        """Map symptoms to relevant specialties."""
        return {
            "chest pain": [SpecialtyType.CARDIOLOGY, SpecialtyType.GENERAL],
            "shortness of breath": [SpecialtyType.CARDIOLOGY, SpecialtyType.GENERAL],
            "palpitations": [SpecialtyType.CARDIOLOGY],
            "headache": [SpecialtyType.NEUROLOGY, SpecialtyType.GENERAL],
            "dizziness": [SpecialtyType.NEUROLOGY, SpecialtyType.CARDIOLOGY],
            "weakness": [SpecialtyType.NEUROLOGY, SpecialtyType.GENERAL],
            "numbness": [SpecialtyType.NEUROLOGY, SpecialtyType.ORTHOPEDICS],
            "pain": [SpecialtyType.ORTHOPEDICS, SpecialtyType.GENERAL],
            "swelling": [SpecialtyType.ORTHOPEDICS, SpecialtyType.CARDIOLOGY],
            "fatigue": [SpecialtyType.GENERAL, SpecialtyType.CARDIOLOGY]
        }
    
    def _initialize_emergency_keywords(self) -> List[str]:
        """Initialize keywords that suggest emergency/urgent care."""
        return [
            "emergency", "urgent", "severe", "acute", "sudden",
            "heart attack", "stroke", "seizure", "unconscious",
            "bleeding", "fracture", "chest pain", "difficulty breathing",
            "cannot move", "paralyzed", "severe pain"
        ]
    
    def route_question(
        self,
        question: str,
        context: Optional[Dict] = None,
        max_specialists: int = 3
    ) -> List[SpecialtyMatch]:
        """
        Route a medical question to appropriate specialists.
        
        Args:
            question: Medical question or case description
            context: Additional context (medical history, etc.)
            max_specialists: Maximum number of specialists to recommend
            
        Returns:
            List of specialty matches ranked by relevance
        """
        try:
            question_lower = question.lower()
            matches = []
            
            # Analyze question for each specialty
            for specialty in SpecialtyType:
                match = self._analyze_specialty_match(specialty, question_lower, context)
                if match.confidence > 0.1:  # Minimum threshold
                    matches.append(match)
            
            # Sort by confidence and limit results
            matches.sort(key=lambda x: x.confidence, reverse=True)
            
            # Ensure general physician is included if no high-confidence matches
            if not matches or max(m.confidence for m in matches) < 0.6:
                general_match = self._create_general_match(question_lower)
                if not any(m.specialty == SpecialtyType.GENERAL for m in matches):
                    matches.append(general_match)
            
            # Re-sort and limit
            matches.sort(key=lambda x: x.confidence, reverse=True)
            return matches[:max_specialists]
            
        except Exception as e:
            logger.error(f"Error routing question: {e}")
            # Fallback to general physician
            return [self._create_general_match(question)]
    
    def _analyze_specialty_match(
        self,
        specialty: SpecialtyType,
        question_lower: str,
        context: Optional[Dict] = None
    ) -> SpecialtyMatch:
        """Analyze how well a question matches a specific specialty."""
        
        keywords = self.specialty_keywords.get(specialty, [])
        matched_keywords = []
        confidence = 0.0
        
        # Direct keyword matching
        for keyword in keywords:
            if keyword in question_lower:
                matched_keywords.append(keyword)
                # Weight longer, more specific keywords higher
                confidence += len(keyword.split()) * 0.1
        
        # Body part analysis
        for body_part, specialties in self.body_part_mapping.items():
            if body_part in question_lower and specialty in specialties:
                confidence += 0.15
                matched_keywords.append(f"body_part:{body_part}")
        
        # Symptom analysis
        for symptom, specialties in self.symptom_mapping.items():
            if symptom in question_lower and specialty in specialties:
                confidence += 0.2
                matched_keywords.append(f"symptom:{symptom}")
        
        # Context analysis
        if context:
            confidence += self._analyze_context_match(specialty, context)
        
        # Emergency keyword boost
        emergency_boost = any(kw in question_lower for kw in self.emergency_keywords)
        if emergency_boost and specialty == SpecialtyType.GENERAL:
            confidence += 0.3
        
        # Specialty-specific adjustments
        confidence = self._apply_specialty_adjustments(specialty, question_lower, confidence)
        
        # Normalize confidence to 0-1 range
        confidence = min(1.0, confidence)
        
        reasoning = self._generate_routing_reasoning(specialty, matched_keywords, confidence)
        
        return SpecialtyMatch(
            specialty=specialty,
            confidence=confidence,
            matched_keywords=matched_keywords,
            reasoning=reasoning
        )
    
    def _analyze_context_match(self, specialty: SpecialtyType, context: Dict) -> float:
        """Analyze context for specialty relevance."""
        boost = 0.0
        
        # Medical history analysis
        if "medical_history" in context:
            history = context["medical_history"]
            for record in history[:5]:  # Check recent records
                record_text = str(record).lower()
                keywords = self.specialty_keywords.get(specialty, [])
                if any(kw in record_text for kw in keywords):
                    boost += 0.1
        
        return min(0.3, boost)  # Cap context boost
    
    def _apply_specialty_adjustments(
        self,
        specialty: SpecialtyType,
        question_lower: str,
        base_confidence: float
    ) -> float:
        """Apply specialty-specific confidence adjustments."""
        
        # Cardiology adjustments
        if specialty == SpecialtyType.CARDIOLOGY:
            if any(term in question_lower for term in ["chest pain", "heart attack", "cardiac"]):
                base_confidence += 0.2
        
        # Neurology adjustments
        elif specialty == SpecialtyType.NEUROLOGY:
            if any(term in question_lower for term in ["headache", "seizure", "stroke"]):
                base_confidence += 0.2
        
        # Orthopedics adjustments
        elif specialty == SpecialtyType.ORTHOPEDICS:
            if any(term in question_lower for term in ["fracture", "joint pain", "back pain"]):
                base_confidence += 0.2
        
        # General physician adjustments
        elif specialty == SpecialtyType.GENERAL:
            # Boost for general symptoms or when no specific specialty is clear
            if any(term in question_lower for term in ["fever", "fatigue", "general", "overall"]):
                base_confidence += 0.15
        
        return base_confidence
    
    def _create_general_match(self, question: str) -> SpecialtyMatch:
        """Create a default general physician match."""
        return SpecialtyMatch(
            specialty=SpecialtyType.GENERAL,
            confidence=0.5,
            matched_keywords=["general_medicine"],
            reasoning="General physician consultation recommended for comprehensive assessment"
        )
    
    def _generate_routing_reasoning(
        self,
        specialty: SpecialtyType,
        matched_keywords: List[str],
        confidence: float
    ) -> str:
        """Generate human-readable reasoning for the routing decision."""
        
        if not matched_keywords:
            return f"Low relevance to {specialty.value}"
        
        keyword_str = ", ".join(matched_keywords[:3])
        
        if confidence > 0.7:
            return f"High relevance to {specialty.value} based on: {keyword_str}"
        elif confidence > 0.4:
            return f"Moderate relevance to {specialty.value} based on: {keyword_str}"
        else:
            return f"Low relevance to {specialty.value} based on: {keyword_str}"
    
    async def get_specialists(
        self,
        question: str,
        context: Optional[Dict] = None,
        max_specialists: int = 3
    ) -> List[BaseSpecialist]:
        """
        Get specialist agent instances for a question.
        
        Args:
            question: Medical question
            context: Additional context
            max_specialists: Maximum number of specialists
            
        Returns:
            List of specialist agent instances
        """
        matches = self.route_question(question, context, max_specialists)
        specialists = []
        
        for match in matches:
            specialist = self.specialists.get(match.specialty)
            if specialist:
                specialists.append(specialist)
                logger.info(f"Routed to {match.specialty.value} (confidence: {match.confidence:.2f})")
        
        return specialists

    async def select_specialists(
        self,
        question: str,
        context: Optional[Dict] = None,
        max_specialists: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Select specialists for a question (orchestrator compatibility).
        
        Args:
            question: Medical question
            context: Additional context
            max_specialists: Maximum number of specialists
            
        Returns:
            List of specialist info dictionaries with 'type' and 'agent' keys
        """
        matches = self.route_question(question, context, max_specialists)
        specialist_info = []
        
        for match in matches:
            specialist = self.specialists.get(match.specialty)
            if specialist:
                info = {
                    'type': match.specialty.value,
                    'agent': specialist,
                    'confidence': match.confidence,
                    'reasoning': match.reasoning
                }
                specialist_info.append(info)
                logger.info(f"Selected {match.specialty.value} (confidence: {match.confidence:.2f})")
        
        return specialist_info
        

# Global expert router instance
expert_router = ExpertRouter()


# Factory function for compatibility
async def get_expert_router() -> ExpertRouter:
    """Get expert router instance."""
    return expert_router


# Legacy compatibility functions
def choose_specialists(question: str) -> List[str]:
    """Legacy compatibility function for choosing specialists."""
    try:
        matches = expert_router.route_question(question)
        return [match.specialty.value for match in matches]
    except Exception as e:
        logger.error(f"Error in legacy choose_specialists: {e}")
        return ["general"]


def get_handlers(role_names: List[str]):
    """Legacy compatibility function for getting specialist handlers."""
    handlers = []
    for role_name in role_names:
        try:
            specialty_type = SpecialtyType(role_name)
            specialist = expert_router.specialists.get(specialty_type)
            if specialist:
                # Create a wrapper for legacy compatibility
                async def legacy_handler(patient_id: str, question: str, spec=specialist):
                    opinion = await spec.get_opinion(user_id, question)
                    return opinion.primary_assessment
                handlers.append(legacy_handler)
        except ValueError:
            logger.warning(f"Unknown specialty: {role_name}")
            # Fallback to general physician
            specialist = expert_router.specialists[SpecialtyType.GENERAL]
            async def fallback_handler(patient_id: str, question: str, spec=specialist):
                opinion = await spec.get_opinion(user_id, question)
                return opinion.primary_assessment
            handlers.append(fallback_handler)
    
    return handlers
