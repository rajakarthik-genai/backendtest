# API Testing Guide

This guide provides comprehensive instructions for testing the MediTwin API endpoints.

## 🧪 Testing Overview

The MediTwin API includes several endpoint categories:
- **Authentication**: User login/logout, token management
- **Document Processing**: Medical document upload and analysis
- **Chat Interface**: Conversational medical assistance
- **Health Monitoring**: System status and diagnostics
- **HIPAA Compliance**: Patient data security validation

## 🔧 Setup Testing Environment

### Prerequisites
```bash
# Install testing dependencies
uv add --dev pytest pytest-asyncio httpx

# Install the project
uv sync

# Start test environment
docker-compose up -d
```

### Environment Configuration
```bash
# Test environment variables
export API_BASE_URL="http://localhost:8000"
export TEST_USER_EMAIL="test@example.com"
export TEST_USER_PASSWORD="testpassword123"
```

## 🔐 Authentication Testing

### Manual Authentication Test
```bash
# Register a test user
curl -X POST "${API_BASE_URL}/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "full_name": "Test User"
  }'

# Login and get token
curl -X POST "${API_BASE_URL}/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123"
  }'

# Expected Response:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "token_type": "bearer",
#   "expires_in": 28800
# }
```

### Authentication Python Test
```python
import httpx
import asyncio

async def test_authentication():
    async with httpx.AsyncClient() as client:
        # Register user
        register_response = await client.post(
            "http://localhost:8000/auth/register",
            json={
                "email": "test@example.com",
                "password": "testpassword123",
                "full_name": "Test User"
            }
        )
        assert register_response.status_code == 201
        
        # Login
        login_response = await client.post(
            "http://localhost:8000/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123"
            }
        )
        assert login_response.status_code == 200
        
        token_data = login_response.json()
        assert "access_token" in token_data
        
        return token_data["access_token"]

# Run the test
token = asyncio.run(test_authentication())
print(f"Token: {token[:50]}...")
```

## 📄 Document Processing Testing

### Upload Medical Document
```bash
# Get authentication token first
TOKEN=$(curl -s -X POST "${API_BASE_URL}/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpassword123"}' \
  | jq -r '.access_token')

# Upload a medical document
curl -X POST "${API_BASE_URL}/documents/upload" \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "file=@test_medical_report.txt" \
  -F "document_type=medical_report"

# Expected Response:
# {
#   "document_id": "doc_123456",
#   "filename": "test_medical_report.txt",
#   "document_type": "medical_report",
#   "status": "uploaded",
#   "upload_time": "2024-01-15T10:30:00Z"
# }
```

### Check Document Status
```bash
# Check processing status
curl -X GET "${API_BASE_URL}/documents/doc_123456/status" \
  -H "Authorization: Bearer ${TOKEN}"

# Expected Response:
# {
#   "document_id": "doc_123456",
#   "status": "processed",
#   "processing_time": 45.2,
#   "extracted_entities": 25,
#   "confidence_score": 0.92
# }
```

### Python Document Test
```python
import httpx
import asyncio
from pathlib import Path

async def test_document_processing():
    async with httpx.AsyncClient() as client:
        # Login first
        login_response = await client.post(
            "http://localhost:8000/auth/login",
            json={"email": "test@example.com", "password": "testpassword123"}
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Upload document
        with open("test_medical_report.txt", "rb") as f:
            upload_response = await client.post(
                "http://localhost:8000/documents/upload",
                headers=headers,
                files={"file": f},
                data={"document_type": "medical_report"}
            )
        
        assert upload_response.status_code == 201
        doc_data = upload_response.json()
        doc_id = doc_data["document_id"]
        
        # Wait for processing
        await asyncio.sleep(5)
        
        # Check status
        status_response = await client.get(
            f"http://localhost:8000/documents/{doc_id}/status",
            headers=headers
        )
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        assert status_data["status"] in ["processing", "processed"]
        
        return doc_id

# Run the test
doc_id = asyncio.run(test_document_processing())
print(f"Document ID: {doc_id}")
```

## 💬 Chat Interface Testing

### Start Chat Session
```bash
# Start a new chat session
curl -X POST "${API_BASE_URL}/chat/start" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "context": "medical_consultation",
    "patient_id": "patient_123"
  }'

# Expected Response:
# {
#   "session_id": "chat_789",
#   "status": "active",
#   "context": "medical_consultation",
#   "created_at": "2024-01-15T10:35:00Z"
# }
```

### Send Chat Message
```bash
# Send a message to the chat
curl -X POST "${API_BASE_URL}/chat/chat_789/message" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What can you tell me about my recent blood work results?",
    "include_medical_context": true
  }'

# Expected Response:
# {
#   "response": "Based on your recent blood work from document doc_123456, I can see that your hemoglobin levels are within normal range at 14.2 g/dL...",
#   "confidence": 0.89,
#   "sources": ["doc_123456"],
#   "session_id": "chat_789"
# }
```

### Python Chat Test
```python
async def test_chat_functionality():
    async with httpx.AsyncClient() as client:
        # Login and get token
        login_response = await client.post(
            "http://localhost:8000/auth/login",
            json={"email": "test@example.com", "password": "testpassword123"}
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Start chat session
        chat_response = await client.post(
            "http://localhost:8000/chat/start",
            headers=headers,
            json={"context": "medical_consultation", "patient_id": "patient_123"}
        )
        assert chat_response.status_code == 201
        
        session_id = chat_response.json()["session_id"]
        
        # Send message
        message_response = await client.post(
            f"http://localhost:8000/chat/{session_id}/message",
            headers=headers,
            json={
                "message": "What's my current health status?",
                "include_medical_context": True
            }
        )
        assert message_response.status_code == 200
        
        response_data = message_response.json()
        assert "response" in response_data
        assert len(response_data["response"]) > 0
        
        return session_id

# Run the test
session_id = asyncio.run(test_chat_functionality())
print(f"Chat Session: {session_id}")
```

## 🏥 Health Check Testing

### System Health Check
```bash
# Check overall system health
curl -X GET "${API_BASE_URL}/health"

# Expected Response:
# {
#   "status": "healthy",
#   "timestamp": "2024-01-15T10:40:00Z",
#   "services": {
#     "database": "healthy",
#     "vector_store": "healthy",
#     "memory_store": "healthy",
#     "knowledge_graph": "healthy"
#   },
#   "version": "1.0.0"
# }
```

### Detailed Health Check
```bash
# Get detailed health information
curl -X GET "${API_BASE_URL}/health/detailed" \
  -H "Authorization: Bearer ${TOKEN}"

# Expected Response:
# {
#   "status": "healthy",
#   "services": {
#     "mongodb": {
#       "status": "healthy",
#       "response_time": 12.5,
#       "connections": 5
#     },
#     "neo4j": {
#       "status": "healthy",
#       "response_time": 8.3,
#       "nodes": 1250,
#       "relationships": 3420
#     },
#     "redis": {
#       "status": "healthy",
#       "response_time": 2.1,
#       "memory_usage": "45%"
#     },
#     "milvus": {
#       "status": "healthy",
#       "response_time": 15.7,
#       "collections": 3,
#       "vectors": 15420
#     }
#   }
# }
```

## 🔒 HIPAA Compliance Testing

### Patient Data Isolation Test
```bash
# Test patient data isolation
curl -X POST "${API_BASE_URL}/hipaa/validate-isolation" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "patient_123",
    "test_type": "data_isolation"
  }'

# Expected Response:
# {
#   "validation_id": "hipaa_val_456",
#   "patient_id": "patient_123",
#   "test_type": "data_isolation",
#   "result": "PASS",
#   "details": {
#     "isolated_data_points": 156,
#     "cross_patient_leaks": 0,
#     "security_violations": 0
#   },
#   "timestamp": "2024-01-15T10:45:00Z"
# }
```

### Audit Trail Test
```bash
# Check audit trail
curl -X GET "${API_BASE_URL}/hipaa/audit-trail?patient_id=patient_123" \
  -H "Authorization: Bearer ${TOKEN}"

# Expected Response:
# {
#   "patient_id": "patient_123",
#   "audit_entries": [
#     {
#       "timestamp": "2024-01-15T10:30:00Z",
#       "action": "document_upload",
#       "user_id": "user_123",
#       "document_id": "doc_123456",
#       "ip_address": "192.168.1.100"
#     },
#     {
#       "timestamp": "2024-01-15T10:35:00Z",
#       "action": "chat_session_start",
#       "user_id": "user_123",
#       "session_id": "chat_789",
#       "ip_address": "192.168.1.100"
#     }
#   ],
#   "total_entries": 2
# }
```

## 🧪 Automated Testing Suite

### Run All Tests
```bash
# Run the complete test suite
uv run pytest tests/ -v

# Run specific test categories
uv run pytest tests/test_health_check.py -v
uv run pytest tests/test_comprehensive.py -v
uv run pytest tests/unit/ -v
uv run pytest tests/integration/ -v

# Run tests with coverage
uv run pytest tests/ --cov=src --cov-report=html
```

### Test Configuration
```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
markers =
    unit: Unit tests
    integration: Integration tests
    health: Health check tests
    hipaa: HIPAA compliance tests
    slow: Slow-running tests
```

### Custom Test Fixtures
```python
# tests/conftest.py
import pytest
import httpx
import asyncio
from typing import AsyncGenerator

@pytest.fixture
async def auth_token() -> str:
    """Get authentication token for testing."""
    async with httpx.AsyncClient() as client:
        # Login
        response = await client.post(
            "http://localhost:8000/auth/login",
            json={"email": "test@example.com", "password": "testpassword123"}
        )
        return response.json()["access_token"]

@pytest.fixture
async def authenticated_client(auth_token: str) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Get authenticated HTTP client."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    async with httpx.AsyncClient(headers=headers) as client:
        yield client

@pytest.fixture
async def test_document(authenticated_client: httpx.AsyncClient) -> str:
    """Upload a test document and return document ID."""
    with open("test_medical_report.txt", "rb") as f:
        response = await authenticated_client.post(
            "http://localhost:8000/documents/upload",
            files={"file": f},
            data={"document_type": "medical_report"}
        )
    return response.json()["document_id"]
```

## 📊 Performance Testing

### Load Testing with Locust
```python
# locustfile.py
from locust import HttpUser, task, between
import json

class MediTwinUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login and get token."""
        response = self.client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "testpassword123"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def check_health(self):
        """Health check endpoint."""
        self.client.get("/health")
    
    @task(2)
    def chat_message(self):
        """Send chat messages."""
        # Start session
        session_response = self.client.post(
            "/chat/start",
            headers=self.headers,
            json={"context": "medical_consultation", "patient_id": "patient_123"}
        )
        session_id = session_response.json()["session_id"]
        
        # Send message
        self.client.post(
            f"/chat/{session_id}/message",
            headers=self.headers,
            json={"message": "What's my health status?"}
        )
    
    @task(1)
    def upload_document(self):
        """Upload test documents."""
        files = {"file": ("test.txt", "Test medical report content", "text/plain")}
        data = {"document_type": "medical_report"}
        self.client.post(
            "/documents/upload",
            headers=self.headers,
            files=files,
            data=data
        )

# Run load test:
# locust -f locustfile.py --host=http://localhost:8000
```

### Stress Testing
```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test health endpoint
ab -n 1000 -c 10 http://localhost:8000/health

# Test with authentication
ab -n 500 -c 5 -H "Authorization: Bearer ${TOKEN}" http://localhost:8000/health/detailed
```

## 🔍 Debugging Failed Tests

### Common Test Failures

#### Authentication Errors
```python
# Debug authentication issues
async def debug_auth():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8000/auth/login",
                json={"email": "test@example.com", "password": "testpassword123"}
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

# Check if user exists
# curl -X GET "http://localhost:8000/auth/users" -H "Authorization: Bearer ${TOKEN}"
```

#### Database Connection Issues
```python
# Test database connectivity
async def debug_database():
    from src.db.mongodb import get_database
    from src.db.neo4j import Neo4jDatabase
    from src.db.redis import get_redis_client
    
    try:
        # Test MongoDB
        db = await get_database()
        print(f"MongoDB: Connected to {db.name}")
        
        # Test Neo4j
        neo4j = Neo4jDatabase()
        result = await neo4j.test_connection()
        print(f"Neo4j: {result}")
        
        # Test Redis
        redis = await get_redis_client()
        await redis.ping()
        print("Redis: Connected")
        
    except Exception as e:
        print(f"Database Error: {e}")
```

#### Document Processing Issues
```python
# Debug document processing
async def debug_document_processing():
    # Check if file exists
    import os
    if not os.path.exists("test_medical_report.txt"):
        print("Test file missing!")
        return
    
    # Check file size
    size = os.path.getsize("test_medical_report.txt")
    print(f"File size: {size} bytes")
    
    # Test upload without auth
    async with httpx.AsyncClient() as client:
        response = await client.post("http://localhost:8000/documents/upload")
        print(f"No auth response: {response.status_code}")
```

### Test Environment Issues

#### Docker Services Not Running
```bash
# Check Docker services
docker-compose ps

# Restart services
docker-compose down
docker-compose up -d

# Check logs
docker-compose logs api
docker-compose logs mongodb
```

#### Port Conflicts
```bash
# Check if ports are in use
netstat -tulpn | grep :8000
netstat -tulpn | grep :27017

# Kill processes using ports
sudo lsof -t -i:8000 | xargs kill -9
```

## 📝 Test Reporting

### HTML Test Reports
```bash
# Generate HTML test report
uv run pytest tests/ --html=reports/test_report.html --self-contained-html

# Generate coverage report
uv run pytest tests/ --cov=src --cov-report=html:reports/coverage
```

### CI/CD Integration
```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      mongodb:
        image: mongo:7
        ports:
          - 27017:27017
      
      redis:
        image: redis:7
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install UV
      run: pip install uv
    
    - name: Install dependencies
      run: uv sync
    
    - name: Run tests
      run: |
        uv run pytest tests/ --junitxml=reports/junit.xml --cov=src --cov-report=xml:reports/coverage.xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: reports/coverage.xml
```

## 🎯 Test Best Practices

### Test Organization
1. **Unit Tests**: Test individual functions/classes
2. **Integration Tests**: Test component interactions
3. **Health Tests**: Monitor system status
4. **HIPAA Tests**: Validate compliance
5. **Performance Tests**: Check scalability

### Test Data Management
```python
# Use factories for test data
class TestDataFactory:
    @staticmethod
    def create_test_user():
        return {
            "email": f"test_{uuid.uuid4()}@example.com",
            "password": "testpassword123",
            "full_name": "Test User"
        }
    
    @staticmethod
    def create_test_document():
        return {
            "content": "Patient presents with mild symptoms...",
            "document_type": "medical_report",
            "patient_id": f"patient_{uuid.uuid4()}"
        }
```

### Test Cleanup
```python
# Always clean up test data
@pytest.fixture(autouse=True)
async def cleanup_test_data():
    yield
    # Clean up after each test
    await cleanup_test_users()
    await cleanup_test_documents()
    await cleanup_test_sessions()
```

This comprehensive testing guide ensures your MediTwin API is thoroughly validated and ready for production use!
