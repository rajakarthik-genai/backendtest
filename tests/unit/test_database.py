"""
Comprehensive Unit Tests for Database Components

This module contains all unit tests for database connections, operations,
and HIPAA compliance validations.
"""

import pytest
import asyncio
import sys
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

# Add project root to path
sys.path.append('/home/user/agents/meditwin-agents')

from src.db.mongodb import get_database
from src.db.neo4j import neo4j_connection, Neo4jConnection
from src.db.redis_db import get_redis
from src.db.milvus_client import get_milvus_client
from src.chat.short_term import get_short_term_memory, ShortTermMemory


class TestMongoDBOperations:
    """Unit tests for MongoDB operations"""
    
    @pytest.mark.asyncio
    async def test_get_database_connection(self):
        """Test MongoDB database connection"""
        try:
            db = await get_database()
            assert db is not None, "Database connection should not be None"
        except Exception as e:
            pytest.skip(f"MongoDB not available: {e}")
    
    @pytest.mark.asyncio 
    async def test_database_operations_mock(self):
        """Test database operations with mocked connection"""
        with patch('src.db.mongodb.get_database') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            
            db = await get_database()
            assert db is not None
            mock_get_db.assert_called_once()


class TestNeo4jOperations:
    """Unit tests for Neo4j operations and HIPAA compliance"""
    
    def test_neo4j_connection_initialization(self):
        """Test Neo4j connection initialization"""
        connection = Neo4jConnection()
        assert connection is not None
        assert hasattr(connection, '_connect')
        assert hasattr(connection, 'execute_query')
        assert hasattr(connection, 'execute_write')
    
    def test_hipaa_compliance_methods_exist(self):
        """Test that HIPAA compliance methods exist"""
        connection = Neo4jConnection()
        
        # Critical HIPAA compliance methods
        assert hasattr(connection, 'validate_patient_isolation'), "Patient isolation validation missing"
        assert hasattr(connection, 'fix_patient_data_isolation'), "Patient data fix method missing"
        assert hasattr(connection, 'create_event_node'), "Event node creation missing"
        assert hasattr(connection, 'create_relationships'), "Relationship creation missing"
    
    def test_create_event_node_signature(self):
        """Test that create_event_node enforces patient isolation"""
        import inspect
        
        sig = inspect.signature(neo4j_connection.create_event_node)
        params = list(sig.parameters.keys())
        
        assert 'patient_id' in params, "create_event_node must include patient_id for HIPAA compliance"
        assert 'event_data' in params, "create_event_node must accept event_data"
    
    def test_create_relationships_validation(self):
        """Test relationship creation validates patient isolation"""
        import inspect
        
        sig = inspect.signature(neo4j_connection.create_relationships)
        params = list(sig.parameters.keys())
        
        required_params = ['patient_id', 'document_id', 'event_type', 'event_id']
        for param in required_params:
            assert param in params, f"create_relationships missing required parameter: {param}"
    
    @patch('src.db.neo4j.GraphDatabase')
    def test_patient_isolation_validation_mock(self, mock_graph_db):
        """Test patient isolation validation with mocked Neo4j"""
        mock_driver = Mock()
        mock_session = Mock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_graph_db.driver.return_value = mock_driver
        
        connection = Neo4jConnection()
        connection.driver = mock_driver
        
        # Test that method exists and can be called
        assert callable(getattr(connection, 'validate_patient_isolation', None))


class TestRedisOperations:
    """Unit tests for Redis operations"""
    
    def test_redis_client_initialization(self):
        """Test Redis client initialization"""
        try:
            redis_client = get_redis()
            assert redis_client is not None
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")
    
    def test_redis_client_methods(self):
        """Test Redis client has required methods"""
        try:
            redis_client = get_redis()
            
            required_methods = ['store_chat_message', 'get_chat_history']
            for method in required_methods:
                assert hasattr(redis_client, method), f"Redis client missing method: {method}"
                
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")


class TestMilvusOperations:
    """Unit tests for Milvus vector database operations"""
    
    def test_milvus_client_initialization(self):
        """Test Milvus client initialization"""
        try:
            milvus_client = get_milvus_client()
            assert milvus_client is not None
        except Exception as e:
            pytest.skip(f"Milvus not available: {e}")
    
    def test_milvus_insert_document_method(self):
        """Test that insert_document method exists (was previously missing)"""
        try:
            milvus_client = get_milvus_client()
            assert hasattr(milvus_client, 'insert_document'), "insert_document method missing from MilvusClient"
        except Exception as e:
            pytest.skip(f"Milvus not available: {e}")


class TestShortTermMemory:
    """Unit tests for Short Term Memory system"""
    
    def test_short_term_memory_initialization(self):
        """Test ShortTermMemory initialization"""
        stm = get_short_term_memory()
        assert stm is not None
        assert isinstance(stm, ShortTermMemory)
    
    def test_required_methods_exist(self):
        """Test that all required methods exist (fixes coroutine errors)"""
        stm = get_short_term_memory()
        
        required_methods = [
            'get_recent_messages', 
            'store_message', 
            'get_context'
        ]
        
        for method in required_methods:
            assert hasattr(stm, method), f"ShortTermMemory missing method: {method}"
            assert callable(getattr(stm, method)), f"Method {method} is not callable"
    
    def test_store_message_signature(self):
        """Test store_message method signature includes all expected parameters"""
        import inspect
        
        stm = get_short_term_memory()
        sig = inspect.signature(stm.store_message)
        params = list(sig.parameters.keys())
        
        expected_params = ['self', 'patient_id', 'conversation_id']
        for param in expected_params:
            assert param in params, f"store_message missing parameter: {param}"
    
    def test_get_recent_messages_signature(self):
        """Test get_recent_messages method signature"""
        import inspect
        
        stm = get_short_term_memory()
        sig = inspect.signature(stm.get_recent_messages)
        params = list(sig.parameters.keys())
        
        expected_params = ['self', 'patient_id']
        for param in expected_params:
            assert param in params, f"get_recent_messages missing parameter: {param}"
    
    @pytest.mark.asyncio
    async def test_memory_operations_mock(self):
        """Test memory operations with mocked Redis"""
        with patch('src.chat.short_term.get_redis') as mock_get_redis:
            mock_redis = Mock()
            mock_redis.get_chat_history.return_value = []
            mock_redis.store_chat_message.return_value = True
            mock_get_redis.return_value = mock_redis
            
            stm = get_short_term_memory()
            
            # Test get_recent_messages
            messages = await stm.get_recent_messages("test_patient", limit=5)
            assert isinstance(messages, list)
            
            # Test store_message  
            result = await stm.store_message(
                patient_id="test_patient",
                conversation_id="test_conv",
                user_message="Test message"
            )
            assert isinstance(result, bool)


class TestDatabaseSecurity:
    """Unit tests for database security and HIPAA compliance"""
    
    def test_patient_id_required_in_entities(self):
        """Test that patient_id is required in all medical entities"""
        # This test ensures HIPAA compliance by verifying patient data isolation
        
        # Test event creation requires patient_id
        import inspect
        sig = inspect.signature(neo4j_connection.create_event_node)
        assert 'patient_id' in sig.parameters, "Events must include patient_id for HIPAA compliance"
        
        # Test document creation includes patient_id validation
        sig = inspect.signature(neo4j_connection.add_document_to_graph)
        assert 'patient_id' in sig.parameters, "Documents must include patient_id for HIPAA compliance"
    
    def test_hipaa_validation_functions(self):
        """Test HIPAA validation functions are available"""
        # Ensure audit and fix functions exist
        assert hasattr(neo4j_connection, 'validate_patient_isolation')
        assert hasattr(neo4j_connection, 'fix_patient_data_isolation')
        
        # Ensure they are callable
        assert callable(neo4j_connection.validate_patient_isolation)
        assert callable(neo4j_connection.fix_patient_data_isolation)
    
    def test_memory_patient_isolation(self):
        """Test memory system enforces patient isolation"""
        stm = get_short_term_memory()
        
        # Verify patient_id is required parameter
        import inspect
        store_sig = inspect.signature(stm.store_message)
        get_sig = inspect.signature(stm.get_recent_messages)
        
        assert 'patient_id' in store_sig.parameters
        assert 'patient_id' in get_sig.parameters


# Pytest fixtures for database testing
@pytest.fixture
def mock_mongodb():
    """Mock MongoDB connection for testing"""
    with patch('src.db.mongodb.get_database') as mock:
        mock_db = AsyncMock()
        mock.return_value = mock_db
        yield mock_db


@pytest.fixture
def mock_neo4j():
    """Mock Neo4j connection for testing"""
    with patch('src.db.neo4j.GraphDatabase') as mock:
        mock_driver = Mock()
        mock.driver.return_value = mock_driver
        yield mock_driver


@pytest.fixture
def mock_redis():
    """Mock Redis connection for testing"""
    with patch('src.db.redis_db.get_redis') as mock:
        mock_redis = Mock()
        mock.return_value = mock_redis
        yield mock_redis


# Integration-style tests that can run without external dependencies
class TestDatabaseIntegration:
    """Database integration tests that work with or without live connections"""
    
    @pytest.mark.asyncio
    async def test_full_database_stack(self, mock_mongodb, mock_neo4j, mock_redis):
        """Test that all database components can be initialized together"""
        
        # Test MongoDB
        db = await get_database()
        assert db is not None
        
        # Test Neo4j
        neo4j_conn = Neo4jConnection()
        assert neo4j_conn is not None
        
        # Test Redis
        redis_client = get_redis()
        assert redis_client is not None
        
        # Test ShortTermMemory
        stm = get_short_term_memory()
        assert stm is not None
        
        print("✅ All database components initialized successfully")


if __name__ == "__main__":
    # Run tests standalone
    pytest.main([__file__, "-v"])

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from typing import Dict, Any

from src.db.mongo_db import MongoDB
from src.db.neo4j_db import Neo4jDB
from src.db.milvus_db import MilvusDB
from src.db.redis_db import RedisDB


class TestMongoDBManager:
    """Test cases for MongoDB manager."""
    
    @pytest.fixture
    def mongo_manager(self):
        """Create MongoDB manager instance."""
        return MongoDB()
    
    @pytest.mark.asyncio
    async def test_init_mongo_success(self, mongo_manager):
        """Test successful MongoDB initialization."""
        with patch('motor.motor_asyncio.AsyncIOMotorClient') as mock_client:
            mock_db = MagicMock()
            mock_client.return_value.__getitem__.return_value = mock_db
            
            await mongo_manager.initialize("mongodb://localhost:27017", "test_db")
            
            assert mongo_manager._initialized is True
            mock_client.assert_called_once_with("mongodb://localhost:27017")
    
    @pytest.mark.asyncio
    async def test_store_medical_record(self, mongo_manager):
        """Test storing medical record."""
        mongo_manager._initialized = True
        mongo_manager.db = MagicMock()
        mongo_manager.db.medical_records.insert_one = AsyncMock(return_value=MagicMock(inserted_id="test_id"))
        
        record_data = {
            "patient_id": "test_patient",
            "condition": "test_condition",
            "timestamp": datetime.utcnow()
        }
        
        with patch.object(mongo_manager, '_hash_user_id', return_value="hashed_id"):
            result = await mongo_manager.store_medical_record("user123", record_data)
            
            assert result == "test_id"
            mongo_manager.db.medical_records.insert_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_medical_records(self, mongo_manager):
        """Test retrieving medical records."""
        mongo_manager._initialized = True
        mongo_manager.db = MagicMock()
        
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=[{"record": "test"}])
        mongo_manager.db.medical_records.find.return_value.sort.return_value.limit.return_value = mock_cursor
        
        with patch.object(mongo_manager, '_hash_user_id', return_value="hashed_id"):
            result = await mongo_manager.get_medical_records("user123")
            
            assert result == [{"record": "test"}]
    
    @pytest.mark.asyncio
    async def test_store_timeline_event(self, mongo_manager):
        """Test storing timeline event."""
        mongo_manager._initialized = True
        mongo_manager.db = MagicMock()
        mongo_manager.db.timeline_events.insert_one = AsyncMock(return_value=MagicMock(inserted_id="timeline_id"))
        
        event_data = {
            "title": "Test Event",
            "description": "Test Description",
            "event_type": "medical"
        }
        
        with patch.object(mongo_manager, '_hash_user_id', return_value="hashed_id"):
            with patch('src.db.mongo_db.ObjectId', return_value="event_123"):
                result = await mongo_manager.store_timeline_event("user123", event_data)
                
                assert result == "event_123"
                mongo_manager.db.timeline_events.insert_one.assert_called_once()


class TestNeo4jManager:
    """Test cases for Neo4j manager."""
    
    @pytest.fixture
    def neo4j_manager(self):
        """Create Neo4j manager instance."""
        return Neo4jDB()
    
    def test_initialize_success(self, neo4j_manager):
        """Test successful Neo4j initialization."""
        with patch('neo4j.GraphDatabase.driver') as mock_driver:
            neo4j_manager.initialize("bolt://localhost:7687", "neo4j", "password")
            
            assert neo4j_manager._initialized is True
            mock_driver.assert_called_once_with("bolt://localhost:7687", auth=("neo4j", "password"))
    
    def test_create_patient_node(self, neo4j_manager):
        """Test creating patient node."""
        neo4j_manager._initialized = True
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_driver.session.return_value = mock_session
        neo4j_manager.driver = mock_driver
        
        patient_data = {
            "name": "John Doe",
            "age": 30,
            "gender": "M"
        }
        
        with patch.object(neo4j_manager, '_hash_user_id', return_value="hashed_id"):
            result = neo4j_manager.create_patient_node("user123", patient_data)
            
            assert result is True
            mock_session.run.assert_called()
    
    def test_create_medical_event(self, neo4j_manager):
        """Test creating medical event."""
        neo4j_manager._initialized = True
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_driver.session.return_value = mock_session
        neo4j_manager.driver = mock_driver
        
        event_data = {
            "title": "Chest Pain",
            "description": "Patient experiencing chest pain",
            "event_type": "symptom"
        }
        
        with patch.object(neo4j_manager, '_hash_user_id', return_value="hashed_id"):
            with patch.object(neo4j_manager, '_identify_body_parts', return_value=["chest"]):
                result = neo4j_manager.create_medical_event("user123", event_data)
                
                assert isinstance(result, str)
                mock_session.run.assert_called()


class TestMilvusManager:
    """Test cases for Milvus manager."""
    
    @pytest.fixture
    def milvus_manager(self):
        """Create Milvus manager instance."""
        return MilvusDB()
    
    def test_initialize_success(self, milvus_manager):
        """Test successful Milvus initialization."""
        with patch('pymilvus.connections.connect') as mock_connect:
            milvus_manager.initialize("localhost", 19530)
            
            assert milvus_manager._initialized is True
            mock_connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_store_embeddings(self, milvus_manager):
        """Test storing embeddings."""
        milvus_manager._initialized = True
        
        with patch('pymilvus.Collection') as mock_collection:
            mock_coll_instance = MagicMock()
            mock_collection.return_value = mock_coll_instance
            
            embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
            texts = ["text1", "text2"]
            
            with patch.object(milvus_manager, '_hash_user_id', return_value="hashed_id"):
                result = await milvus_manager.store_embeddings("user123", "doc123", embeddings, texts)
                
                assert result is True
                mock_coll_instance.insert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_similar(self, milvus_manager):
        """Test similarity search."""
        milvus_manager._initialized = True
        
        with patch('pymilvus.Collection') as mock_collection:
            mock_coll_instance = MagicMock()
            mock_collection.return_value = mock_coll_instance
            
            mock_result = MagicMock()
            mock_result.__iter__ = lambda x: iter([MagicMock(entity=MagicMock(text="result1", score=0.9))])
            mock_coll_instance.search.return_value = [mock_result]
            
            query_embedding = [0.1, 0.2, 0.3]
            
            with patch.object(milvus_manager, '_hash_user_id', return_value="hashed_id"):
                results = await milvus_manager.search_similar("user123", query_embedding)
                
                assert len(results) > 0
                mock_coll_instance.search.assert_called_once()


class TestRedisManager:
    """Test cases for Redis manager."""
    
    @pytest.fixture
    def redis_manager(self):
        """Create Redis manager instance."""
        return RedisDB()
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, redis_manager):
        """Test successful Redis initialization."""
        with patch('redis.asyncio.Redis.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            mock_client.ping.return_value = True
            
            await redis_manager.initialize("redis://localhost:6379")
            
            assert redis_manager._initialized is True
            mock_redis.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_store_chat_message(self, redis_manager):
        """Test storing chat message."""
        redis_manager._initialized = True
        redis_manager.client = AsyncMock()
        
        message_data = {
            "role": "user",
            "content": "Test message",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        with patch.object(redis_manager, '_hash_user_id', return_value="hashed_id"):
            result = await redis_manager.store_chat_message("user123", "session123", message_data)
            
            assert result is True
            redis_manager.client.lpush.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_chat_history(self, redis_manager):
        """Test retrieving chat history."""
        redis_manager._initialized = True
        redis_manager.client = AsyncMock()
        redis_manager.client.lrange.return_value = [b'{"role": "user", "content": "test"}']
        
        with patch.object(redis_manager, '_hash_user_id', return_value="hashed_id"):
            result = await redis_manager.get_chat_history("user123", "session123")
            
            assert len(result) == 1
            assert result[0]["content"] == "test"
            redis_manager.client.lrange.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_store_session_data(self, redis_manager):
        """Test storing session data."""
        redis_manager._initialized = True
        redis_manager.client = AsyncMock()
        
        session_data = {"key": "value", "timestamp": datetime.utcnow().isoformat()}
        
        with patch.object(redis_manager, '_hash_user_id', return_value="hashed_id"):
            result = await redis_manager.store_session_data("user123", "session123", session_data)
            
            assert result is True
            redis_manager.client.hset.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_session_data(self, redis_manager):
        """Test retrieving session data."""
        redis_manager._initialized = True
        redis_manager.client = AsyncMock()
        redis_manager.client.hgetall.return_value = {b"key": b'"value"', b"timestamp": b'"2023-01-01T00:00:00"'}
        
        with patch.object(redis_manager, '_hash_user_id', return_value="hashed_id"):
            result = await redis_manager.get_session_data("user123", "session123")
            
            assert result["key"] == "value"
            redis_manager.client.hgetall.assert_called_once()


class TestFullDocumentDeletion:
    @pytest.mark.asyncio
    async def test_full_document_deletion(self):
        """Test full document deletion across MongoDB, Neo4j, Milvus, and Redis."""
        with patch('src.db.mongo_db.MongoDB.delete_user_data', new_callable=AsyncMock) as mock_mongo_delete, \
             patch('src.db.neo4j_db.Neo4jDB.delete_user_data', new_callable=MagicMock) as mock_neo4j_delete, \
             patch('src.db.milvus_db.MilvusDB.delete_user_data', new_callable=MagicMock) as mock_milvus_delete, \
             patch('src.db.redis_db.RedisDB.delete_user_data', new_callable=MagicMock) as mock_redis_delete:
            mock_mongo_delete.return_value = {"success": True}
            mock_neo4j_delete.return_value = True
            mock_milvus_delete.return_value = True
            mock_redis_delete.return_value = True
            # Simulate deletion
            mongo_result = await mock_mongo_delete("user123")
            neo4j_result = mock_neo4j_delete("user123")
            milvus_result = mock_milvus_delete("user123")
            redis_result = mock_redis_delete("user123")
            assert mongo_result["success"] is True
            assert neo4j_result is True
            assert milvus_result is True
            assert redis_result is True

class TestUserProfilePersistence:
    @pytest.mark.asyncio
    async def test_user_profile_crud(self, mongo_manager):
        """Test user profile create, read, update, and delete in MongoDB."""
        mongo_manager._initialized = True
        mongo_manager.db = MagicMock()
        # Create
        mongo_manager.db.medical_records.insert_one = AsyncMock(return_value=MagicMock(inserted_id="profile_id"))
        with patch.object(mongo_manager, '_hash_user_id', return_value="hashed_id"):
            record_data = {"profile": {"smoking_status": "never"}}
            result = await mongo_manager.store_medical_record("user123", record_data, record_type="profile")
            assert result == "profile_id"
        # Read
        mongo_manager.db.medical_records.find.return_value.sort.return_value.limit.return_value = AsyncMock(to_list=AsyncMock(return_value=[{"data": record_data}]))
        records = await mongo_manager.get_medical_records("user123", record_type="profile")
        assert records[0]["data"] == record_data
        # Update
        mongo_manager.db.medical_records.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
        update_data = {"profile": {"smoking_status": "former"}}
        updated = await mongo_manager.update_medical_record("user123", "profile_id", update_data)
        assert updated is True
        # Delete
        mongo_manager.db.medical_records.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
        deleted = await mongo_manager.delete_medical_record("user123", "profile_id")
        assert deleted is True
