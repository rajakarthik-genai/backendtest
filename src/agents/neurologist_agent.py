"""
Neurologist Agent - Neurological specialist agent.

This module implements a neurologist agent that provides specialized
consultation for brain, spine, and nervous system conditions.
"""

import json
from typing import Optional
from src.agents.base_specialist import BaseSpecialist, SpecialtyType
from src.config.settings import settings
from src.utils.logging import logger
from src.prompts import get_agent_prompt


class NeurologistAgent(BaseSpecialist):
    """
    Neurologist specialist agent for neurological consultation.
    
    Handles brain and nervous system conditions, including stroke,
    seizures, headaches, movement disorders, and cognitive issues.
    """
    
    def __init__(self, custom_prompt: Optional[str] = None):
        """
        Initialize the Neurologist agent.
        
        Args:
            custom_prompt: Optional custom system prompt
        """
        system_prompt = custom_prompt or self.get_specialty_prompt()
        super().__init__(SpecialtyType.NEUROLOGY, system_prompt)
    
    def get_specialty_prompt(self) -> str:
        """Get the neurologist system prompt from prompts folder."""
        try:
            return get_agent_prompt("neurologist")
        except Exception as e:
            logger.warning(f"Failed to load neurologist prompt: {e}")
            # Fallback to basic prompt
            return """You are a Neurologist Agent, a brain and nervous system specialist.
            
Goals:
- Interpret neurological imaging/tests accurately
- Provide clear, jargon-free explanations of brain/nervous findings
- Advise on next diagnostic or treatment steps where applicable

Tone: Calm, supportive—neurological issues often cause anxiety.

Output format: JSON with keys: summary (string), confidence (int 1-10), sources (list[str])
            
If no neuro data or symptom outside neurology, politely defer."""


# Create default instance
neurologist_agent = NeurologistAgent()
