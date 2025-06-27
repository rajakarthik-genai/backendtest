"""
Integration tests for the MediTwin backend API endpoints.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock
import json
from datetime import datetime

from src.main import app


class TestTimelineEndpoints:
    """Integration tests for timeline endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_timeline_success(self):
        """Test successful timeline retrieval."""
        mock_mongo_events = [
            {
                "event_id": "event_1",
                "event_type": "medical",
                "title": "Check-up",
                "description": "Annual check-up",
                "timestamp": "2023-06-01T10:00:00",
                "severity": "low",
                "metadata": {}
            }
        ]
        
        mock_neo4j_events = [
            {
                "event_id": "event_2",
                "event_type": "medical",
                "title": "Blood Test",
                "description": "Routine blood work",
                "timestamp": "2023-06-02T11:00:00",
                "severity": "medium",
                "affected_body_parts": ["arm"]
            }
        ]
        
        with patch('src.db.mongo_db.get_mongo') as mock_get_mongo:
            with patch('src.db.neo4j_db.get_graph') as mock_get_graph:
                mock_mongo = AsyncMock()
                mock_mongo.get_timeline_events.return_value = mock_mongo_events
                mock_get_mongo.return_value = mock_mongo
                
                mock_neo4j = MagicMock()
                mock_neo4j.get_patient_timeline.return_value = mock_neo4j_events
                mock_get_graph.return_value = mock_neo4j
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.get("/timeline/?user_id=test_user&limit=10")
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert "events" in data
                    assert "total_count" in data
                    assert len(data["events"]) == 2
    
    @pytest.mark.asyncio
    async def test_create_timeline_event_success(self):
        """Test successful timeline event creation."""
        with patch('src.db.mongo_db.get_mongo') as mock_get_mongo:
            with patch('src.db.neo4j_db.get_graph') as mock_get_graph:
                mock_mongo = AsyncMock()
                mock_mongo.store_timeline_event.return_value = "event_123"
                mock_get_mongo.return_value = mock_mongo
                
                mock_neo4j = MagicMock()
                mock_get_graph.return_value = mock_neo4j
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.post("/timeline/event", params={
                        "user_id": "test_user",
                        "event_type": "medical",
                        "title": "Test Event",
                        "description": "Test Description",
                        "severity": "medium"
                    })
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["event_id"] == "event_123"
                    assert "message" in data
    
    @pytest.mark.asyncio
    async def test_update_timeline_event_success(self):
        """Test successful timeline event update."""
        existing_event = {
            "event_id": "event_123",
            "event_type": "medical",
            "title": "Original Title",
            "description": "Original Description"
        }
        
        with patch('src.db.mongo_db.get_mongo') as mock_get_mongo:
            mock_mongo = AsyncMock()
            mock_mongo.get_timeline_event.return_value = existing_event
            mock_mongo.update_timeline_event.return_value = True
            mock_get_mongo.return_value = mock_mongo
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.put("/timeline/event/event_123", 
                    params={"user_id": "test_user"},
                    data={"title": "Updated Title"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["event_id"] == "event_123"
                assert "updated_fields" in data
    
    @pytest.mark.asyncio
    async def test_delete_timeline_event_success(self):
        """Test successful timeline event deletion."""
        existing_event = {
            "event_id": "event_123",
            "event_type": "medical"
        }
        
        with patch('src.db.mongo_db.get_mongo') as mock_get_mongo:
            mock_mongo = AsyncMock()
            mock_mongo.get_timeline_event.return_value = existing_event
            mock_mongo.delete_timeline_event.return_value = True
            mock_get_mongo.return_value = mock_mongo
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.delete("/timeline/event/event_123?user_id=test_user")
                
                assert response.status_code == 200
                data = response.json()
                assert data["event_id"] == "event_123"
    
    @pytest.mark.asyncio
    async def test_get_timeline_summary(self):
        """Test timeline summary endpoint."""
        mock_events = [
            {
                "event_type": "medical",
                "severity": "high",
                "timestamp": "2023-06-01T10:00:00"
            },
            {
                "event_type": "lifestyle",
                "severity": "low", 
                "timestamp": "2023-06-02T10:00:00"
            }
        ]
        
        with patch('src.db.mongo_db.get_mongo') as mock_get_mongo:
            mock_mongo = AsyncMock()
            mock_mongo.get_timeline_events.return_value = mock_events
            mock_get_mongo.return_value = mock_mongo
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/timeline/summary?user_id=test_user&days=30")
                
                assert response.status_code == 200
                data = response.json()
                assert "total_events" in data
                assert "event_types" in data
                assert "severity_distribution" in data
    
    @pytest.mark.asyncio
    async def test_search_timeline_events(self):
        """Test timeline search endpoint."""
        mock_events = [
            {
                "event_type": "medical",
                "title": "Blood Test",
                "description": "Routine blood work",
                "severity": "medium",
                "timestamp": "2023-06-01T10:00:00"
            }
        ]
        
        with patch('src.db.mongo_db.get_mongo') as mock_get_mongo:
            mock_mongo = AsyncMock()
            mock_mongo.get_timeline_events.return_value = mock_events
            mock_get_mongo.return_value = mock_mongo
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/timeline/search?user_id=test_user&event_type=medical&search_term=blood")
                
                assert response.status_code == 200
                data = response.json()
                assert "events" in data
                assert "total_found" in data
                assert "filters_applied" in data


class TestChatEndpoints:
    """Integration tests for chat endpoints."""
    
    @pytest.mark.asyncio
    async def test_chat_endpoint_success(self):
        """Test successful chat interaction."""
        with patch('src.agents.orchestrator_agent.get_orchestrator') as mock_get_orchestrator:
            mock_orchestrator = AsyncMock()
            mock_response = {
                "response": "Test medical response",
                "confidence": 8,
                "sources": ["Medical database"],
                "session_id": "session_123"
            }
            mock_orchestrator.process_query.return_value = mock_response
            mock_get_orchestrator.return_value = mock_orchestrator
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post("/chat/", json={
                    "message": "I have a headache",
                    "user_id": "test_user",
                    "session_id": "session_123"
                })
                
                assert response.status_code == 200
                data = response.json()
                assert "response" in data
                assert "confidence" in data
                assert "sources" in data
    
    @pytest.mark.asyncio
    async def test_chat_history_endpoint(self):
        """Test chat history retrieval."""
        mock_history = [
            {
                "role": "user",
                "content": "I have a headache",
                "timestamp": "2023-06-01T10:00:00"
            },
            {
                "role": "assistant", 
                "content": "Based on your symptoms...",
                "timestamp": "2023-06-01T10:01:00"
            }
        ]
        
        with patch('src.db.redis_db.get_redis') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.get_chat_history.return_value = mock_history
            mock_get_redis.return_value = mock_redis
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/chat/history?user_id=test_user&session_id=session_123")
                
                assert response.status_code == 200
                data = response.json()
                assert "messages" in data
                assert len(data["messages"]) == 2


class TestUploadEndpoints:
    """Integration tests for upload endpoints."""
    
    @pytest.mark.asyncio
    async def test_upload_document_success(self):
        """Test successful document upload."""
        with patch('src.agents.ingestion_agent.get_ingestion_agent') as mock_get_ingestion:
            mock_ingestion = AsyncMock()
            mock_ingestion.process_document.return_value = {
                "document_id": "doc_123",
                "status": "completed",
                "entities_extracted": 5
            }
            mock_get_ingestion.return_value = mock_ingestion
            
            # Mock file content
            file_content = b"PDF content here"
            files = {"file": ("test.pdf", file_content, "application/pdf")}
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post("/upload/document", 
                    files=files,
                    data={"user_id": "test_user"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "document_id" in data
                assert "status" in data
    
    @pytest.mark.asyncio
    async def test_upload_status_endpoint(self):
        """Test upload status checking."""
        mock_status = {
            "document_id": "doc_123",
            "status": "processing",
            "progress": 50,
            "stages_completed": ["extraction", "parsing"]
        }
        
        with patch('src.db.mongo_db.get_mongo') as mock_get_mongo:
            mock_mongo = AsyncMock()
            mock_mongo.get_document_metadata.return_value = mock_status
            mock_get_mongo.return_value = mock_mongo
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/upload/status/doc_123?user_id=test_user")
                
                assert response.status_code == 200
                data = response.json()
                assert data["document_id"] == "doc_123"
                assert data["status"] == "processing"


class TestHealthEndpoints:
    """Integration tests for health check endpoints."""
    
    @pytest.mark.asyncio
    async def test_health_check_basic(self):
        """Test basic health check endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "MediTwin Backend"
    
    @pytest.mark.asyncio 
    async def test_detailed_health_check(self):
        """Test detailed health check endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "services" in data
            assert "timestamp" in data


class TestErrorHandling:
    """Integration tests for error handling."""
    
    @pytest.mark.asyncio
    async def test_timeline_user_isolation(self):
        """Test that users can only access their own timeline data."""
        with patch('src.db.mongo_db.get_mongo') as mock_get_mongo:
            mock_mongo = AsyncMock()
            mock_mongo.get_timeline_events.return_value = []
            mock_get_mongo.return_value = mock_mongo
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/timeline/?user_id=different_user")
                
                assert response.status_code == 200
                # Should return empty results due to user isolation
                data = response.json()
                assert len(data["events"]) == 0
    
    @pytest.mark.asyncio
    async def test_invalid_user_id_format(self):
        """Test handling of invalid user ID format."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/timeline/?user_id=")
            
            assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_timeline_event_not_found(self):
        """Test 404 response for non-existent timeline event."""
        with patch('src.db.mongo_db.get_mongo') as mock_get_mongo:
            mock_mongo = AsyncMock()
            mock_mongo.get_timeline_event.return_value = None
            mock_get_mongo.return_value = mock_mongo
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.delete("/timeline/event/nonexistent?user_id=test_user")
                
                assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_database_connection_error(self):
        """Test handling of database connection errors."""
        with patch('src.db.mongo_db.get_mongo') as mock_get_mongo:
            mock_get_mongo.side_effect = Exception("Database connection failed")
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/timeline/?user_id=test_user")
                
                assert response.status_code == 500
