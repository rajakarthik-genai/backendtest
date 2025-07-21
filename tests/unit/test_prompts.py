"""
Unit tests for prompt management system.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from src.prompts import PromptManager, get_agent_prompt, get_ocr_prompt, get_entities_prompt


class TestPromptManager:
    """Test cases for PromptManager class."""

    def test_init(self):
        """Test PromptManager initialization."""
        manager = PromptManager()
        assert manager.prompts_dir.exists()
        assert isinstance(manager._cache, dict)
        assert len(manager._cache) == 0

    def test_load_prompt_success(self):
        """Test successful prompt loading."""
        # Create a temporary prompt file
        test_prompt_data = {
            "agent": "Test Agent",
            "role": "Test role",
            "goals": ["Test goal 1", "Test goal 2"]
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            prompt_file = temp_path / "test_prompt.json"
            
            with open(prompt_file, 'w') as f:
                json.dump(test_prompt_data, f)
            
            manager = PromptManager()
            manager.prompts_dir = temp_path
            
            result = manager.load_prompt("test_prompt")
            assert result == test_prompt_data
            assert "test_prompt" in manager._cache

    def test_load_prompt_file_not_found(self):
        """Test prompt loading with non-existent file."""
        manager = PromptManager()
        
        with pytest.raises(FileNotFoundError):
            manager.load_prompt("nonexistent_prompt")

    def test_load_prompt_invalid_json(self):
        """Test prompt loading with invalid JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            prompt_file = temp_path / "invalid_prompt.json"
            
            with open(prompt_file, 'w') as f:
                f.write("invalid json content")
            
            manager = PromptManager()
            manager.prompts_dir = temp_path
            
            with pytest.raises(json.JSONDecodeError):
                manager.load_prompt("invalid_prompt")

    def test_get_system_prompt_full_structure(self):
        """Test system prompt generation with full JSON structure."""
        test_prompt_data = {
            "agent": "Test Agent",
            "role": "Test specialist",
            "goals": ["Goal 1", "Goal 2"],
            "tone": "Professional",
            "step_by_step_reasoning": ["Step 1", "Step 2"],
            "output_schema": "test_schema",
            "hallucination_guard": "Important note"
        }
        
        manager = PromptManager()
        
        with patch.object(manager, 'load_prompt', return_value=test_prompt_data):
            result = manager.get_system_prompt("test")
            
            assert "Agent: Test Agent" in result
            assert "Role: Test specialist" in result
            assert "Goals:" in result
            assert "Goal 1" in result
            assert "Tone: Professional" in result
            assert "Step-by-step reasoning:" in result
            assert "Output Schema: test_schema" in result
            assert "Important: Important note" in result

    def test_get_system_prompt_minimal_structure(self):
        """Test system prompt generation with minimal JSON structure."""
        test_prompt_data = {
            "agent": "Test Agent"
        }
        
        manager = PromptManager()
        
        with patch.object(manager, 'load_prompt', return_value=test_prompt_data):
            result = manager.get_system_prompt("test")
            assert "Agent: Test Agent" in result

    def test_get_system_prompt_with_logic(self):
        """Test system prompt generation with logic field."""
        test_prompt_data = {
            "agent": "Test Agent",
            "logic": ["Logic step 1", "Logic step 2"]
        }
        
        manager = PromptManager()
        
        with patch.object(manager, 'load_prompt', return_value=test_prompt_data):
            result = manager.get_system_prompt("test")
            assert "Logic:" in result
            assert "Logic step 1" in result

    def test_get_system_prompt_with_workflow(self):
        """Test system prompt generation with workflow field."""
        test_prompt_data = {
            "agent": "Test Agent",
            "workflow": ["Workflow step 1", "Workflow step 2"]
        }
        
        manager = PromptManager()
        
        with patch.object(manager, 'load_prompt', return_value=test_prompt_data):
            result = manager.get_system_prompt("test")
            assert "Workflow:" in result
            assert "Workflow step 1" in result

    def test_get_system_prompt_error_fallback(self):
        """Test system prompt generation with error fallback."""
        manager = PromptManager()
        
        with patch.object(manager, 'load_prompt', side_effect=Exception("Test error")):
            result = manager.get_system_prompt("test")
            assert "You are a test medical specialist" in result

    def test_get_ocr_prompt_success(self):
        """Test OCR prompt retrieval."""
        test_ocr_data = {"system": "Test OCR prompt"}
        
        manager = PromptManager()
        
        with patch.object(manager, 'load_prompt', return_value=test_ocr_data):
            result = manager.get_ocr_prompt()
            assert result == "Test OCR prompt"

    def test_get_ocr_prompt_error_fallback(self):
        """Test OCR prompt retrieval with error fallback."""
        manager = PromptManager()
        
        with patch.object(manager, 'load_prompt', side_effect=Exception("Test error")):
            result = manager.get_ocr_prompt()
            assert result == "You are a medical OCR assistant."

    def test_get_entities_prompt_success(self):
        """Test entities prompt retrieval."""
        test_entities_data = {"system": "Test entities prompt"}
        
        manager = PromptManager()
        
        with patch.object(manager, 'load_prompt', return_value=test_entities_data):
            result = manager.get_entities_prompt()
            assert result == "Test entities prompt"

    def test_get_entities_prompt_error_fallback(self):
        """Test entities prompt retrieval with error fallback."""
        manager = PromptManager()
        
        with patch.object(manager, 'load_prompt', side_effect=Exception("Test error")):
            result = manager.get_entities_prompt()
            assert result == "You are a clinical NLP model."

    def test_get_example_output_success(self):
        """Test example output retrieval."""
        test_prompt_data = {
            "example_output": {"test": "example"}
        }
        
        manager = PromptManager()
        
        with patch.object(manager, 'load_prompt', return_value=test_prompt_data):
            result = manager.get_example_output("test")
            assert result == {"test": "example"}

    def test_get_example_output_none(self):
        """Test example output retrieval when not available."""
        test_prompt_data = {}
        
        manager = PromptManager()
        
        with patch.object(manager, 'load_prompt', return_value=test_prompt_data):
            result = manager.get_example_output("test")
            assert result is None

    def test_get_example_output_error(self):
        """Test example output retrieval with error."""
        manager = PromptManager()
        
        with patch.object(manager, 'load_prompt', side_effect=Exception("Test error")):
            result = manager.get_example_output("test")
            assert result is None

    def test_clear_cache(self):
        """Test cache clearing."""
        manager = PromptManager()
        manager._cache["test"] = {"data": "test"}
        
        assert len(manager._cache) == 1
        manager.clear_cache()
        assert len(manager._cache) == 0

    def test_caching_behavior(self):
        """Test that prompts are cached correctly."""
        test_prompt_data = {"agent": "Test Agent"}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            prompt_file = temp_path / "test_prompt.json"
            
            with open(prompt_file, 'w') as f:
                json.dump(test_prompt_data, f)
            
            manager = PromptManager()
            manager.prompts_dir = temp_path
            
            # First load should read file
            result1 = manager.load_prompt("test_prompt")
            assert result1 == test_prompt_data
            assert "test_prompt" in manager._cache
            
            # Second load should use cache
            result2 = manager.load_prompt("test_prompt")
            assert result2 == test_prompt_data
            assert result1 is result2  # Same object from cache


class TestConvenienceFunctions:
    """Test cases for convenience functions."""

    @patch('src.prompts.prompt_manager')
    def test_get_agent_prompt(self, mock_manager):
        """Test get_agent_prompt convenience function."""
        mock_manager.get_system_prompt.return_value = "Test prompt"
        
        result = get_agent_prompt("cardiologist")
        
        mock_manager.get_system_prompt.assert_called_once_with("cardiologist")
        assert result == "Test prompt"

    @patch('src.prompts.prompt_manager')
    def test_get_ocr_prompt(self, mock_manager):
        """Test get_ocr_prompt convenience function."""
        mock_manager.get_ocr_prompt.return_value = "Test OCR prompt"
        
        result = get_ocr_prompt()
        
        mock_manager.get_ocr_prompt.assert_called_once()
        assert result == "Test OCR prompt"

    @patch('src.prompts.prompt_manager')
    def test_get_entities_prompt(self, mock_manager):
        """Test get_entities_prompt convenience function."""
        mock_manager.get_entities_prompt.return_value = "Test entities prompt"
        
        result = get_entities_prompt()
        
        mock_manager.get_entities_prompt.assert_called_once()
        assert result == "Test entities prompt"
