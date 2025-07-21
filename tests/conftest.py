"""
Test configuration and fixtures for MediTwin Backend tests.
"""

import pytest
import asyncio
import os
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient
from fastapi.testclient import TestClient

from src.main import app
from src.config.settings import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings():
    """Test settings with mock values."""
    test_env = {
        "MONGO_URI": "mongodb://localhost:27017",
        "MONGO_DB_NAME": "meditwin_test",
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "test",
        "NEO4J_PASSWORD": "test",
        "MILVUS_HOST": "localhost",
        "MILVUS_PORT": "19530",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379",
        "OPENAI_API_KEY": "test-key",
        "OPENAI_MODEL": "gpt-4o-mini",
        "SECRET_KEY": "test-secret-key",
        "ENCRYPTION_KEY": "test-encryption-key-32-bytes-long"
    }
    
    # Store original values
    original_values = {}
    for key, value in test_env.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value
    
    # Reload settings
    settings.__init__()
    
    yield settings
    
    # Restore original values
    for key, value in original_values.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


@pytest.fixture
def test_client():
    """Test client for API testing."""
    return TestClient(app)


@pytest.fixture
async def async_test_client():
    """Async test client for API testing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_mongo():
    """Mock MongoDB client."""
    mock = AsyncMock()
    mock._initialized = True
    mock.store_user_data = AsyncMock(return_value="test-doc-id")
    mock.get_user_data = AsyncMock(return_value={"user_id": "test-user", "data": "test"})
    mock.store_timeline_event = AsyncMock(return_value="test-event-id")
    mock.get_timeline_events = AsyncMock(return_value=[])
    mock.get_timeline_event = AsyncMock(return_value=None)
    mock.update_timeline_event = AsyncMock(return_value=True)
    mock.delete_timeline_event = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_neo4j():
    """Mock Neo4j client."""
    mock = MagicMock()
    mock._initialized = True
    mock.create_patient_node = MagicMock(return_value=True)
    mock.create_medical_event = MagicMock(return_value="test-event-id")
    mock.update_medical_event = MagicMock(return_value=True)
    mock.delete_medical_event = MagicMock(return_value=True)
    mock.get_patient_timeline = MagicMock(return_value=[])
    return mock


@pytest.fixture
def mock_milvus():
    """Mock Milvus client."""
    mock = AsyncMock()
    mock._initialized = True
    mock.store_embeddings = AsyncMock(return_value=True)
    mock.search_similar = AsyncMock(return_value=[])
    return mock


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    mock = AsyncMock()
    mock._initialized = True
    mock.set_session_data = AsyncMock(return_value=True)
    mock.get_session_data = AsyncMock(return_value=None)
    mock.store_chat_message = AsyncMock(return_value=True)
    mock.get_chat_history = AsyncMock(return_value=[])
    return mock


@pytest.fixture
def mock_openai():
    """Mock OpenAI client."""
    mock = AsyncMock()
    
    # Mock chat completion response
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock()]
    mock_response.choices[0].message.content = '{"summary": "Test response", "confidence": 8, "sources": ["test"]}'
    
    mock.chat.completions.create = AsyncMock(return_value=mock_response)
    return mock


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "user_id": "test-user-123",
        "name": "Test User",
        "age": 35,
        "gender": "male",
        "medical_conditions": ["hypertension"],
        "medications": ["lisinopril"]
    }


@pytest.fixture
def sample_timeline_event():
    """Sample timeline event for testing."""
    return {
        "event_type": "medical",
        "title": "Blood Pressure Check",
        "description": "Routine blood pressure measurement",
        "timestamp": "2024-01-01T10:00:00Z",
        "severity": "medium",
        "metadata": {"systolic": 120, "diastolic": 80}
    }


@pytest.fixture
def sample_medical_query():
    """Sample medical query for testing."""
    return {
        "user_id": "test-user-123",
        "message": "I have been experiencing chest pain after exercise. Should I be concerned?",
        "session_id": "test-session-456"
    }
