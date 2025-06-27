"""
Unit tests for timeline endpoints.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from src.api.endpoints.timeline import router
from src.utils.schema import TimelineEvent, TimelineResponse


class TestTimelineEndpoints:
    """Test cases for timeline endpoints."""

    @patch('src.api.endpoints.timeline.get_mongo')
    @patch('src.api.endpoints.timeline.get_graph')
    @patch('src.api.endpoints.timeline.log_user_action')
    async def test_get_timeline_success(self, mock_log, mock_graph, mock_mongo):
        """Test successful timeline retrieval."""
        # Mock database responses
        mock_mongo_client = AsyncMock()
        mock_mongo_client.get_timeline_events.return_value = [
            {
                "event_id": "test-event-1",
                "event_type": "medical",
                "title": "Blood Test",
                "description": "Routine blood work",
                "timestamp": "2024-01-01T10:00:00Z",
                "severity": "medium",
                "metadata": {}
            }
        ]
        mock_mongo.return_value = mock_mongo_client
        
        mock_neo4j_client = AsyncMock()
        mock_neo4j_client.get_patient_timeline.return_value = [
            {
                "event_id": "test-event-2",
                "event_type": "medical",
                "title": "Cardiology Visit",
                "description": "Routine cardiology checkup",
                "timestamp": "2024-01-02T14:00:00Z",
                "severity": "medium",
                "affected_body_parts": ["heart"]
            }
        ]
        mock_graph.return_value = mock_neo4j_client
        
        # Test the endpoint
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        
        with TestClient(app) as client:
            response = client.get("/timeline/?user_id=test-user&limit=10")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "events" in data
            assert "total_count" in data
            assert "date_range" in data
            assert len(data["events"]) == 2
            
            # Verify mock calls
            mock_mongo_client.get_timeline_events.assert_called_once_with("test-user", 10)
            mock_neo4j_client.get_patient_timeline.assert_called_once_with("test-user", 10)
            mock_log.assert_called_once()

    @patch('src.api.endpoints.timeline.get_mongo')
    @patch('src.api.endpoints.timeline.log_user_action')
    async def test_create_timeline_event_success(self, mock_log, mock_mongo):
        """Test successful timeline event creation."""
        mock_mongo_client = AsyncMock()
        mock_mongo_client.store_timeline_event.return_value = "test-event-id"
        mock_mongo.return_value = mock_mongo_client
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        
        with TestClient(app) as client:
            response = client.post("/timeline/event", params={
                "user_id": "test-user",
                "event_type": "medical",
                "title": "Test Event",
                "description": "Test event description",
                "severity": "medium"
            })
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["event_id"] == "test-event-id"
            assert data["message"] == "Timeline event created successfully"
            assert data["event_type"] == "medical"
            
            # Verify mock calls
            mock_mongo_client.store_timeline_event.assert_called_once()
            mock_log.assert_called_once()

    @patch('src.api.endpoints.timeline.get_mongo')
    @patch('src.api.endpoints.timeline.log_user_action')
    async def test_delete_timeline_event_success(self, mock_log, mock_mongo):
        """Test successful timeline event deletion."""
        mock_mongo_client = AsyncMock()
        mock_mongo_client.get_timeline_event.return_value = {
            "event_id": "test-event-id",
            "event_type": "medical",
            "title": "Test Event"
        }
        mock_mongo_client.delete_timeline_event.return_value = True
        mock_mongo.return_value = mock_mongo_client
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        
        with TestClient(app) as client:
            response = client.delete("/timeline/event/test-event-id?user_id=test-user")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["message"] == "Timeline event deleted successfully"
            assert data["event_id"] == "test-event-id"
            
            # Verify mock calls
            mock_mongo_client.get_timeline_event.assert_called_once_with("test-user", "test-event-id")
            mock_mongo_client.delete_timeline_event.assert_called_once_with("test-user", "test-event-id")
            mock_log.assert_called_once()

    @patch('src.api.endpoints.timeline.get_mongo')
    async def test_delete_timeline_event_not_found(self, mock_mongo):
        """Test timeline event deletion when event not found."""
        mock_mongo_client = AsyncMock()
        mock_mongo_client.get_timeline_event.return_value = None
        mock_mongo.return_value = mock_mongo_client
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        
        with TestClient(app) as client:
            response = client.delete("/timeline/event/nonexistent-id?user_id=test-user")
            
            assert response.status_code == 404
            data = response.json()
            assert "Timeline event not found" in data["detail"]

    @patch('src.api.endpoints.timeline.get_mongo')
    @patch('src.api.endpoints.timeline.log_user_action')
    async def test_get_timeline_summary_success(self, mock_log, mock_mongo):
        """Test successful timeline summary generation."""
        mock_mongo_client = AsyncMock()
        mock_mongo_client.get_timeline_events.return_value = [
            {
                "event_type": "medical",
                "severity": "medium",
                "timestamp": datetime.utcnow().isoformat()
            },
            {
                "event_type": "lifestyle",
                "severity": "low",
                "timestamp": (datetime.utcnow() - timedelta(days=1)).isoformat()
            }
        ]
        mock_mongo.return_value = mock_mongo_client
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        
        with TestClient(app) as client:
            response = client.get("/timeline/summary?user_id=test-user&days=30")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "period" in data
            assert "total_events" in data
            assert "event_types" in data
            assert "severity_distribution" in data
            assert "daily_activity" in data
            assert "trends" in data
            
            assert data["total_events"] == 2
            assert "medical" in data["event_types"]
            assert "lifestyle" in data["event_types"]
            
            # Verify mock calls
            mock_mongo_client.get_timeline_events.assert_called_once_with("test-user", limit=1000)
            mock_log.assert_called_once()

    @patch('src.api.endpoints.timeline.get_mongo')
    @patch('src.api.endpoints.timeline.log_user_action')
    async def test_search_timeline_events_success(self, mock_log, mock_mongo):
        """Test successful timeline event search."""
        mock_mongo_client = AsyncMock()
        mock_mongo_client.get_timeline_events.return_value = [
            {
                "event_type": "medical",
                "title": "Blood Test",
                "description": "Routine blood work",
                "severity": "medium",
                "timestamp": datetime.utcnow().isoformat()
            },
            {
                "event_type": "lifestyle", 
                "title": "Exercise",
                "description": "Morning run",
                "severity": "low",
                "timestamp": (datetime.utcnow() - timedelta(days=1)).isoformat()
            }
        ]
        mock_mongo.return_value = mock_mongo_client
        
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        
        with TestClient(app) as client:
            response = client.get("/timeline/search?user_id=test-user&event_type=medical&search_term=blood")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "events" in data
            assert "total_found" in data
            assert "returned" in data
            assert "filters_applied" in data
            
            # Should only return the medical event with "blood" in title
            assert data["returned"] == 1
            assert data["events"][0]["event_type"] == "medical"
            assert "blood" in data["events"][0]["title"].lower()
            
            # Verify mock calls
            mock_mongo_client.get_timeline_events.assert_called_once_with("test-user", limit=1000)
            mock_log.assert_called_once()

    def test_get_timeline_invalid_date_format(self):
        """Test timeline retrieval with invalid date format."""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        
        with TestClient(app) as client:
            response = client.get("/timeline/?user_id=test-user&start_date=invalid-date")
            
            assert response.status_code == 400
            data = response.json()
            assert "Invalid start_date format" in data["detail"]

    def test_create_timeline_event_invalid_timestamp(self):
        """Test timeline event creation with invalid timestamp."""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        
        with TestClient(app) as client:
            response = client.post("/timeline/event", params={
                "user_id": "test-user",
                "event_type": "medical",
                "title": "Test Event",
                "description": "Test description",
                "timestamp": "invalid-timestamp"
            })
            
            assert response.status_code == 400
            data = response.json()
            assert "Invalid timestamp format" in data["detail"]
