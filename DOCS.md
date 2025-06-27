# MediTwin Backend - Production-Ready Medical AI System

[![Tests](https://github.com/your-org/meditwin-backend/workflows/Tests/badge.svg)](https://github.com/your-org/meditwin-backend/actions)
[![Coverage](https://codecov.io/gh/your-org/meditwin-backend/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/meditwin-backend)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![HIPAA Compliant](https://img.shields.io/badge/HIPAA-Compliant-green.svg)](#security-and-compliance)

A production-ready, HIPAA-compliant multi-agent RAG (Retrieval-Augmented Generation) backend for personalized medical insights and digital health applications.

## 🏗️ Architecture Overview

The MediTwin backend is built using a microservices architecture with the following key components:

### Core Technologies
- **FastAPI**: High-performance async web framework
- **MongoDB**: Primary data store for PHI/PII with encryption
- **Neo4j**: Knowledge graph for medical relationships
- **Milvus**: Vector database for semantic search
- **Redis**: Session management and caching
- **CrewAI**: Multi-agent orchestration framework

### Security & Compliance
- **HIPAA Compliant**: Encrypted data storage, audit logging, user isolation
- **Data Segregation**: Per-user data isolation with hashed identifiers
- **Secure Encryption**: AES-256 for PII, HMAC-SHA256 for IDs
- **Audit Logging**: Comprehensive HIPAA-compliant activity tracking

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Docker & Docker Compose
- uv package manager

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/your-org/meditwin-backend.git
cd meditwin-backend
```

2. **Install dependencies with uv**
```bash
uv sync
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Start services with Docker Compose**
```bash
docker-compose up -d
```

5. **Run the application**
```bash
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

## 📁 Project Structure

```
src/
├── main.py                 # FastAPI application entry point
├── config/
│   └── settings.py         # Pydantic settings management
├── api/
│   └── endpoints/          # API route handlers
│       ├── chat.py         # Chat and conversation endpoints
│       ├── timeline.py     # Medical timeline management
│       ├── upload.py       # Document upload and processing
│       ├── expert_opinion.py
│       ├── anatomy.py
│       └── events.py
├── agents/                 # Multi-agent system
│   ├── orchestrator_agent.py      # Central coordination
│   ├── cardiologist_agent.py      # Heart specialist
│   ├── neurologist_agent.py       # Brain specialist
│   ├── orthopedist_agent.py       # Bone/joint specialist
│   ├── general_physician_agent.py # Primary care
│   ├── aggregator_agent.py        # Response synthesis
│   └── ingestion_agent.py         # Document processing
├── db/                     # Database managers
│   ├── mongo_db.py         # MongoDB operations
│   ├── neo4j_db.py         # Neo4j knowledge graph
│   ├── milvus_db.py        # Vector database
│   └── redis_db.py         # Session and cache
├── prompts/                # Agent prompt management
│   ├── __init__.py         # Prompt loading utilities
│   ├── cardiologist_prompt.json
│   ├── neurologist_prompt.json
│   ├── orchestrator_prompt.json
│   ├── aggregator_prompt.json
│   ├── entities.json       # NLP entity extraction
│   └── ocr.json           # OCR processing
├── tools/                  # Agent tools and utilities
│   ├── pdf_extractor.py    # Document processing
│   ├── knowledge_graph.py  # Graph operations
│   ├── vector_store.py     # Embedding management
│   ├── document_db.py      # Document operations
│   └── web_search.py       # External search
├── utils/
│   ├── schema.py           # Pydantic models
│   └── logging.py          # HIPAA-compliant logging
├── chat/                   # Conversation management
│   ├── history.py          # Chat history
│   ├── short_term.py       # Session memory
│   └── long_term.py        # Persistent memory
└── memory/
    └── memory_manager.py   # Memory coordination
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following configuration:

```bash
# Application
ENVIRONMENT=production
SECRET_KEY=your-secret-key-here
DEBUG=false

# Database URLs
MONGO_URI=mongodb://user:pass@localhost:27017/meditwin
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-neo4j-password
REDIS_HOST=localhost
REDIS_PORT=6379
MILVUS_HOST=localhost
MILVUS_PORT=19530

# OpenAI API
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL_CHAT=gpt-4
OPENAI_MODEL_EMBEDDING=text-embedding-ada-002

# Security
ENCRYPTION_KEY=your-32-byte-encryption-key
HASH_SECRET=your-hash-secret

# AgentOps (optional)
AGENTOPS_API_KEY=your-agentops-key

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## 🏥 API Endpoints

### Chat & Conversation
- `POST /chat/` - Send message to medical AI
- `POST /chat/stream` - Streaming chat responses (SSE)
- `GET /chat/history` - Retrieve conversation history
- `POST /chat/session` - Create new chat session

### Timeline Management
- `GET /timeline/` - Get patient medical timeline
- `POST /timeline/event` - Create timeline event
- `PUT /timeline/event/{id}` - Update timeline event
- `DELETE /timeline/event/{id}` - Delete timeline event
- `GET /timeline/summary` - Timeline statistics
- `GET /timeline/search` - Search/filter timeline events

### Document Processing
- `POST /upload/document` - Upload medical documents
- `GET /upload/status/{id}` - Check processing status
- `GET /upload/documents` - List user documents

### Expert Opinions
- `POST /expert_opinion/` - Get specialist consultation
- `GET /expert_opinion/history` - Previous consultations

### Anatomy & Events
- `GET /anatomy/` - Query anatomical information
- `POST /events/` - Create medical events
- `GET /events/` - Retrieve medical events

## 🤖 Multi-Agent System

The MediTwin backend uses a sophisticated multi-agent architecture:

### Agent Types

1. **Orchestrator Agent**
   - Central coordinator for all requests
   - Routes queries to appropriate specialists
   - Manages context and session state

2. **Specialist Agents**
   - **Cardiologist**: Heart and cardiovascular conditions
   - **Neurologist**: Brain and nervous system disorders
   - **Orthopedist**: Bone, joint, and musculoskeletal issues
   - **General Physician**: Primary care and general health

3. **Aggregator Agent**
   - Synthesizes responses from multiple specialists
   - Resolves conflicts and provides unified answers
   - Maintains confidence scoring

4. **Ingestion Agent**
   - Processes uploaded documents (PDF, images)
   - Extracts medical entities and relationships
   - Stores data across multiple databases

### Agent Workflow

```mermaid
graph TD
    A[User Query] --> B[Orchestrator Agent]
    B --> C{Determine Specialists}
    C --> D[Cardiologist]
    C --> E[Neurologist]
    C --> F[Orthopedist]
    C --> G[General Physician]
    D --> H[Aggregator Agent]
    E --> H
    F --> H
    G --> H
    H --> I[Unified Response]
    I --> J[User]
```

## 🗄️ Database Architecture

### MongoDB (Primary Data Store)
- **Collections**: `medical_records`, `timeline_events`, `documents`, `user_data`
- **Encryption**: Field-level encryption for PII/PHI
- **Indexing**: Optimized for user isolation and temporal queries

### Neo4j (Knowledge Graph)
- **Nodes**: Patients, Conditions, Medications, Body Parts, Events
- **Relationships**: Medical associations and causal links
- **User Isolation**: Separate subgraphs per user

### Milvus (Vector Database)
- **Collections**: Document embeddings, semantic search
- **Embedding Model**: OpenAI text-embedding-ada-002
- **Search**: Similarity search for relevant medical information

### Redis (Session & Cache)
- **Chat History**: Conversation persistence
- **Session Data**: User session management
- **Caching**: Frequent query results

## 🧪 Testing

The project includes comprehensive test coverage:

```bash
# Run all tests
uv run pytest

# Run unit tests only
uv run pytest tests/unit/

# Run integration tests
uv run pytest tests/integration/

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test markers
uv run pytest -m "unit and not slow"
```

### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing
- **Database Tests**: Data layer validation
- **Agent Tests**: Multi-agent system testing

## 🔒 Security & Compliance

### HIPAA Compliance Features

1. **Data Encryption**
   - AES-256 encryption for PII/PHI at rest
   - TLS 1.3 for data in transit
   - Encrypted database connections

2. **Access Control**
   - User-based data isolation
   - Role-based access control (RBAC)
   - Audit logging for all data access

3. **Data Integrity**
   - Input validation and sanitization
   - SQL injection prevention
   - Cross-site scripting (XSS) protection

4. **Audit & Monitoring**
   - Comprehensive activity logging
   - HIPAA-compliant log retention
   - Real-time security monitoring

### Security Best Practices

```python
# Example: Secure user ID hashing
def _hash_user_id(self, user_id: str) -> str:
    """Hash user ID for database storage."""
    return hmac.new(
        self.hash_secret.encode(),
        user_id.encode(),
        hashlib.sha256
    ).hexdigest()
```

## 🚀 Deployment

### Docker Deployment

The project includes a complete Docker setup:

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Scale services
docker-compose up -d --scale backend=3
```

### Production Considerations

1. **Environment Configuration**
   - Use production-grade database credentials
   - Configure proper SSL certificates
   - Set up monitoring and alerting

2. **Scaling**
   - Horizontal scaling with load balancers
   - Database replica sets for high availability
   - Redis clustering for session management

3. **Monitoring**
   - Application performance monitoring (APM)
   - Database performance monitoring
   - Health check endpoints

## 📊 Monitoring & Observability

### Health Checks
- `GET /` - Basic health status
- `GET /health` - Detailed system health

### Logging
- Structured JSON logging
- HIPAA-compliant log sanitization
- Centralized log aggregation

### Metrics
- API response times
- Database query performance
- Agent processing times
- User activity patterns

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes and add tests
4. Run the test suite: `uv run pytest`
5. Submit a pull request

### Development Setup

```bash
# Install development dependencies
uv sync --dev

# Install pre-commit hooks
uv run pre-commit install

# Run code formatting
uv run black src/
uv run isort src/

# Run type checking
uv run mypy src/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [API Docs](http://localhost:8000/docs)
- **Issues**: [GitHub Issues](https://github.com/your-org/meditwin-backend/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/meditwin-backend/discussions)

## 🔗 Related Projects

- [MediTwin Frontend](https://github.com/your-org/meditwin-frontend) - React-based web interface
- [MediTwin Mobile](https://github.com/your-org/meditwin-mobile) - Mobile application
- [MediTwin Auth](https://github.com/your-org/meditwin-auth) - Authentication service

---

**Note**: This system is designed for educational and research purposes. Always consult with qualified healthcare professionals for medical advice.
