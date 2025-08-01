# Developer Guide

This guide provides comprehensive information for developers working on the MediTwin system.

## 🚀 Getting Started

### Development Environment Setup

#### Prerequisites
- Python 3.10 or higher
- UV package manager
- Docker and Docker Compose
- Git

#### Initial Setup
```bash
# Clone the repository
git clone <repository-url>
cd meditwin-agents

# Create and activate virtual environment with UV
uv sync

# Copy environment configuration
cp .env.example .env

# Edit .env with your local configuration
nano .env
```

#### Environment Variables
```bash
# Development Database URLs
MONGODB_URL=mongodb://localhost:27017/meditwin_dev
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=dev_password
REDIS_URL=redis://localhost:6379/0
MILVUS_HOST=localhost
MILVUS_PORT=19530

# Development API Settings
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=true
LOG_LEVEL=DEBUG

# JWT Settings for Development
JWT_SECRET_KEY=dev-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# AI Model Configuration
OPENAI_API_KEY=your-development-api-key
EMBEDDING_MODEL=text-embedding-3-small
CHAT_MODEL=gpt-4-turbo-preview
```

### Database Setup

#### Using Docker (Recommended)
```bash
# Start all databases
docker-compose up -d mongodb neo4j redis milvus

# Verify databases are running
docker-compose ps
```

#### Manual Setup
```bash
# MongoDB
sudo systemctl start mongod

# Neo4j
sudo systemctl start neo4j

# Redis
sudo systemctl start redis

# Milvus (requires Docker)
docker run -d --name milvus_standalone -p 19530:19530 milvusdb/milvus:latest
```

#### Database Initialization
```bash
# Initialize database schemas and constraints
uv run python scripts/init_databases.py

# Apply HIPAA compliance fixes
uv run python hipaa_compliance_fix.py

# Create test data (optional)
uv run python scripts/create_test_data.py
```

## 🏗️ Project Structure

```
meditwin-agents/
├── src/                          # Main application code
│   ├── agents/                   # AI agents
│   │   ├── orchestrator_agent.py
│   │   ├── medical_agent.py
│   │   ├── chat_agent.py
│   │   └── ingestion_agent.py
│   ├── api/                      # FastAPI routes
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── chat.py
│   │   │   └── documents.py
│   │   └── dependencies.py
│   ├── auth/                     # Authentication system
│   │   ├── jwt_handler.py
│   │   └── password_utils.py
│   ├── chat/                     # Memory management
│   │   ├── short_term.py
│   │   └── long_term.py
│   ├── core/                     # Core utilities
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   └── logging.py
│   ├── db/                       # Database connections
│   │   ├── mongodb.py
│   │   ├── neo4j.py
│   │   ├── redis_db.py
│   │   └── milvus_client.py
│   ├── models/                   # Data models
│   ├── services/                 # Business logic
│   ├── utils/                    # Utility functions
│   └── main.py                   # Application entry point
├── tests/                        # Test suite
│   ├── test_health_check.py      # System health tests
│   ├── test_comprehensive.py     # Integration tests
│   ├── unit/                     # Unit tests
│   └── integration/              # Integration tests
├── docs/                         # Documentation
├── scripts/                      # Utility scripts
├── docker-compose.yml            # Docker configuration
├── pyproject.toml               # Project configuration
└── README.md                    # Project overview
```

## 🔧 Development Workflow

### Running the Application

#### Development Server
```bash
# Start with auto-reload
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Start with debug logging
uv run uvicorn src.main:app --reload --log-level debug

# Start with specific workers
uv run uvicorn src.main:app --workers 4
```

#### Production Mode
```bash
# Start production server
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Code Quality

#### Formatting and Linting
```bash
# Format code with Black
uv run black src/ tests/

# Sort imports
uv run isort src/ tests/

# Lint with flake8
uv run flake8 src/ tests/

# Type checking with mypy
uv run mypy src/
```

#### Pre-commit Hooks
```bash
# Install pre-commit hooks
uv run pre-commit install

# Run manually
uv run pre-commit run --all-files
```

### Testing

#### Running Tests
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test files
uv run pytest tests/unit/test_database.py
uv run pytest tests/integration/test_api_integration.py

# Run health checks
uv run python tests/test_health_check.py
```

#### Test Categories
1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test component interactions
3. **Health Checks**: Test system-wide health and connectivity
4. **Comprehensive Tests**: Full end-to-end testing

#### Writing Tests
```python
# Unit test example
import pytest
from src.db.neo4j import Neo4jConnection

class TestNeo4jConnection:
    def test_connection_initialization(self):
        conn = Neo4jConnection()
        assert conn is not None
        assert hasattr(conn, 'validate_patient_isolation')

# Integration test example
@pytest.mark.asyncio
async def test_chat_endpoint():
    with patch('src.auth.jwt_handler.decode_jwt') as mock_decode:
        mock_decode.return_value = {"user_id": "test"}
        response = client.post("/api/chat/message", json={"message": "Hello"})
        assert response.status_code in [200, 422]
```

## 🗄️ Database Development

### MongoDB Development

#### Collections Structure
```javascript
// Users collection
{
  "_id": ObjectId,
  "email": "user@example.com",
  "hashed_password": "bcrypt_hash",
  "full_name": "User Name",
  "role": "patient|doctor|admin",
  "is_active": true,
  "created_at": ISODate,
  "patient_id": "unique_patient_id"
}

// Documents collection
{
  "_id": ObjectId,
  "patient_id": "patient_123",
  "filename": "lab_results.pdf",
  "content_type": "application/pdf",
  "file_size": 1024567,
  "status": "processed|processing|failed",
  "uploaded_at": ISODate,
  "processed_at": ISODate,
  "metadata": {}
}
```

#### Database Operations
```python
from src.db.mongodb import get_database

async def create_patient_record(patient_data):
    db = await get_database()
    collection = db.patients
    result = await collection.insert_one(patient_data)
    return str(result.inserted_id)
```

### Neo4j Development

#### Graph Schema
```cypher
// Patient nodes
(:Patient {patient_id: "patient_123", name: "John Doe"})

// Body part nodes (HIPAA compliant)
(:BodyPart {name: "heart", patient_id: "patient_123", severity: 0.8})

// Event nodes
(:Event {event_id: "event_123", patient_id: "patient_123", type: "diagnosis"})

// Relationships
(:Patient)-[:HAS_BODY_PART]->(:BodyPart)
(:Patient)-[:HAS_EVENT]->(:Event)
(:Document)-[:CONTAINS_EVENT]->(:Event)
```

#### HIPAA Compliance in Neo4j
```python
# Always include patient_id in node creation
def create_body_part(patient_id: str, body_part: str):
    query = """
    MATCH (p:Patient {patient_id: $patient_id})
    MERGE (bp:BodyPart {name: $body_part, patient_id: $patient_id})
    MERGE (p)-[:HAS_BODY_PART]->(bp)
    """
    neo4j_connection.execute_write(query, {
        "patient_id": patient_id,
        "body_part": body_part
    })
```

### Redis Development

#### Key Patterns
```python
# Chat history: stm:{user_id}:{doctor_id}:{conversation_id}
# User sessions: session:{user_id}
# Cache: cache:{key}

# Storing chat messages
redis_client.store_chat_message(
    user_id="patient_123",
    conversation_id="session_456",
    message_data={"role": "user", "content": "Hello"}
)
```

## 🤖 AI Agents Development

### Agent Architecture

#### Base Agent Pattern
```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAgent(ABC):
    def __init__(self, model_name: str = "gpt-4-turbo-preview"):
        self.model_name = model_name
        self.client = self._initialize_client()
    
    @abstractmethod
    async def process_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    def _initialize_client(self):
        # Initialize AI model client
        pass
```

#### Medical Agent Example
```python
class MedicalAgent(BaseAgent):
    async def process_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        # Get patient medical history
        patient_id = context.get("patient_id")
        medical_history = await self._get_medical_context(patient_id)
        
        # Process with AI model
        response = await self._generate_medical_response(query, medical_history)
        
        return {
            "response": response,
            "confidence": 0.9,
            "source": "medical_agent"
        }
```

### Agent Communication
```python
# Orchestrator routing example
class OrchestratorAgent:
    def __init__(self):
        self.medical_agent = MedicalAgent()
        self.chat_agent = ChatAgent()
    
    async def route_query(self, query: str, context: Dict[str, Any]):
        if self._is_medical_query(query):
            return await self.medical_agent.process_query(query, context)
        else:
            return await self.chat_agent.process_query(query, context)
```

## 🔐 Security Development

### Authentication & Authorization

#### JWT Implementation
```python
from src.auth.jwt_handler import create_jwt_token, decode_jwt

# Creating tokens
token = create_jwt_token({"user_id": "123", "email": "user@example.com"})

# Verifying tokens
payload = decode_jwt(token)
user_id = payload["user_id"]
```

#### Protected Endpoints
```python
from fastapi import Depends
from src.auth.dependencies import get_current_user

@router.post("/protected-endpoint")
async def protected_endpoint(
    data: RequestModel,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    # Process request with user context
```

### HIPAA Compliance Development

#### Patient Data Isolation
```python
# Always validate patient ownership
async def get_patient_documents(patient_id: str, requesting_user_id: str):
    # Verify the requesting user owns this patient data
    if not await verify_patient_ownership(patient_id, requesting_user_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Return documents only for this patient
    return await get_documents_for_patient(patient_id)
```

#### Audit Logging
```python
from src.utils.audit import log_patient_access

async def access_patient_data(patient_id: str, user_id: str, action: str):
    # Log the access for HIPAA compliance
    await log_patient_access(
        patient_id=patient_id,
        accessed_by=user_id,
        action=action,
        timestamp=datetime.utcnow(),
        ip_address=request.client.host
    )
```

## 📊 Monitoring & Debugging

### Logging
```python
from src.utils.logging import logger

# Structured logging
logger.info("Processing document", extra={
    "patient_id": patient_id,
    "document_id": document_id,
    "action": "document_processing",
    "duration_ms": processing_time
})

# Error logging with context
logger.error("Database connection failed", extra={
    "database": "mongodb",
    "error": str(exception),
    "retry_count": retry_count
})
```

### Health Checks
```python
# Custom health check
async def check_ai_service_health():
    try:
        response = await ai_client.test_connection()
        return {"status": "healthy", "response_time": response.duration}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

### Performance Monitoring
```python
import time
from functools import wraps

def monitor_performance(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start_time
        
        logger.info(f"Function {func.__name__} took {duration:.2f}s")
        return result
    return wrapper
```

## 🚀 Deployment

### Local Development
```bash
# Start all services
docker-compose up -d

# Run application
uv run uvicorn src.main:app --reload
```

### Production Deployment
```bash
# Build production image
docker build -t meditwin-api .

# Deploy with production compose
docker-compose -f docker-compose.prod.yml up -d

# Check deployment health
curl http://localhost:8000/health
```

### Environment-Specific Configuration
```python
# src/core/config.py
class Settings(BaseSettings):
    environment: str = "development"
    debug: bool = False
    
    @property
    def is_development(self) -> bool:
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
```

## 🔍 Common Development Tasks

### Adding a New API Endpoint
1. Create the endpoint in the appropriate router
2. Add request/response models
3. Implement business logic
4. Add authentication if needed
5. Write unit and integration tests
6. Update API documentation

### Adding a New Database Operation
1. Implement the database operation
2. Ensure HIPAA compliance (patient_id isolation)
3. Add error handling
4. Write unit tests with mocked databases
5. Add integration tests

### Adding a New AI Agent
1. Extend the BaseAgent class
2. Implement the process_query method
3. Add to orchestrator routing
4. Write tests with mocked AI responses
5. Update documentation

### Debugging Common Issues

#### Database Connection Issues
```bash
# Check database connectivity
uv run python tests/test_health_check.py

# Test specific database
uv run python -c "from src.db.mongodb import get_database; import asyncio; print(asyncio.run(get_database()))"
```

#### Authentication Issues
```bash
# Test JWT token creation/validation
uv run python -c "from src.auth.jwt_handler import create_jwt_token, decode_jwt; token = create_jwt_token({'user_id': '123'}); print(decode_jwt(token))"
```

#### Memory System Issues
```bash
# Test memory system
uv run python -c "from src.chat.short_term import get_short_term_memory; stm = get_short_term_memory(); print('Memory system OK')"
```

## 📝 Contributing Guidelines

1. **Branch Naming**: `feature/description`, `bugfix/description`, `hotfix/description`
2. **Commit Messages**: Follow conventional commits format
3. **Code Review**: All changes require peer review
4. **Testing**: Ensure all tests pass and add tests for new features
5. **Documentation**: Update documentation for API changes
6. **HIPAA Compliance**: Ensure all changes maintain patient data isolation

## 🆘 Getting Help

1. Check this developer guide
2. Review the main documentation
3. Run system health checks
4. Check the troubleshooting section
5. Contact the development team

Remember: Always prioritize HIPAA compliance and patient data security in all development activities!
