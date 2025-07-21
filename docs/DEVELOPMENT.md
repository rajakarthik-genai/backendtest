# MediTwin Backend Development Guide

## Quick Start

### Prerequisites

- **UV Package Manager**: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Docker & Docker Compose**: For running databases
- **Python 3.10+**: Required for the application

### Setup Development Environment

1. **Clone and Install Dependencies**
   ```bash
   git clone <repository-url>
   cd meditwin-agents
   
   # Install dependencies with UV
   uv sync
   
   # Activate virtual environment
   source .venv/bin/activate  # Linux/Mac
   # or
   .venv\Scripts\activate     # Windows
   ```

2. **Start Database Services**
   ```bash
   # Start all required databases
   docker-compose up -d mongodb neo4j milvus redis
   
   # Verify services are running
   docker-compose ps
   ```

3. **Configure Environment**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit .env with your settings
   nano .env
   ```

4. **Run Development Server**
   ```bash
   # Start with hot reload
   uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   
   # Or use the provided task
   uv run task dev
   ```

5. **Access Services**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health
   - MongoDB Express: http://localhost:8081 (if enabled)
   - Neo4j Browser: http://localhost:7474

## Development Workflow

### Code Structure

```
src/
├── main.py                 # FastAPI application entry point
├── config/
│   └── settings.py        # Configuration management
├── api/
│   └── endpoints/         # API route handlers
├── agents/                # AI agent implementations
├── db/                    # Database clients and models
├── utils/                 # Utilities (logging, schemas)
├── prompts/              # Agent prompts and templates
└── tools/                # Agent tools and integrations

tests/
├── unit/                 # Unit tests
├── integration/          # Integration tests
└── conftest.py          # Test configuration
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test categories
uv run pytest tests/unit/          # Unit tests only
uv run pytest tests/integration/   # Integration tests only

# Run with coverage report
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_timeline.py

# Run tests matching pattern
uv run pytest -k "test_timeline"

# Run tests with verbose output
uv run pytest -v

# Run tests in parallel (if pytest-xdist installed)
uv run pytest -n auto
```

### Code Quality

```bash
# Format code with Black
uv run black src/ tests/

# Check code style
uv run flake8 src/ tests/

# Type checking with mypy
uv run mypy src/

# Sort imports
uv run isort src/ tests/

# Run all quality checks
uv run task lint
```

### Database Management

```bash
# Reset databases (development only)
docker-compose down -v
docker-compose up -d

# View database logs
docker-compose logs mongodb
docker-compose logs neo4j
docker-compose logs milvus
docker-compose logs redis

# Access database shells
docker-compose exec mongodb mongosh
docker-compose exec neo4j cypher-shell
docker-compose exec redis redis-cli
```

## Testing Strategy

### Unit Tests
- Test individual functions and classes
- Mock external dependencies
- Fast execution (< 1 second per test)
- Location: `tests/unit/`

### Integration Tests
- Test API endpoints end-to-end
- Use test databases
- Test agent workflows
- Location: `tests/integration/`

### Test Database Setup
```bash
# Start test databases
docker-compose -f docker-compose.test.yml up -d

# Run integration tests
TESTING=true uv run pytest tests/integration/

# Clean up test databases
docker-compose -f docker-compose.test.yml down -v
```

## Agent Development

### Creating New Agents

1. **Create Agent Class**
   ```python
   # src/agents/new_specialist_agent.py
   from src.agents.base_specialist import BaseSpecialist, SpecialtyType
   from src.prompts import get_agent_prompt
   
   class NewSpecialistAgent(BaseSpecialist):
       def __init__(self):
           prompt = get_agent_prompt("new_specialist")
           super().__init__(SpecialtyType.NEW_SPECIALTY, prompt)
   ```

2. **Create Prompt File**
   ```json
   // src/prompts/new_specialist_prompt.json
   {
     "agent": "New Specialist Agent",
     "role": "Specialist in new medical domain",
     "goals": ["Goal 1", "Goal 2"],
     "tone": "Professional and clear",
     "output_schema": "summary:str, confidence:int, sources:list[str]"
   }
   ```

3. **Add Tests**
   ```python
   # tests/unit/test_new_specialist.py
   def test_new_specialist_agent():
       agent = NewSpecialistAgent()
       assert agent.specialty == SpecialtyType.NEW_SPECIALTY
   ```

### Agent Tool Development

```python
# src/tools/new_tool.py
class NewTool:
    async def process(self, query: str, user_id: str) -> dict:
        # Implement tool logic
        return {"result": "processed"}

# Register tool with agents
from src.agents.base_specialist import register_tool
register_tool("new_tool", NewTool())
```

## API Endpoint Development

### Creating New Endpoints

1. **Create Router**
   ```python
   # src/api/endpoints/new_endpoint.py
   from fastapi import APIRouter, HTTPException
   from src.utils.schema import NewRequest, NewResponse
   
   router = APIRouter(prefix="/new", tags=["new"])
   
   @router.post("/", response_model=NewResponse)
   async def new_endpoint(request: NewRequest):
       # Implementation
       return NewResponse(...)
   ```

2. **Add Schema Models**
   ```python
   # src/utils/schema.py
   class NewRequest(BaseModel):
       user_id: str
       data: str
   
   class NewResponse(BaseModel):
       result: str
       status: str
   ```

3. **Register Router**
   ```python
   # src/api/__init__.py
   from src.api.endpoints import new_endpoint
   
   _ROUTERS = [
       # ... existing routers
       new_endpoint,
   ]
   ```

4. **Add Tests**
   ```python
   # tests/integration/test_new_endpoint.py
   @pytest.mark.asyncio
   async def test_new_endpoint():
       async with AsyncClient(app=app, base_url="http://test") as client:
           response = await client.post("/new/", json={"user_id": "test", "data": "test"})
           assert response.status_code == 200
   ```

## Database Development

### Adding Database Operations

1. **MongoDB Operations**
   ```python
   # src/db/mongo_db.py
   async def new_operation(self, user_id: str, data: dict) -> str:
       hashed_user_id = self._hash_user_id(user_id)
       # Implement operation
       return result_id
   ```

2. **Neo4j Operations**
   ```python
   # src/db/neo4j_db.py
   def new_graph_operation(self, user_id: str, data: dict) -> bool:
       hashed_user_id = self._hash_user_id(user_id)
       with self.driver.session() as session:
           # Implement Cypher query
           return success
   ```

3. **Milvus Operations**
   ```python
   # src/db/milvus_db.py
   async def new_vector_operation(self, user_id: str, embeddings: list) -> list:
       collection = self._get_user_collection(user_id)
       # Implement vector operation
       return results
   ```

## Debugging

### Development Debugging

```bash
# Start with debugger support
uv run python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m uvicorn src.main:app --reload

# View logs in real-time
tail -f logs/app.log

# Check database connections
uv run python -c "
from src.db.mongo_db import get_mongo
import asyncio
async def test():
    mongo = await get_mongo()
    print('MongoDB:', mongo._initialized)
asyncio.run(test())
"
```

### Production Debugging

```bash
# View container logs
docker-compose logs -f backend

# Access container shell
docker-compose exec backend bash

# Check health endpoints
curl http://localhost:8000/health
curl http://localhost:8000/
```

## Performance Optimization

### Database Performance

1. **MongoDB Indexing**
   ```python
   # Ensure proper indexes exist
   await db.collection.create_index([("user_id", 1), ("timestamp", -1)])
   ```

2. **Neo4j Query Optimization**
   ```cypher
   // Use proper indexes and constraints
   CREATE INDEX ON :Patient(patient_id)
   CREATE CONSTRAINT ON (e:Event) ASSERT e.event_id IS UNIQUE
   ```

3. **Milvus Collection Tuning**
   ```python
   # Optimize collection parameters
   collection_params = {
       "metric_type": "COSINE",
       "index_type": "IVF_FLAT",
       "params": {"nlist": 1024}
   }
   ```

### Application Performance

1. **Async/Await Usage**
   - Use async for all I/O operations
   - Avoid blocking calls in request handlers
   - Use connection pooling for databases

2. **Caching Strategy**
   ```python
   # Redis caching for frequent queries
   @cache_result(ttl=300)  # 5 minutes
   async def expensive_operation(user_id: str):
       # Implementation
       pass
   ```

3. **Response Optimization**
   - Use streaming for large responses
   - Implement pagination for list endpoints
   - Compress responses when appropriate

## Security Development

### Testing Security

```bash
# Test with security scanners
uv run bandit -r src/

# Check dependencies for vulnerabilities
uv audit

# Test authentication
curl -H "Authorization: Bearer invalid" http://localhost:8000/chat/history
```

### Security Guidelines

1. **Input Validation**
   - Validate all user inputs with Pydantic
   - Sanitize strings before database storage
   - Use parameterized queries

2. **Data Protection**
   - Encrypt PII before storage
   - Hash user IDs consistently
   - Log security events

3. **Error Handling**
   - Don't expose internal errors to users
   - Log security-relevant errors
   - Use generic error messages

## Deployment

### Local Production Testing

```bash
# Build production image
docker build -f backend_RAG.dockerfile -t meditwin-backend:local .

# Test production setup
docker-compose -f docker-compose.prod.yml up -d

# Run smoke tests
uv run pytest tests/integration/test_deployment.py
```

### Environment-Specific Configuration

```bash
# Development
export ENVIRONMENT=development
export LOG_LEVEL=DEBUG

# Staging
export ENVIRONMENT=staging
export LOG_LEVEL=INFO

# Production
export ENVIRONMENT=production
export LOG_LEVEL=WARNING
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Check database status
   docker-compose ps
   
   # Restart databases
   docker-compose restart mongodb neo4j milvus redis
   ```

2. **Import Errors**
   ```bash
   # Verify virtual environment
   which python
   
   # Reinstall dependencies
   uv sync --force
   ```

3. **Test Failures**
   ```bash
   # Run tests with verbose output
   uv run pytest -v --tb=long
   
   # Check test database state
   docker-compose -f docker-compose.test.yml logs
   ```

### Getting Help

1. **Check Logs**
   - Application logs: `logs/app.log`
   - Database logs: `docker-compose logs <service>`
   - Test output: `pytest -v`

2. **Debugging Tools**
   - FastAPI docs: `/docs` endpoint
   - Health check: `/health` endpoint
   - Database admin interfaces

3. **Development Resources**
   - FastAPI documentation
   - CrewAI documentation
   - Database-specific documentation
