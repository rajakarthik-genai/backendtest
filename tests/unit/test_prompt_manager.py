"""
Unit tests for the prompt management system.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from src.prompts import PromptManager, get_agent_prompt, get_ocr_prompt, get_entities_prompt


class TestPromptManager:
    """Test cases for PromptManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.prompt_manager = PromptManager()
        self.test_prompt_data = {
            "agent": "Test Agent",
            "role": "Test role",
            "goals": ["Goal 1", "Goal 2"],
            "tone": "Professional",
            "step_by_step_reasoning": ["Step 1", "Step 2"],
            "output_schema": "test_schema",
            "hallucination_guard": "Test guard",
            "example_output": {"test": "example"}
        }
    
    def test_init(self):
        """Test PromptManager initialization."""
        pm = PromptManager()
        assert pm.prompts_dir == Path(__file__).parent.parent.parent / "src" / "prompts"
        assert pm._cache == {}
    
    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists")
    def test_load_prompt_success(self, mock_exists, mock_file):
        """Test successful prompt loading."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(self.test_prompt_data)
        
        result = self.prompt_manager.load_prompt("test_prompt")
        
        assert result == self.test_prompt_data
        assert "test_prompt" in self.prompt_manager._cache
        mock_file.assert_called_once()
    
    @patch("pathlib.Path.exists")
    def test_load_prompt_file_not_found(self, mock_exists):
        """Test FileNotFoundError when prompt file doesn't exist."""
        mock_exists.return_value = False
        
        with pytest.raises(FileNotFoundError):
            self.prompt_manager.load_prompt("nonexistent_prompt")
    
    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists")
    def test_load_prompt_invalid_json(self, mock_exists, mock_file):
        """Test handling of invalid JSON in prompt file."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = "invalid json"
        
        with pytest.raises(json.JSONDecodeError):
            self.prompt_manager.load_prompt("invalid_prompt")
    
    def test_load_prompt_caching(self):
        """Test that prompts are cached after first load."""
        # Manually add to cache
        self.prompt_manager._cache["cached_prompt"] = self.test_prompt_data
        
        result = self.prompt_manager.load_prompt("cached_prompt")
        assert result == self.test_prompt_data
    
    @patch.object(PromptManager, 'load_prompt')
    def test_get_system_prompt_complete(self, mock_load):
        """Test system prompt generation with all fields."""
        mock_load.return_value = self.test_prompt_data
        
        result = self.prompt_manager.get_system_prompt("test")
        
        expected_parts = [
            "Agent: Test Agent",
            "Role: Test role",
            "Goals:\n- Goal 1\n- Goal 2",
            "Tone: Professional",
            "Step-by-step reasoning:\n- Step 1\n- Step 2",
            "Output Schema: test_schema",
            "Important: Test guard"
        ]
        
        for part in expected_parts:
            assert part in result
        mock_load.assert_called_once_with("test_prompt")
    
    @patch.object(PromptManager, 'load_prompt')
    def test_get_system_prompt_minimal(self, mock_load):
        """Test system prompt generation with minimal fields."""
        minimal_data = {"agent": "Minimal Agent"}
        mock_load.return_value = minimal_data
        
        result = self.prompt_manager.get_system_prompt("minimal")
        
        assert "Agent: Minimal Agent" in result
        mock_load.assert_called_once_with("minimal_prompt")
    
    @patch.object(PromptManager, 'load_prompt')
    def test_get_system_prompt_with_logic(self, mock_load):
        """Test system prompt generation with logic field instead of reasoning."""
        data_with_logic = {
            "agent": "Logic Agent",
            "logic": ["Logic step 1", "Logic step 2"]
        }
        mock_load.return_value = data_with_logic
        
        result = self.prompt_manager.get_system_prompt("logic")
        
        assert "Logic:\n- Logic step 1\n- Logic step 2" in result
    
    @patch.object(PromptManager, 'load_prompt')
    def test_get_system_prompt_with_workflow(self, mock_load):
        """Test system prompt generation with workflow field."""
        data_with_workflow = {
            "agent": "Workflow Agent",
            "workflow": ["Workflow step 1", "Workflow step 2"]
        }
        mock_load.return_value = data_with_workflow
        
        result = self.prompt_manager.get_system_prompt("workflow")
        
        assert "Workflow:\n- Workflow step 1\n- Workflow step 2" in result
    
    @patch.object(PromptManager, 'load_prompt')
    def test_get_system_prompt_error_fallback(self, mock_load):
        """Test fallback behavior when prompt loading fails."""
        mock_load.side_effect = Exception("Test error")
        
        result = self.prompt_manager.get_system_prompt("error")
        
        assert result == "You are a error medical specialist. Provide accurate, evidence-based medical information."
    
    @patch.object(PromptManager, 'load_prompt')
    def test_get_ocr_prompt_success(self, mock_load):
        """Test OCR prompt retrieval."""
        ocr_data = {"system": "Test OCR prompt"}
        mock_load.return_value = ocr_data
        
        result = self.prompt_manager.get_ocr_prompt()
        
        assert result == "Test OCR prompt"
        mock_load.assert_called_once_with("ocr")
    
    @patch.object(PromptManager, 'load_prompt')
    def test_get_ocr_prompt_fallback(self, mock_load):
        """Test OCR prompt fallback on error."""
        mock_load.side_effect = Exception("Test error")
        
        result = self.prompt_manager.get_ocr_prompt()
        
        assert result == "You are a medical OCR assistant."
    
    @patch.object(PromptManager, 'load_prompt')
    def test_get_entities_prompt_success(self, mock_load):
        """Test entities prompt retrieval."""
        entities_data = {"system": "Test entities prompt"}
        mock_load.return_value = entities_data
        
        result = self.prompt_manager.get_entities_prompt()
        
        assert result == "Test entities prompt"
        mock_load.assert_called_once_with("entities")
    
    @patch.object(PromptManager, 'load_prompt')
    def test_get_entities_prompt_fallback(self, mock_load):
        """Test entities prompt fallback on error."""
        mock_load.side_effect = Exception("Test error")
        
        result = self.prompt_manager.get_entities_prompt()
        
        assert result == "You are a clinical NLP model."
    
    @patch.object(PromptManager, 'load_prompt')
    def test_get_example_output_success(self, mock_load):
        """Test example output retrieval."""
        mock_load.return_value = self.test_prompt_data
        
        result = self.prompt_manager.get_example_output("test")
        
        assert result == {"test": "example"}
        mock_load.assert_called_once_with("test_prompt")
    
    @patch.object(PromptManager, 'load_prompt')
    def test_get_example_output_not_found(self, mock_load):
        """Test example output when not available."""
        mock_load.return_value = {"agent": "No example"}
        
        result = self.prompt_manager.get_example_output("test")
        
        assert result is None
    
    @patch.object(PromptManager, 'load_prompt')
    def test_get_example_output_error(self, mock_load):
        """Test example output on error."""
        mock_load.side_effect = Exception("Test error")
        
        result = self.prompt_manager.get_example_output("test")
        
        assert result is None
    
    def test_clear_cache(self):
        """Test cache clearing."""
        self.prompt_manager._cache["test"] = {"data": "test"}
        
        self.prompt_manager.clear_cache()
        
        assert self.prompt_manager._cache == {}


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    @patch('src.prompts.prompt_manager')
    def test_get_agent_prompt(self, mock_manager):
        """Test get_agent_prompt convenience function."""
        mock_manager.get_system_prompt.return_value = "Test prompt"
        
        result = get_agent_prompt("cardiologist")
        
        assert result == "Test prompt"
        mock_manager.get_system_prompt.assert_called_once_with("cardiologist")
    
    @patch('src.prompts.prompt_manager')
    def test_get_ocr_prompt_function(self, mock_manager):
        """Test get_ocr_prompt convenience function."""
        mock_manager.get_ocr_prompt.return_value = "OCR prompt"
        
        result = get_ocr_prompt()
        
        assert result == "OCR prompt"
        mock_manager.get_ocr_prompt.assert_called_once()
    
    @patch('src.prompts.prompt_manager')
    def test_get_entities_prompt_function(self, mock_manager):
        """Test get_entities_prompt convenience function."""
        mock_manager.get_entities_prompt.return_value = "Entities prompt"
        
        result = get_entities_prompt()
        
        assert result == "Entities prompt"
        mock_manager.get_entities_prompt.assert_called_once()
