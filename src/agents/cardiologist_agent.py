"""
Cardiologist Agent - Cardiovascular specialist agent.

This module implements a cardiologist agent that provides specialized
consultation for heart and cardiovascular system conditions.
"""

import json
from typing import Optional
from src.agents.base_specialist import BaseSpecialist, SpecialtyType
from src.config.settings import settings
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
            # Fallback to basic prompt
            return """You are a Cardiologist Agent, a heart and circulatory system expert.
            
Goals:
- Interpret cardiovascular symptoms and patient heart-related data accurately
- Explain heart findings in clear, patient-friendly language
- Request extra tests only when truly necessary

Output format: JSON with keys: summary (string), confidence (int 1-10), sources (list[str])
            
If no cardiac data available, reply: 'No sufficient heart-related data to answer.'
Do NOT discuss other organs outside your specialty."""


# Create default instance
cardiologist_agent = CardiologistAgent()
