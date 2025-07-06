# MediTwin Backend - Production-Ready Medical AI System

[![Tests](https://github.com/your-org/meditwin-backend/workflows/Tests/badge.svg)](https://github.com/your-org/meditwin-backend/actions)
[![Coverage](https://codecov.io/gh/your-org/meditwin-backend/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/meditwin-backend)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![HIPAA Compliant](https://img.shields.io/badge/HIPAA-Compliant-green.svg)](#security-and-compliance)

A production-ready, HIPAA-compliant multi-agent RAG (Retrieval-Augmented Generation) backend for personalized medical insights and digital health applications.

## 🏥 Overview

MediTwin Backend is a sophisticated medical AI system that provides secure, scalable medical consultation services through specialized AI agents. It processes medical documents, maintains patient knowledge graphs, and provides expert medical insights through a multi-agent orchestration system.

### Key Features

- **Multi-Agent Architecture**: Specialized medical agents (Cardiologist, Neurologist, Orthopedist, General Physician)
- **RAG System**: Knowledge retrieval from medical databases and documents
- **HIPAA Compliance**: End-to-end data encryption and user isolation
- **Real-time Streaming**: Server-Sent Events (SSE) for chat interfaces
- **Document Processing**: PDF/OCR/LLM pipeline for medical document ingestion
- **Multi-database**: MongoDB (PHI), Neo4j (Knowledge Graph), Milvus (Vectors), Redis (Cache)

## 🏗️ Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        UI[Frontend UI]
        API[API Gateway]
    end
    
    subgraph "MediTwin Backend"
        FastAPI[FastAPI Server]
        
        subgraph "Agent System"
            Orchestrator[Orchestrator Agent]
            Cardio[Cardiologist Agent]
            Neuro[Neurologist Agent]
            Ortho[Orthopedist Agent]
            GP[General Physician Agent]
            Aggregator[Aggregator Agent]
        end
        
        subgraph "Data Processing"
            Ingestion[Ingestion Agent]
            PDFExtractor[PDF Extractor]
            OCR[OCR Engine]
            LLMProcessor[LLM Processor]
        end
    end
    
    subgraph "Data Layer"
        MongoDB[(MongoDB<br/>Medical Records)]
        Neo4j[(Neo4j<br/>Knowledge Graph)]
        Milvus[(Milvus<br/>Vector Store)]
        Redis[(Redis<br/>Cache & Sessions)]
    end
    
    UI --> API
    API --> FastAPI
    FastAPI --> Orchestrator
    Orchestrator --> Cardio
    Orchestrator --> Neuro
    Orchestrator --> Ortho
    Orchestrator --> GP
    Orchestrator --> Aggregator
    
    FastAPI --> Ingestion
    Ingestion --> PDFExtractor
    Ingestion --> OCR
    Ingestion --> LLMProcessor
    
    FastAPI --> MongoDB
    FastAPI --> Neo4j
    FastAPI --> Milvus
    FastAPI --> Redis
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Docker & Docker Compose
- uv package manager
- OpenAI API key

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

4. **Start database services**
```bash
docker-compose up -d mongo redis neo4j milvus
```

5. **Run the application**
```bash
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

6. **Access the application**
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## 📚 Documentation

- **[Development Guide](DEVELOPMENT.md)** - Setup and development workflow
- **[API Documentation](API.md)** - Complete API reference
- **[Deployment Guide](DEPLOYMENT.md)** - Production deployment instructions
- **[Testing Guide](TESTING.md)** - Testing procedures and reports

## 🔐 Security & HIPAA Compliance

### Data Protection
- **Encryption**: AES-256 encryption for PII data
- **User Isolation**: Complete data segregation per user
- **Audit Logging**: HIPAA-compliant activity tracking
- **JWT Authentication**: Secure token-based authentication

### Compliance Features
- **Data Minimization**: Only collect necessary medical data
- **Access Controls**: Role-based access control (RBAC)
- **Audit Trail**: Complete audit logging for all actions
- **Data Retention**: Configurable data retention policies

## 🤖 Agent System

### Specialist Agents
- **Cardiologist Agent**: Heart and cardiovascular conditions
- **Neurologist Agent**: Brain and nervous system disorders
- **Orthopedist Agent**: Musculoskeletal conditions
- **General Physician Agent**: General medical conditions

### System Agents
- **Orchestrator Agent**: Routes queries to appropriate specialists
- **Aggregator Agent**: Synthesizes multiple specialist responses
- **Ingestion Agent**: Processes medical documents and extracts entities

## 💾 Database Architecture

### MongoDB (Primary Data Store)
- Medical records and patient data
- Document metadata and processing status
- User profiles and preferences
- Encrypted PII storage

### Neo4j (Knowledge Graph)
- Patient medical history relationships
- Body part and condition connections
- Treatment and medication relationships
- Temporal medical events

### Milvus (Vector Database)
- Document embeddings for semantic search
- Medical knowledge embeddings
- Similarity search capabilities
- RAG retrieval system

### Redis (Cache & Sessions)
- Session management
- Chat history caching
- Background task status
- Rate limiting data

## 🛡️ Production Considerations

### Security Hardening
- Enable HTTPS/TLS encryption
- Configure CORS properly
- Implement rate limiting
- Set up security headers
- Use Docker secrets for sensitive data

### Performance Optimization
- Enable database connection pooling
- Implement Redis caching strategy
- Configure load balancing
- Set up monitoring and alerting

### Backup & Recovery
- Regular database backups
- Disaster recovery procedures
- Data retention policies
- HIPAA compliance documentation

## 🔧 Configuration

### Environment Variables
```bash
# Database Configuration
MONGO_URI=mongodb://admin:password@mongo:27017/meditwin?authSource=admin
NEO4J_URI=bolt://neo4j:7687
REDIS_URL=redis://redis:6379/0
MILVUS_URI=http://milvus:19530

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL_CHAT=gpt-4o-mini

# JWT Configuration
JWT_SECRET_KEY=your_super_secret_jwt_key_here
JWT_ALGORITHM=HS256
JWT_REQUIRE_AUTH=true

# Encryption Configuration
AES_ENCRYPTION_KEY=your_32_byte_aes_key_here_exactly_32_bytes
PATIENT_ID_SALT=your_patient_id_salt_for_hmac_hashing
```

## 🧪 Testing

The system includes comprehensive testing:

### Test Coverage
- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing
- **End-to-End Tests**: Complete user journey testing
- **Load Tests**: Performance and scalability testing

### Test Results
- ✅ Document Upload Pipeline: Fully functional
- ✅ Multi-database Storage: Verified across all databases
- ✅ Authentication System: JWT validation working
- ✅ Agent Orchestration: Specialist routing functional
- ⚠️ Chat Endpoints: Timeout issues under investigation

## 📊 Monitoring & Logging

### Logging
- Structured logging with JSON format
- User action audit trails
- Error tracking and alerting
- Performance metrics collection

### Health Monitoring
- Database connection health checks
- Agent system status monitoring
- API endpoint availability
- Resource utilization tracking

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check Docker services are running
   - Verify environment variables
   - Check network connectivity

2. **Authentication Failures**
   - Verify JWT secret key configuration
   - Check token expiration settings
   - Validate token format

3. **Agent Response Timeouts**
   - Check OpenAI API key and quota
   - Verify network connectivity
   - Review agent processing logs

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📞 Support

For support and questions:
- Create an issue in the GitHub repository
- Contact the development team
- Review the documentation and FAQs

---

**Note**: This system handles sensitive medical data. Ensure proper security measures and compliance with healthcare regulations (HIPAA, GDPR) in your deployment.
