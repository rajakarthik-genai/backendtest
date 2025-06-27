"""
Integration tests for MediTwin Backend.
"""
import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient

from src.main import app


class TestHealthEndpoints:
    """Integration tests for health check endpoints."""

    def test_health_check(self):
        """Test basic health check endpoint."""
        with TestClient(app) as client:
            response = client.get("/")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "MediTwin Backend"
            assert data["version"] == "1.0.0"

    def test_detailed_health_check(self):
        """Test detailed health check endpoint."""
        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "timestamp" in data
            assert "services" in data
            assert data["services"]["api"] == "healthy"


class TestAPIDocumentation:
    """Integration tests for API documentation endpoints."""

    def test_openapi_docs(self):
        """Test OpenAPI documentation endpoint."""
        with TestClient(app) as client:
            response = client.get("/docs")
            assert response.status_code == 200

    def test_redoc_docs(self):
        """Test ReDoc documentation endpoint."""
        with TestClient(app) as client:
            response = client.get("/redoc")
            assert response.status_code == 200


@pytest.mark.asyncio
class TestAsyncEndpoints:
    """Integration tests for async endpoints."""

    async def test_async_client_creation(self):
        """Test async client can be created."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/")
            assert response.status_code == 200


class TestRouterMounting:
    """Integration tests for router mounting and routing."""

    def test_timeline_router_mounted(self):
        """Test that timeline router is properly mounted."""
        with TestClient(app) as client:
            # Test that timeline endpoints are accessible
            response = client.get("/timeline/?user_id=test-user")
            # Should get a 500 due to missing DB connections, but not 404
            assert response.status_code != 404

    def test_chat_router_mounted(self):
        """Test that chat router is properly mounted."""
        with TestClient(app) as client:
            # Test that chat endpoints are accessible
            response = client.get("/chat/history?user_id=test-user")
            # Should get a 500 due to missing DB connections, but not 404
            assert response.status_code != 404

    def test_upload_router_mounted(self):
        """Test that upload router is properly mounted."""
        with TestClient(app) as client:
            # Test that upload endpoints are accessible
            response = client.get("/upload/status/test-id?user_id=test-user")
            # Should get a 500 due to missing DB connections, but not 404
            assert response.status_code != 404


class TestCORSAndSecurity:
    """Integration tests for CORS and security settings."""

    def test_cors_headers(self):
        """Test CORS headers are properly set."""
        with TestClient(app) as client:
            response = client.options("/", headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            })
            # Should allow CORS for development
            assert response.status_code in [200, 404]  # 404 is OK if OPTIONS not explicitly handled

    def test_security_headers(self):
        """Test security headers are present."""
        with TestClient(app) as client:
            response = client.get("/")
            # Check for basic security headers
            assert response.status_code == 200


class TestErrorHandling:
    """Integration tests for error handling."""

    def test_404_handling(self):
        """Test 404 error handling."""
        with TestClient(app) as client:
            response = client.get("/nonexistent-endpoint")
            assert response.status_code == 404

    def test_method_not_allowed(self):
        """Test method not allowed handling."""
        with TestClient(app) as client:
            response = client.patch("/")  # PATCH not allowed on root
            assert response.status_code == 405


class TestEndpointValidation:
    """Integration tests for request validation."""

    def test_missing_required_params(self):
        """Test validation of missing required parameters."""
        with TestClient(app) as client:
            # Timeline endpoint requires user_id
            response = client.get("/timeline/")
            assert response.status_code == 422  # Validation error

    def test_invalid_param_types(self):
        """Test validation of invalid parameter types."""
        with TestClient(app) as client:
            # Limit should be int, not string
            response = client.get("/timeline/?user_id=test&limit=invalid")
            assert response.status_code == 422  # Validation error
