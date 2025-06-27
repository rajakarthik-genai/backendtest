# MediTwin Digital Health Backend

A comprehensive multi-agent RAG (Retrieval-Augmented Generation) backend system for medical digital twins with HIPAA-compliant data handling.

## 🏗️ Architecture

This system consists of two coordinated services:

1. **Login Service** (Port 8081) - Authentication with PostgreSQL
2. **MediTwin Backend** (Port 8000) - Main API with MongoDB, Neo4j, Milvus, Redis

## 🚀 Key Features

- **Multi-Agent RAG**: CrewAI orchestrated specialist agents (GP, Cardiologist, Neurologist, Orthopedist)
- **Real-time Streaming**: Server-Sent Events (SSE) for live chat responses
- **HIPAA Compliance**: Encrypted PII, separate PHI storage, hashed patient IDs
- **Multi-Modal Processing**: PDF → OCR → GPT-4V fallback pipeline
- **Vector Search**: HuggingFace SentenceTransformers with OpenAI Ada fallback
- **Knowledge Graph**: Neo4j for medical relationships and anatomy mapping
- **Secure Authentication**: JWT tokens shared between services

## 🛠️ Technology Stack

### Backend Services
- **FastAPI**: Async web framework
- **CrewAI**: Multi-agent orchestration
- **LangChain**: LLM workflow management

### Databases
- **PostgreSQL**: User authentication and profiles
- **MongoDB**: Encrypted PII and medical records (PHI)
- **Neo4j**: Medical knowledge graph
- **Milvus**: Vector embeddings for semantic search
- **Redis**: Caching and session management

### AI/ML Components
- **OpenAI GPT-4**: Multi-agent reasoning and web search
- **SentenceTransformers**: Local embeddings (all-MiniLM-L6-v2)
- **Tesseract OCR**: Scanned document processing
- **PDFPlumber**: Text extraction from PDFs

## 📁 Project Structure

```
/meditwin-agents/
├── docker-compose.yml              # Orchestrates all services
├── backend_RAG.dockerfile          # Main API container
├── .env                            # Environment variables
├── requirements.txt                # Python dependencies
├── src/                            # Main application code
│   ├── main.py                     # FastAPI entrypoint
│   ├── config/settings.py          # Configuration management
│   ├── api/endpoints/              # REST API routes
│   ├── agents/                     # CrewAI specialist agents
│   ├── chat/                       # Memory management (STM/LTM)
│   ├── db/                         # Database clients
│   ├── tools/                      # PDF, vector, graph tools
│   ├── utils/                      # Encryption, logging utilities
│   └── prompts/                    # Agent prompt templates
└── neo4j/                          # Neo4j configuration
```

## 🔒 Security & HIPAA Compliance

### Data Separation
- **PII Collection**: Encrypted patient identities (name, email, address)
- **PHI Collection**: De-identified medical records linked by hashed patient_id
- **Knowledge Graph**: General medical knowledge (no patient data)

### Encryption
- **Patient IDs**: HMAC-SHA256 hashed identifiers
- **PII Fields**: AES-256 field-level encryption
- **Transport**: TLS for all service communication
- **At Rest**: MongoDB WiredTiger encryption

### Authentication
- **JWT Tokens**: Shared secret between login and main services
- **OAuth2**: Google SSO integration
- **Role-based Access**: Admin vs patient permissions

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API key
- 8GB+ RAM (for all services)

### Environment Setup

1. **Clone and configure**:
```bash
cd /home/user/agents/meditwin-agents
cp .env.example .env
# Edit .env with your API keys and passwords
```

2. **Start all services**:
```bash
docker-compose up -d
```

3. **Verify deployment**:
```bash
# Check service health
curl http://localhost:8000/health
curl http://localhost:8081/health

# View logs
docker-compose logs -f backend
```

### API Endpoints

#### Authentication (Port 8081)
- `POST /auth/signup` - User registration
- `POST /auth/login` - Email/password login
- `GET /auth/google` - Google OAuth login
- `GET /users/me` - Current user profile

#### MediTwin API (Port 8000)
- `POST /upload` - Upload medical documents
- `POST /chat/stream` - Real-time chat with agents (SSE)
- `POST /chat/expert_opinion` - Multi-specialist consultation
- `GET /timeline` - Patient medical timeline
- `GET /anatomy` - Body part analysis from graph
- `POST /events` - Manual event creation

## 🤖 Multi-Agent System

### Specialist Agents
- **General Physician**: Primary care and general health
- **Cardiologist**: Heart and cardiovascular conditions
- **Neurologist**: Brain and nervous system
- **Orthopedist**: Bones, joints, and musculoskeletal

### Agent Workflow
1. **Router**: Keywords-based specialist selection
2. **Orchestrator**: Coordinates multiple agents
3. **Aggregator**: Combines specialist responses
4. **Streaming**: Real-time answer delivery via SSE

## 📊 Data Processing Pipeline

### Document Ingestion
1. **PDF Upload** → Text extraction (PDFPlumber)
2. **OCR Fallback** → Tesseract for scanned documents  
3. **Vision Fallback** → GPT-4V for complex images
4. **Structured Parsing** → Extract conditions, medications, labs
5. **Multi-DB Storage** → MongoDB (records) + Neo4j (relationships) + Milvus (vectors)

### Chat Processing
1. **Authentication** → JWT token verification
2. **Agent Selection** → Route to relevant specialists
3. **Context Retrieval** → Query patient history and knowledge
4. **LLM Reasoning** → Generate specialist responses
5. **Response Streaming** → Real-time delivery to client

## 🔍 Example Usage

### Upload Medical Record
```bash
curl -X POST http://localhost:8000/upload \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@medical_report.pdf"
```

### Stream Chat Response
```javascript
const eventSource = new EventSource('/chat/stream', {
  headers: { 'Authorization': 'Bearer ' + token }
});

eventSource.onmessage = function(event) {
  console.log('AI Response:', event.data);
};
```

### Get Medical Timeline
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  "http://localhost:8000/timeline?user_id=patient123"
```

## 🧪 Testing

### Unit Tests
```bash
docker-compose exec backend pytest tests/
```

### Integration Tests
```bash
# Test complete upload → chat flow
python tests/test_integration.py
```

### Sample Medical Records
The `tests/samples/` directory contains anonymized medical reports for testing the ingestion pipeline.

## 📝 Development

### Adding New Agents
1. Create prompt template in `src/prompts/`
2. Add agent class in `src/agents/`
3. Update router keywords in `expert_router.py`

### Extending Database Schema
1. Update MongoDB collections in `db/mongo_db.py`
2. Add Neo4j node types in `db/neo4j_db.py`
3. Configure new Milvus collections in `db/milvus_db.py`

## 🚨 Production Considerations

### Scaling
- Use multiple FastAPI workers (Gunicorn)
- Implement Redis clustering for session data
- Consider MongoDB sharding for large datasets
- Use Neo4j Enterprise for high availability

### Monitoring
- Set up Prometheus metrics collection
- Configure log aggregation (ELK stack)
- Monitor database performance and connections
- Track AI token usage and costs

### Security
- Regular security audits and penetration testing
- Rotate encryption keys and JWT secrets
- Monitor for unusual access patterns
- Implement rate limiting and DDoS protection

## 📞 Support

For questions or issues:
1. Check the logs: `docker-compose logs -f`
2. Verify environment variables in `.env`
3. Ensure all services are healthy: `docker-compose ps`
4. Review the API documentation at `http://localhost:8000/docs`

## 🔄 Updates & Maintenance

### Database Migrations
```bash
# MongoDB migrations
python scripts/migrate_mongo.py

# Neo4j schema updates  
python scripts/update_neo4j_schema.py
```

### Backup Procedures
```bash
# Automated backup script
./scripts/backup_all_databases.sh
```

---

**Built with ❤️ for secure, intelligent healthcare**
