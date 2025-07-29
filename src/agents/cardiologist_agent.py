"""
Cardiologist Agent - Cardiovascular specialist agent.

This module implements a cardiologist agent that provides specialized
consultation for heart and cardiovascular system conditions.
"""

import json
from typing import Optional
from src.agents.base_specialist import BaseSpecialist, SpecialtyType
from src.core.config import settings
from src.utils.logging import logger
from src.prompts import get_agent_prompt


class CardiologistAgent(BaseSpecialist):
    """
    Cardiologist specialist agent for cardiovascular consultation.
    
    Handles heart conditions, cardiovascular risk assessment,
    and cardiac-related symptoms and diseases.
    """
    
    def __init__(self, custom_prompt: Optional[str] = None):
        """
        Initialize the Cardiologist agent.
        
        Args:
            custom_prompt: Optional custom system prompt
        """
        system_prompt = custom_prompt or self.get_specialty_prompt()
        super().__init__(SpecialtyType.CARDIOLOGY, system_prompt)
    
    def get_specialty_prompt(self) -> str:
        """Get the cardiologist system prompt from prompts folder."""
        try:
            return get_agent_prompt("cardiologist")
        except Exception as e:
            logger.warning(f"Failed to load cardiologist prompt: {e}")
            # Enhanced fallback prompt
            return """You are a board-certified Cardiologist Agent specializing in cardiovascular medicine.

EXPERTISE:
- Cardiovascular disease diagnosis and management
- Cardiac risk stratification and prevention
- Heart rhythm disorders and electrophysiology
- Heart failure and cardiomyopathy
- Coronary artery disease and interventional cardiology
- Hypertension and vascular medicine

APPROACH:
1. Analyze cardiovascular symptoms systematically
2. Consider patient risk factors (age, diabetes, smoking, family history)
3. Interpret cardiac tests (ECG, echo, stress tests, cardiac enzymes)
4. Provide evidence-based recommendations
5. Identify urgent vs non-urgent cardiac concerns

TOOLS AVAILABLE:
- Web search for latest cardiology guidelines
- Vector database for cardiology research
- Knowledge graph for cardiac condition relationships
- Patient records for cardiac history and test results

OUTPUT: Always provide structured analysis with confidence level and sources.
If insufficient cardiac data, state: 'Insufficient cardiovascular data for assessment.'
Focus strictly on cardiac/cardiovascular aspects - refer other concerns to appropriate specialists.

EMERGENCY INDICATORS: Chest pain, shortness of breath, syncope, palpitations require immediate evaluation."""


# Factory function for creating cardiologist instances
def get_cardiologist_agent(custom_prompt: Optional[str] = None) -> CardiologistAgent:
    """Get a cardiologist agent instance."""
    return CardiologistAgent(custom_prompt)

# Default instance for backward compatibility
cardiologist_agent = CardiologistAgent()
