"""
Prompt management utilities for loading and managing agent prompts.

This module provides utilities to load, validate, and manage JSON-based
prompts for different agent types in the MediTwin system.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from src.utils.logging import logger


class PromptManager:
    """Manages loading and caching of agent prompts."""
    
    def __init__(self):
        self.prompts_dir = Path(__file__).parent
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def load_prompt(self, prompt_name: str) -> Dict[str, Any]:
        """
        Load a prompt from the prompts directory.
        
        Args:
            prompt_name: Name of the prompt file (without .json extension)
            
        Returns:
            Dict containing the prompt configuration
            
        Raises:
            FileNotFoundError: If prompt file doesn't exist
            json.JSONDecodeError: If prompt file is invalid JSON
        """
        if prompt_name in self._cache:
            return self._cache[prompt_name]
        
        prompt_file = self.prompts_dir / f"{prompt_name}.json"
        
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
        
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_data = json.load(f)
            
            self._cache[prompt_name] = prompt_data
            logger.info(f"Loaded prompt: {prompt_name}")
            return prompt_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in prompt file {prompt_file}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load prompt {prompt_name}: {e}")
            raise
    
    def get_system_prompt(self, agent_type: str) -> str:
        """
        Get the system prompt for a specific agent type.
        
        Args:
            agent_type: Type of agent (e.g., 'cardiologist', 'neurologist')
            
        Returns:
            Formatted system prompt string
        """
        try:
            prompt_data = self.load_prompt(f"{agent_type}_prompt")
            
            # Build system prompt from the JSON structure
            system_prompt_parts = []
            
            if "agent" in prompt_data:
                system_prompt_parts.append(f"Agent: {prompt_data['agent']}")
            
            if "role" in prompt_data:
                system_prompt_parts.append(f"Role: {prompt_data['role']}")
            
            if "goals" in prompt_data:
                goals_text = "Goals:\n" + "\n".join(f"- {goal}" for goal in prompt_data['goals'])
                system_prompt_parts.append(goals_text)
            
            if "tone" in prompt_data:
                system_prompt_parts.append(f"Tone: {prompt_data['tone']}")
            
            if "step_by_step_reasoning" in prompt_data:
                reasoning_text = "Step-by-step reasoning:\n" + "\n".join(prompt_data['step_by_step_reasoning'])
                system_prompt_parts.append(reasoning_text)
            elif "logic" in prompt_data:
                logic_text = "Logic:\n" + "\n".join(prompt_data['logic'])
                system_prompt_parts.append(logic_text)
            elif "workflow" in prompt_data:
                workflow_text = "Workflow:\n" + "\n".join(prompt_data['workflow'])
                system_prompt_parts.append(workflow_text)
            
            if "output_schema" in prompt_data:
                system_prompt_parts.append(f"Output Schema: {prompt_data['output_schema']}")
            
            if "hallucination_guard" in prompt_data:
                system_prompt_parts.append(f"Important: {prompt_data['hallucination_guard']}")
            
            return "\n\n".join(system_prompt_parts)
            
        except Exception as e:
            logger.error(f"Failed to build system prompt for {agent_type}: {e}")
            return f"You are a {agent_type} medical specialist. Provide accurate, evidence-based medical information."
    
    def get_ocr_prompt(self) -> str:
        """Get the OCR system prompt for document processing."""
        try:
            ocr_data = self.load_prompt("ocr")
            return ocr_data.get("system", "You are a medical OCR assistant.")
        except Exception as e:
            logger.error(f"Failed to load OCR prompt: {e}")
            return "You are a medical OCR assistant."
    
    def get_entities_prompt(self) -> str:
        """Get the entities extraction prompt for NLP processing."""
        try:
            entities_data = self.load_prompt("entities")
            return entities_data.get("system", "You are a clinical NLP model.")
        except Exception as e:
            logger.error(f"Failed to load entities prompt: {e}")
            return "You are a clinical NLP model."
    
    def get_example_output(self, agent_type: str) -> Optional[Dict[str, Any]]:
        """
        Get example output for an agent type.
        
        Args:
            agent_type: Type of agent
            
        Returns:
            Example output dictionary or None if not available
        """
        try:
            prompt_data = self.load_prompt(f"{agent_type}_prompt")
            return prompt_data.get("example_output")
        except Exception:
            return None
    
    def clear_cache(self):
        """Clear the prompt cache."""
        self._cache.clear()
        logger.info("Prompt cache cleared")


# Global prompt manager instance
prompt_manager = PromptManager()


def get_agent_prompt(agent_type: str) -> str:
    """
    Convenience function to get agent system prompt.
    
    Args:
        agent_type: Type of agent (cardiologist, neurologist, etc.)
        
    Returns:
        System prompt string
    """
    return prompt_manager.get_system_prompt(agent_type)


def get_ocr_prompt() -> str:
    """Convenience function to get OCR prompt."""
    return prompt_manager.get_ocr_prompt()


def get_entities_prompt() -> str:
    """Convenience function to get entities extraction prompt."""
    return prompt_manager.get_entities_prompt()
