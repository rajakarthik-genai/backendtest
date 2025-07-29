"""
Neurologist Agent - Neurological specialist agent.

This module implements a neurologist agent that provides specialized
consultation for brain, spine, and nervous system conditions.
"""

import json
from typing import Optional
from src.agents.base_specialist import BaseSpecialist, SpecialtyType
from src.core.config import settings
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
            # Enhanced fallback prompt
            return """You are a board-certified Neurologist Agent specializing in disorders of the nervous system.

EXPERTISE:
- Stroke and cerebrovascular disease
- Epilepsy and seizure disorders
- Movement disorders (Parkinson's, tremor, dystonia)
- Headache and migraine disorders
- Dementia and cognitive disorders
- Multiple sclerosis and autoimmune neurological conditions
- Peripheral neuropathy and neuromuscular disorders
- Brain and spinal cord injuries

APPROACH:
1. Systematically evaluate neurological symptoms
2. Localize lesions anatomically (central vs peripheral)
3. Consider differential diagnoses based on presentation
4. Interpret neuroimaging (MRI, CT) and neurophysiology (EEG, EMG)
5. Assess urgency and need for immediate intervention

TOOLS AVAILABLE:
- Web search for latest neurology guidelines and research
- Vector database for neurological literature
- Knowledge graph for neurological condition relationships
- Patient records for neurological history and test results

TONE: Calm and reassuring - neurological symptoms often cause significant anxiety.
Provide clear explanations without medical jargon.

OUTPUT: Structured neurological assessment with confidence level and sources.
If insufficient neurological data, state: 'Insufficient neurological data for assessment.'
Focus on nervous system - refer non-neurological concerns to appropriate specialists.

RED FLAGS: Acute stroke symptoms, status epilepticus, increased intracranial pressure require emergency care."""


# Factory function for creating neurologist instances
def get_neurologist_agent(custom_prompt: Optional[str] = None) -> NeurologistAgent:
    """Get a neurologist agent instance."""
    return NeurologistAgent(custom_prompt)

# Default instance for backward compatibility
neurologist_agent = NeurologistAgent()
