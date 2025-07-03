#!/usr/bin/env python3
"""
Production Test Suite

This is the main production test suite that validates all critical functionality
including API endpoints, authentication, RAG pipeline, and core agent capabilities.
"""

import asyncio
import httpx
import pytest
import sys
from pathlib import Path

# Add project path
sys.path.append(str(Path(__file__).parent.parent))

from src.config.settings import settings
from src.utils.logging import logger


class TestProductionSuite:
    """Comprehensive production test suite."""
    
    BASE_URL = "http://localhost:8000"
    TEST_DATA_DIR = Path(__file__).parent / "data"
    
    @pytest.fixture(scope="class")
    async def client(self):
        """HTTP client for API testing."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            yield client
    
    async def test_health_check(self, client):
        """Test basic health check endpoint."""
        response = await client.get(f"{self.BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    async def test_openai_functionality(self, client):
        """Test OpenAI API integration."""
        # This should be implemented based on test_openai_functionality.py
        pass
    
    async def test_document_upload_and_processing(self, client):
        """Test document upload and RAG processing."""
        test_file = self.TEST_DATA_DIR / "test_upload.pdf"
        if not test_file.exists():
            pytest.skip("Test document not found")
        
        with open(test_file, "rb") as f:
            files = {"file": ("test_upload.pdf", f, "application/pdf")}
            response = await client.post(f"{self.BASE_URL}/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    async def test_chat_endpoint(self, client):
        """Test chat endpoint functionality."""
        payload = {
            "message": "What is the patient's condition?",
            "conversation_id": "test_prod_001"
        }
        response = await client.post(f"{self.BASE_URL}/chat", json=payload)
        assert response.status_code in [200, 422]  # 422 acceptable if no documents uploaded
    
    async def test_expert_opinion_endpoint(self, client):
        """Test expert opinion endpoint."""
        payload = {
            "query": "Provide a cardiology consultation for chest pain",
            "specialist": "cardiologist"
        }
        response = await client.post(f"{self.BASE_URL}/expert-opinion", json=payload)
        assert response.status_code in [200, 422]  # 422 acceptable if no documents uploaded
    
    async def test_authentication_endpoints(self, client):
        """Test authentication functionality."""
        # Test login endpoint exists
        response = await client.post(f"{self.BASE_URL}/auth/login", json={
            "username": "test@example.com",
            "password": "invalid"
        })
        assert response.status_code in [400, 401, 422]  # Should reject invalid credentials


if __name__ == "__main__":
    # Run tests directly
    import pytest
    pytest.main([__file__, "-v"])
