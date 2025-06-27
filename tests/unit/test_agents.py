"""
Unit tests for agent functionality.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.agents.cardiologist_agent import CardiologistAgent
from src.agents.neurologist_agent import NeurologistAgent
from src.agents.orchestrator_agent import OrchestratorAgent
from src.agents.ingestion_agent import IngestionAgent


class TestCardiologistAgent:
    """Test cases for CardiologistAgent."""

    def test_init(self):
        """Test CardiologistAgent initialization."""
        agent = CardiologistAgent()
        assert agent.specialty_type.value == "cardiology"
        assert agent.system_prompt is not None

    @patch('src.agents.cardiologist_agent.get_agent_prompt')
    def test_get_specialty_prompt(self, mock_get_prompt):
        """Test specialty prompt retrieval."""
        mock_get_prompt.return_value = "Test cardiologist prompt"
        
        agent = CardiologistAgent()
        prompt = agent.get_specialty_prompt()
        
        assert prompt == "Test cardiologist prompt"
        mock_get_prompt.assert_called_once_with("cardiologist")

    @patch('src.agents.cardiologist_agent.get_agent_prompt')
    def test_get_specialty_prompt_fallback(self, mock_get_prompt):
        """Test specialty prompt fallback on error."""
        mock_get_prompt.side_effect = Exception("Test error")
        
        agent = CardiologistAgent()
        prompt = agent.get_specialty_prompt()
        
        assert "Cardiologist Agent" in prompt
        assert "heart and circulatory system expert" in prompt


class TestNeurologistAgent:
    """Test cases for NeurologistAgent."""

    def test_init(self):
        """Test NeurologistAgent initialization."""
        agent = NeurologistAgent()
        assert agent.specialty_type.value == "neurology"
        assert agent.system_prompt is not None

    @patch('src.agents.neurologist_agent.get_agent_prompt')
    def test_get_specialty_prompt(self, mock_get_prompt):
        """Test specialty prompt retrieval."""
        mock_get_prompt.return_value = "Test neurologist prompt"
        
        agent = NeurologistAgent()
        prompt = agent.get_specialty_prompt()
        
        assert prompt == "Test neurologist prompt"
        mock_get_prompt.assert_called_once_with("neurologist")


class TestOrchestratorAgent:
    """Test cases for OrchestratorAgent."""

    def test_init(self):
        """Test OrchestratorAgent initialization."""
        agent = OrchestratorAgent()
        assert hasattr(agent, 'cardiologist')
        assert hasattr(agent, 'neurologist')
        assert hasattr(agent, 'general_physician')

    @patch('src.agents.orchestrator_agent.get_agent_prompt')
    def test_get_system_prompt(self, mock_get_prompt):
        """Test system prompt retrieval."""
        mock_get_prompt.return_value = "Test orchestrator prompt"
        
        agent = OrchestratorAgent()
        prompt = agent.get_system_prompt()
        
        assert prompt == "Test orchestrator prompt"
        mock_get_prompt.assert_called_once_with("orchestrator")

    @patch('src.agents.orchestrator_agent.get_mongo')
    @patch('src.agents.orchestrator_agent.get_redis')
    async def test_process_query_simple(self, mock_redis, mock_mongo):
        """Test simple query processing."""
        # Mock dependencies
        mock_redis_client = AsyncMock()
        mock_redis_client.get_chat_history.return_value = []
        mock_redis.return_value = mock_redis_client
        
        mock_mongo_client = AsyncMock()
        mock_mongo_client.get_user_data.return_value = {"user_id": "test", "age": 30}
        mock_mongo.return_value = mock_mongo_client
        
        agent = OrchestratorAgent()
        
        # Mock the specialist response
        with patch.object(agent.cardiologist, 'consult', return_value='{"summary": "Test response", "confidence": 8, "sources": ["test"]}'):
            response = await agent.process_query(
                user_id="test-user",
                query="I have chest pain",
                session_id="test-session"
            )
            
            assert "summary" in response or "Test response" in response


class TestIngestionAgent:
    """Test cases for IngestionAgent."""

    def test_init(self):
        """Test IngestionAgent initialization."""
        agent = IngestionAgent()
        assert agent.supported_formats == ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp']

    @patch('src.agents.ingestion_agent.get_mongo')
    @patch('src.agents.ingestion_agent.get_neo4j')
    @patch('src.agents.ingestion_agent.get_milvus')
    async def test_process_document(self, mock_milvus, mock_neo4j, mock_mongo):
        """Test document processing pipeline."""
        # Mock database clients
        mock_mongo_client = AsyncMock()
        mock_mongo_client.store_document_metadata.return_value = "test-doc-id"
        mock_mongo.return_value = mock_mongo_client
        
        mock_neo4j_client = MagicMock()
        mock_neo4j_client.create_document_node.return_value = True
        mock_neo4j.return_value = mock_neo4j_client
        
        mock_milvus_client = AsyncMock()
        mock_milvus_client.store_embeddings.return_value = True
        mock_milvus.return_value = mock_milvus_client
        
        agent = IngestionAgent()
        
        # Mock the file processing methods
        with patch.object(agent, '_extract_text', return_value="Sample medical text"):
            with patch.object(agent, '_extract_entities', return_value={"conditions": ["hypertension"]}):
                with patch.object(agent, '_generate_embeddings', return_value=[0.1, 0.2, 0.3]):
                    
                    result = await agent.process_document(
                        user_id="test-user",
                        document_id="test-doc",
                        file_path="/tmp/test.pdf",
                        metadata={"filename": "test.pdf"}
                    )
                    
                    assert "document_id" in result
                    assert result["status"] == "completed"

    def test_extract_text_unsupported_format(self):
        """Test text extraction with unsupported file format."""
        agent = IngestionAgent()
        
        # Test with unsupported file extension
        result = agent._extract_text("/tmp/test.txt")
        assert result == ""  # Should return empty string for unsupported formats


class TestAgentIntegration:
    """Integration tests for agent interactions."""

    @patch('src.agents.orchestrator_agent.get_mongo')
    @patch('src.agents.orchestrator_agent.get_redis')
    async def test_orchestrator_with_multiple_specialists(self, mock_redis, mock_mongo):
        """Test orchestrator coordinating multiple specialists."""
        # Mock dependencies
        mock_redis_client = AsyncMock()
        mock_redis_client.get_chat_history.return_value = []
        mock_redis.return_value = mock_redis_client
        
        mock_mongo_client = AsyncMock()
        mock_mongo_client.get_user_data.return_value = {"user_id": "test", "age": 30}
        mock_mongo.return_value = mock_mongo_client
        
        agent = OrchestratorAgent()
        
        # Mock multiple specialist responses
        cardio_response = '{"summary": "Heart looks normal", "confidence": 8, "sources": ["ECG"]}'
        neuro_response = '{"summary": "No neurological issues", "confidence": 7, "sources": ["MRI"]}'
        
        with patch.object(agent.cardiologist, 'consult', return_value=cardio_response):
            with patch.object(agent.neurologist, 'consult', return_value=neuro_response):
                with patch.object(agent.aggregator, 'aggregate', return_value='{"summary": "Overall healthy", "confidence": 7, "sources": ["ECG", "MRI"]}'):
                    
                    response = await agent.process_query(
                        user_id="test-user",
                        query="I have chest pain and headaches",
                        session_id="test-session"
                    )
                    
                    # Should aggregate multiple specialist responses
                    assert response is not None

    @patch('src.agents.ingestion_agent.get_entities_prompt')
    @patch('src.agents.ingestion_agent.get_ocr_prompt')
    def test_ingestion_agent_uses_prompts(self, mock_ocr_prompt, mock_entities_prompt):
        """Test that ingestion agent uses prompt system."""
        mock_ocr_prompt.return_value = "Test OCR prompt"
        mock_entities_prompt.return_value = "Test entities prompt"
        
        agent = IngestionAgent()
        
        # The agent should be able to access prompts
        assert hasattr(agent, '_extract_entities')
        # Verify prompts are accessible (they're imported)
        from src.agents.ingestion_agent import get_entities_prompt, get_ocr_prompt
        assert get_entities_prompt() == "Test entities prompt"
        assert get_ocr_prompt() == "Test OCR prompt"
