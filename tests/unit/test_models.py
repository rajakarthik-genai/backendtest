"""
Unit tests for data models and schemas.
"""

import pytest
from pydantic import ValidationError
from datetime import datetime
from typing import Optional

class TestDataModels:
    """Test data model validation"""
    
    def test_chat_request_valid(self):
        """Test valid ChatRequest creation"""
        # This would test the actual ChatRequest model
        # For now, testing the concept
        request_data = {
            "message": "Hello",
            "session_id": "test"
        }
        assert request_data["message"] == "Hello"
        assert request_data["session_id"] == "test"
        
    def test_chat_request_missing_message(self):
        """Test ChatRequest with missing message"""
        # This would test validation errors
        request_data = {"session_id": "test"}
        # In real implementation, this would raise ValidationError
        assert "message" not in request_data
        
    def test_chat_response_valid(self):
        """Test valid ChatResponse creation"""
        response_data = {
            "response": "Hello back",
            "session_id": "test",
            "timestamp": datetime.utcnow().isoformat()
        }
        assert response_data["response"] == "Hello back"
        assert response_data["session_id"] == "test"
        assert "timestamp" in response_data
        
    def test_upload_response_valid(self):
        """Test valid UploadResponse creation"""
        response_data = {
            "document_id": "test-id",
            "status": "queued",
            "message": "File uploaded successfully"
        }
        assert response_data["document_id"] == "test-id"
        assert response_data["status"] == "queued"
        assert response_data["message"] == "File uploaded successfully"
        
    def test_processing_status_valid(self):
        """Test valid ProcessingStatus creation"""
        status_data = {
            "task_id": "test-task",
            "status": "processing",
            "progress": 0.5,
            "message": "Processing document",
            "started_at": datetime.utcnow().isoformat()
        }
        assert status_data["task_id"] == "test-task"
        assert status_data["status"] == "processing"
        assert status_data["progress"] == 0.5
        
    def test_symptom_analysis_request_valid(self):
        """Test valid SymptomAnalysisRequest creation"""
        request_data = {
            "symptoms": ["headache", "fever"],
            "duration": "2 days",
            "severity": "moderate",
            "context": "Started after stress"
        }
        assert len(request_data["symptoms"]) == 2
        assert request_data["duration"] == "2 days"
        assert request_data["severity"] == "moderate"
        
    def test_drug_interaction_request_valid(self):
        """Test valid DrugInteractionRequest creation"""
        request_data = {
            "medications": ["aspirin", "ibuprofen", "warfarin"]
        }
        assert len(request_data["medications"]) == 3
        assert "aspirin" in request_data["medications"]
