"""
Unit tests for database modules.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from typing import Dict, Any

from src.db.mongo_db import MongoDBManager
from src.db.neo4j_db import Neo4jManager
from src.db.milvus_db import MilvusManager
from src.db.redis_db import RedisManager


class TestMongoDBManager:
    """Test cases for MongoDB manager."""
    
    @pytest.fixture
    def mongo_manager(self):
        """Create MongoDB manager instance."""
        return MongoDBManager()
    
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
        return Neo4jManager()
    
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
        return MilvusManager()
    
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
        return RedisManager()
    
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
