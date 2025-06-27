# MediTwin Backend API Documentation

## Overview

The MediTwin Backend is a HIPAA-compliant, multi-agent RAG (Retrieval-Augmented Generation) system for personalized medical insights. It provides secure, intelligent medical consultation through specialized AI agents.

## Architecture

### Core Components

1. **Multi-Agent System**: Specialized medical agents (Cardiologist, Neurologist, Orthopedist, General Physician)
2. **Knowledge Sources**: Vector database (Milvus), Knowledge graph (Neo4j), Document storage (MongoDB)
3. **Security Layer**: User isolation, PII/PHI encryption, HIPAA compliance
4. **Streaming Interface**: Real-time chat with Server-Sent Events (SSE)

### Technology Stack

- **Framework**: FastAPI
- **Databases**: MongoDB, Neo4j, Milvus, Redis
- **AI Framework**: CrewAI for agent orchestration
- **Package Manager**: UV
- **Deployment**: Docker & Docker Compose

## API Endpoints

### Chat Endpoints

#### POST `/chat/stream`
Stream real-time chat responses from medical agents.

**Request Body:**
```json
{
  "user_id": "string",
  "message": "string",
  "conversation_id": "string (optional)",
  "agent_type": "string (optional)"
}
```

**Response:** Server-Sent Events stream
```
data: {"type": "agent", "agent": "orchestrator", "content": "Processing your request..."}
data: {"type": "agent", "agent": "cardiologist", "content": "Based on your symptoms..."}
data: {"type": "final", "response": {"summary": "...", "confidence": 8, "sources": [...]}}
```

#### POST `/chat/message`
Send a single chat message (non-streaming).

**Request/Response:** Same as streaming but returns complete response immediately.

#### GET `/chat/history`
Retrieve chat conversation history.

**Query Parameters:**
- `user_id`: User identifier (required)
- `conversation_id`: Specific conversation (optional)
- `limit`: Number of messages to return (default: 50)

### Timeline Endpoints

#### GET `/timeline/`
Retrieve chronological medical events timeline.

**Query Parameters:**
- `user_id`: User identifier (required)
- `start_date`: Start date in ISO format (optional)
- `end_date`: End date in ISO format (optional)
- `event_types`: Comma-separated event types (optional)
- `limit`: Maximum events to return (default: 50)

**Response:**
```json
{
  "events": [
    {
      "event_id": "string",
      "user_id": "string",
      "event_type": "string",
      "title": "string",
      "description": "string",
      "timestamp": "2023-06-01T10:00:00Z",
      "severity": "string",
      "metadata": {}
    }
  ],
  "total_count": 0,
  "date_range": {
    "start": "2023-06-01T10:00:00Z",
    "end": "2023-06-30T10:00:00Z"
  }
}
```

#### POST `/timeline/event`
Create a new timeline event.

**Request Body:**
```json
{
  "user_id": "string",
  "event_type": "string",
  "title": "string",
  "description": "string",
  "timestamp": "string (optional)",
  "severity": "string (optional)",
  "metadata": {}
}
```

#### PUT `/timeline/event/{event_id}`
Update an existing timeline event.

#### DELETE `/timeline/event/{event_id}`
Delete a timeline event.

#### GET `/timeline/summary`
Get statistical summary of timeline events.

**Query Parameters:**
- `user_id`: User identifier (required)
- `days`: Number of days to summarize (default: 30)

#### GET `/timeline/search`
Search and filter timeline events.

**Query Parameters:**
- `user_id`: User identifier (required)
- `event_type`: Filter by event type (optional)
- `severity`: Filter by severity (optional)
- `search_term`: Search in title/description (optional)
- Additional date filters available

### Upload Endpoints

#### POST `/upload/file`
Upload medical documents for processing.

**Request:** Multipart form data with file upload
- `file`: Document file (PDF, images)
- `user_id`: User identifier
- `metadata`: JSON string with additional metadata (optional)

**Response:**
```json
{
  "document_id": "string",
  "status": "processing",
  "message": "File uploaded successfully"
}
```

#### GET `/upload/status/{document_id}`
Check document processing status.

**Response:**
```json
{
  "document_id": "string",
  "status": "completed|processing|failed",
  "progress": 0.75,
  "message": "Processing complete",
  "extracted_entities": {},
  "error": "string (if failed)"
}
```

#### GET `/upload/history`
Get upload history for a user.

**Query Parameters:**
- `user_id`: User identifier (required)
- `limit`: Number of uploads to return (default: 50)

### Expert Opinion Endpoints

#### POST `/expert-opinion/consult`
Get expert medical consultation from specialized agents.

**Request Body:**
```json
{
  "user_id": "string",
  "query": "string",
  "specialist": "cardiologist|neurologist|orthopedist|general_physician (optional)",
  "include_sources": true,
  "context": {}
}
```

**Response:**
```json
{
  "consultation_id": "string",
  "specialist": "string",
  "summary": "string",
  "confidence": 8,
  "sources": ["string"],
  "recommendations": ["string"],
  "follow_up": "string"
}
```

### Anatomy Endpoints

#### GET `/anatomy/body-part/{part_name}`
Get medical information about specific body parts.

#### GET `/anatomy/systems`
List all body systems and organs.

### Events Endpoints

#### GET `/events/medical`
Retrieve medical events from knowledge graph.

#### POST `/events/medical`
Create medical events in knowledge graph.

## Authentication & Security

### User Identification
- All endpoints require `user_id` parameter
- User authentication handled by separate login service
- Backend receives authenticated user ID from frontend

### Data Protection
- **User Isolation**: Each user's data is completely isolated
- **PII Encryption**: Personal data encrypted with AES-256
- **ID Hashing**: User IDs hashed with HMAC-SHA256 before storage
- **HIPAA Compliance**: All logging sanitized, audit trails maintained

### Rate Limiting
- 100 requests per minute per user for chat endpoints
- 1000 requests per minute per user for other endpoints
- Upload size limited to 50MB per file

## Data Models

### Core Models

```python
class TimelineEvent(BaseModel):
    event_id: Optional[str] = None
    user_id: str
    event_type: str = "general"
    title: str
    description: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    severity: str = "medium"  # low|medium|high|critical
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ChatMessage(BaseModel):
    message_id: Optional[str] = None
    user_id: str
    conversation_id: str
    role: str  # user|assistant
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class DocumentMetadata(BaseModel):
    document_id: Optional[str] = None
    user_id: str
    filename: str
    file_path: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)
    processing_status: str = "pending"
    extracted_entities: Optional[Dict[str, Any]] = Field(default_factory=dict)
```

## Agent System

### Agent Types

1. **Orchestrator Agent**: Central coordinator that routes queries to specialists
2. **Cardiologist Agent**: Heart and cardiovascular system specialist
3. **Neurologist Agent**: Brain and nervous system specialist  
4. **Orthopedist Agent**: Musculoskeletal system specialist
5. **General Physician Agent**: Primary care and general medicine
6. **Aggregator Agent**: Combines multiple specialist responses
7. **Ingestion Agent**: Processes and extracts data from documents

### Agent Workflow

1. **Query Reception**: User query received by orchestrator
2. **Routing Decision**: Orchestrator determines relevant specialists
3. **Parallel Consultation**: Specialists analyze query with their tools
4. **Response Aggregation**: Aggregator combines specialist responses
5. **Final Response**: Unified response delivered to user

### Agent Tools

Each agent has access to specialized tools:

- **Web Search**: Latest medical research and guidelines
- **Vector Store**: Embedded medical knowledge base
- **Knowledge Graph**: Patient history and medical relationships
- **Document DB**: Patient records and test results

## Error Handling

### Standard Error Responses

```json
{
  "detail": "Error description",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2023-06-01T10:00:00Z",
  "trace_id": "string"
}
```

### Common Error Codes

- `USER_NOT_FOUND`: User ID not found or invalid
- `DOCUMENT_NOT_FOUND`: Document ID not found
- `PROCESSING_FAILED`: Document processing failed
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `VALIDATION_ERROR`: Request validation failed
- `INTERNAL_ERROR`: Server internal error

## Development & Testing

### Running Tests

```bash
# Install dependencies
uv sync

# Run all tests
uv run pytest

# Run unit tests only
uv run pytest tests/unit/

# Run integration tests
uv run pytest tests/integration/

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

### Local Development

```bash
# Start development server
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Start with Docker Compose (includes all databases)
docker-compose up -d

# View API documentation
open http://localhost:8000/docs
```

### Environment Variables

```bash
# Database URLs
MONGO_URI=mongodb://localhost:27017
NEO4J_URI=bolt://localhost:7687
MILVUS_HOST=localhost
REDIS_HOST=localhost

# Security
SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-encryption-key

# AI Models
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL_CHAT=gpt-4
OPENAI_MODEL_EMBEDDING=text-embedding-ada-002

# AgentOps (optional)
AGENTOPS_API_KEY=your-agentops-key
```

## Deployment

### Docker Deployment

```bash
# Build backend image
docker build -f backend_RAG.dockerfile -t meditwin-backend .

# Start all services
docker-compose up -d

# Check service health
docker-compose ps
curl http://localhost:8000/health
```

### Production Considerations

1. **Scalability**: Use load balancer for multiple backend instances
2. **Database**: Use managed database services for production
3. **Monitoring**: Implement comprehensive logging and monitoring
4. **Backup**: Regular database backups and disaster recovery
5. **SSL**: HTTPS termination at load balancer level
6. **Secrets**: Use proper secret management (AWS Secrets Manager, etc.)

## Monitoring & Observability

### Health Checks

- `GET /health`: Detailed system health check
- `GET /`: Basic health check
- Database connection status
- Agent system status

### Logging

- Structured JSON logging
- HIPAA-compliant sanitization
- User action tracking
- Error tracking with trace IDs
- Performance metrics

### Metrics

- Request latency and throughput
- Agent response times
- Database query performance
- Error rates by endpoint
- User activity patterns

## Security Best Practices

### Data Handling

1. **Encryption at Rest**: All PHI encrypted in databases
2. **Encryption in Transit**: TLS 1.3 for all communications
3. **Access Control**: Role-based access control (RBAC)
4. **Audit Logging**: Complete audit trail of all data access
5. **Data Retention**: Configurable data retention policies

### HIPAA Compliance

- **Administrative Safeguards**: Access management, training
- **Physical Safeguards**: Secure data centers, access controls
- **Technical Safeguards**: Encryption, access controls, audit controls
- **Business Associate Agreements**: Proper vendor agreements

## Contributing

### Code Style

- Python: Follow PEP 8, use Black formatter
- FastAPI: Follow FastAPI best practices
- Testing: Maintain >80% code coverage
- Documentation: Update API docs for all changes

### Git Workflow

1. Create feature branch from main
2. Implement changes with tests
3. Update documentation
4. Create pull request
5. Code review and approval
6. Merge to main

## Support

For technical support or questions:

- **Issues**: GitHub Issues for bug reports
- **Discussions**: GitHub Discussions for questions
- **Documentation**: This README and inline code docs
- **API Reference**: `/docs` endpoint when running locally
