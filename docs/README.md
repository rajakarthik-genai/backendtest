# MediTwin Documentation

Welcome to the comprehensive documentation for MediTwin - a HIPAA-compliant AI-powered medical assistant system.

## 📚 Documentation Overview

This documentation covers all aspects of the MediTwin system, from setup and development to API usage and security compliance.

### 📖 Available Documents

1. **[API Documentation](API_DOCUMENTATION.md)** - Complete API reference with all endpoints
2. **[API Quick Reference](API_QUICK_REFERENCE.md)** - Quick lookup for API endpoints
3. **[HIPAA Compliance Guide](HIPAA_COMPLIANCE_FIX.md)** - Critical security and privacy implementation details

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- MongoDB
- Neo4j
- Redis
- Milvus
- UV package manager

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd meditwin-agents

# Install dependencies
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run the application
uv run python src/main.py
```

## 🏗️ System Architecture

MediTwin is built with a microservices architecture designed for scalability, security, and HIPAA compliance:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │    │   AI Agents     │
│   (React/Web)   │◄──►│   (FastAPI)     │◄──►│   (Medical AI)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │     Database Layer      │
                    │  ┌─────────────────┐   │
                    │  │    MongoDB      │   │  Patient Data
                    │  │   (Documents)   │   │
                    │  └─────────────────┘   │
                    │  ┌─────────────────┐   │
                    │  │     Neo4j       │   │  Medical Graph
                    │  │  (Relationships)│   │
                    │  └─────────────────┘   │
                    │  ┌─────────────────┐   │
                    │  │     Redis       │   │  Cache/Memory
                    │  │   (Sessions)    │   │
                    │  └─────────────────┘   │
                    │  ┌─────────────────┐   │
                    │  │     Milvus      │   │  Vector Search
                    │  │   (Embeddings)  │   │
                    │  └─────────────────┘   │
                    └─────────────────────────┘
```

### Key Components

#### 🤖 AI Agents
- **Orchestrator Agent**: Routes queries to appropriate specialists
- **Medical Agent**: Provides medical analysis and recommendations
- **Chat Agent**: Handles conversational interactions
- **Ingestion Agent**: Processes medical documents

#### 🗄️ Database Layer
- **MongoDB**: Patient records, documents, user management
- **Neo4j**: Medical knowledge graph, patient relationships
- **Redis**: Session management, short-term memory
- **Milvus**: Vector storage for semantic search

#### 🔐 Security & Compliance
- **HIPAA Compliance**: Patient data isolation and privacy
- **JWT Authentication**: Secure API access
- **Data Encryption**: At rest and in transit
- **Audit Logging**: Complete audit trail

## 🔒 HIPAA Compliance

MediTwin is designed with HIPAA compliance as a core requirement:

### Patient Data Isolation
- Each patient's data is completely isolated
- No cross-patient data sharing
- Composite database constraints ensure privacy
- Audit tools validate data isolation

### Security Measures
- End-to-end encryption
- Secure authentication and authorization
- Comprehensive audit logging
- Privacy-by-design architecture

### Compliance Features
- Patient consent management
- Data access controls
- Breach notification capabilities
- Compliance monitoring and reporting

## 📊 Testing

MediTwin includes comprehensive testing:

### Test Structure
```
tests/
├── test_health_check.py      # System health monitoring
├── test_comprehensive.py     # Full integration tests
├── unit/
│   ├── test_database.py      # Database unit tests
│   ├── test_agents.py        # AI agent tests
│   └── test_auth.py          # Authentication tests
└── integration/
    ├── test_api_integration.py  # API integration tests
    └── test_api_endpoints.py    # Endpoint-specific tests
```

### Running Tests
```bash
# Run all tests
uv run pytest

# Run specific test categories
uv run pytest tests/unit/
uv run pytest tests/integration/
uv run pytest tests/test_health_check.py

# Run with coverage
uv run pytest --cov=src
```

### Health Checks
The system includes comprehensive health checks:
```bash
# Run system health check
uv run python tests/test_health_check.py
```

## 🚀 Development

### Development Setup
```bash
# Install development dependencies
uv sync --dev

# Run in development mode
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Code Quality
```bash
# Format code
uv run black src/ tests/

# Lint code
uv run flake8 src/ tests/

# Type checking
uv run mypy src/
```

### Database Migrations
```bash
# MongoDB migrations
uv run python scripts/migrate_mongo.py

# Neo4j constraints and indexes
uv run python scripts/setup_neo4j.py

# HIPAA compliance fixes
uv run python hipaa_compliance_fix.py
```

## 📡 API Usage

### Authentication
```bash
# Register user
curl -X POST "http://localhost:8000/api/auth/register" \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com", "password": "secure123", "full_name": "User Name"}'

# Login
curl -X POST "http://localhost:8000/api/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=user@example.com&password=secure123"
```

### Document Upload
```bash
# Upload medical document
curl -X POST "http://localhost:8000/api/documents/upload" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -F "file=@medical_report.pdf"
```

### Chat Interaction
```bash
# Send chat message
curl -X POST "http://localhost:8000/api/chat/message" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"message": "What do my lab results mean?", "conversation_id": "session1"}'
```

## 🔧 Configuration

### Environment Variables
```bash
# Database Configuration
MONGODB_URL=mongodb://localhost:27017
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
REDIS_URL=redis://localhost:6379
MILVUS_HOST=localhost
MILVUS_PORT=19530

# Security
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false

# AI Models
OPENAI_API_KEY=your-openai-key
EMBEDDING_MODEL=text-embedding-3-small
CHAT_MODEL=gpt-4-turbo-preview
```

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Scale services
docker-compose up -d --scale api=3
```

## 📈 Monitoring & Logging

### Health Monitoring
- System health checks at `/health`
- Database connection monitoring
- AI agent availability checking
- HIPAA compliance validation

### Logging
- Structured JSON logging
- Patient access audit logs
- Error tracking and alerting
- Performance metrics

### Metrics
- API response times
- Database query performance
- AI agent processing times
- Security event monitoring

## 🆘 Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check database connectivity
uv run python tests/test_health_check.py
```

#### HIPAA Compliance Issues
```bash
# Run HIPAA compliance check and fix
uv run python hipaa_compliance_fix.py
```

#### Memory System Errors
```bash
# Test memory system
uv run python -c "from src.chat.short_term import get_short_term_memory; print('Memory OK')"
```

### Support
- Check the troubleshooting section in API documentation
- Run system health checks
- Review audit logs for security issues
- Contact the development team for critical issues

## 📞 Support & Contributing

### Getting Help
1. Check this documentation
2. Run system health checks
3. Review error logs
4. Contact the development team

### Contributing
1. Fork the repository
2. Create a feature branch
3. Write tests for your changes
4. Ensure HIPAA compliance
5. Submit a pull request

## 📄 License

This project is licensed under [LICENSE] - see the LICENSE file for details.

---

## 🔗 Related Links

- [API Documentation](API_DOCUMENTATION.md)
- [Quick Reference](API_QUICK_REFERENCE.md)
- [HIPAA Compliance](HIPAA_COMPLIANCE_FIX.md)
- [Project Repository](https://github.com/your-org/meditwin-agents)
