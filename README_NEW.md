# Medical Digital Twin API

A comprehensive, production-ready FastAPI application for medical digital twin visualization and AI-powered health analysis.

## Features

- **Document Processing**: Upload and process medical documents with AI-powered extraction
- **Chat Interface**: Streaming chat with medical context and RAG capabilities
- **Expert Opinion**: Multi-agent expert consultation system
- **Health Visualization**: 3D body part visualization with severity mapping
- **Timeline Analysis**: Medical event timeline tracking
- **Report Generation**: Comprehensive medical reports with visualizations
- **Real-time Monitoring**: Health metrics and prometheus monitoring

## Architecture

### Core Components

- **FastAPI Application**: Modern async web framework
- **Database Layer**: MongoDB, Neo4j, Redis integration
- **AI Services**: OpenAI integration for LLM processing
- **Authentication**: JWT-based security
- **Rate Limiting**: Request throttling and monitoring
- **Background Processing**: Async job queue system

### Directory Structure

```
src/
├── core/                   # Core configuration and utilities
│   ├── config.py          # Settings and configuration
│   ├── exceptions.py      # Custom exception classes
│   └── logging.py         # Logging configuration
├── models/                 # Pydantic data models
│   ├── document.py        # Document-related models
│   ├── health.py          # Health status models
│   ├── timeline.py        # Timeline event models
│   ├── chat.py            # Chat request/response models
│   └── report.py          # Report generation models
├── db/                     # Database connections and models
│   ├── mongodb.py         # MongoDB async connection
│   ├── neo4j.py           # Neo4j graph database
│   ├── redis_client.py    # Redis cache and queue
│   └── models.py          # Database models
├── api/                    # API endpoints and routing
│   ├── dependencies.py    # Shared dependencies
│   └── routers/           # API route modules
│       ├── documents.py   # Document upload/management
│       ├── chat.py        # Chat with streaming
│       ├── expert_opinion.py # Multi-agent expert system
│       ├── health.py      # Health status endpoints
│       ├── timeline.py    # Timeline analysis
│       ├── reports.py     # Report generation
│       └── visualization.py # 3D visualization data
└── main_new.py            # Application entry point
```

## Quick Start

### Prerequisites

- Python 3.9+
- MongoDB
- Neo4j
- Redis
- OpenAI API Key

### Installation

1. **Clone and setup environment**:
```bash
cd /home/user/agents/meditwin-agents
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements_new.txt
```

2. **Configure environment variables**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables:
```env
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key
NEO4J_PASSWORD=your-neo4j-password
MONGO_URI=mongodb://root:example@localhost:27017/medical_twin?authSource=admin
REDIS_URL=redis://localhost:6379/0
NEO4J_URI=bolt://localhost:7687
```

3. **Start the application**:
```bash
python src/main_new.py
```

The API will be available at `http://localhost:8000`

### API Documentation

- **Interactive Docs**: `http://localhost:8000/api/docs`
- **ReDoc**: `http://localhost:8000/api/redoc`
- **Health Check**: `http://localhost:8000/health`
- **Metrics**: `http://localhost:8000/metrics`

## API Endpoints

### Document Management
- `POST /api/v1/documents/upload` - Upload medical documents
- `GET /api/v1/documents/status/{patient_id}` - Get document status
- `GET /api/v1/documents/document/{document_id}` - Get document details
- `POST /api/v1/documents/reprocess/{document_id}` - Reprocess document
- `DELETE /api/v1/documents/delete/{document_id}` - Delete document

### Chat Interface
- `POST /api/v1/chat/stream` - Streaming chat with medical context
- `POST /api/v1/chat/message` - Non-streaming chat
- `GET /api/v1/chat/history/{patient_id}` - Get chat history

### Expert Opinion
- `POST /api/v1/expert-opinion/stream` - Streaming expert consultation
- `POST /api/v1/expert-opinion/quick` - Quick expert opinion

### Health Status
- `GET /api/v1/health/body-parts/{patient_id}` - Get body parts health
- `GET /api/v1/health/summary/{patient_id}` - Get health summary
- `GET /api/v1/health/body-part/{patient_id}/{body_part}` - Body part details

### Timeline Analysis
- `POST /api/v1/timeline/events` - Get timeline events
- `GET /api/v1/timeline/patient/{patient_id}` - Get patient timeline
- `GET /api/v1/timeline/summary/{patient_id}` - Timeline summary

### Report Generation
- `POST /api/v1/reports/generate` - Generate medical reports
- `GET /api/v1/reports/status/{report_id}` - Report status
- `GET /api/v1/reports/download/{report_id}` - Download report
- `GET /api/v1/reports/list/{patient_id}` - List patient reports

### 3D Visualization
- `GET /api/v1/visualization/3d-model/{patient_id}` - 3D visualization data
- `GET /api/v1/visualization/body-part-map/{patient_id}` - Body part mapping
- `GET /api/v1/visualization/severity-heatmap/{patient_id}` - Severity heatmap
- `GET /api/v1/visualization/trends/{patient_id}` - Health trends

## Key Features

### 1. Document Processing
- **Multi-format Support**: PDF, DOCX, images, DICOM
- **AI Extraction**: LLM-powered medical information extraction
- **Body Part Mapping**: Automatic mapping to anatomical structures
- **Timeline Generation**: Temporal event extraction

### 2. Chat System
- **Streaming Responses**: Real-time chat with SSE
- **Medical Context**: RAG with patient history
- **Memory Management**: Conversation history tracking
- **Smart Context**: Automatic context relevance detection

### 3. Expert Opinion System
- **Dynamic Expert Selection**: AI-powered specialist selection
- **Multi-agent Collaboration**: Parallel expert consultation
- **Consensus Building**: Synthesized recommendations
- **Streaming Analysis**: Real-time expert assessment

### 4. Health Visualization
- **3D Body Model**: Interactive digital twin
- **Severity Mapping**: Color-coded health status
- **Trend Analysis**: Temporal health progression
- **Heatmap Visualization**: Severity over time

### 5. Security & Performance
- **JWT Authentication**: Secure user authentication
- **Rate Limiting**: Request throttling
- **Error Handling**: Comprehensive exception management
- **Monitoring**: Prometheus metrics integration

## Configuration

### Body Parts Configuration
The system supports 40+ body parts organized by category:
- Head and Neck (brain, eyes, ears, nose, throat, neck, face, skull)
- Torso Upper (shoulders, chest, heart, lungs, thyroid)
- Torso Mid (liver, stomach, pancreas, spleen, gallbladder)
- Torso Lower (kidneys, bladder, intestines, appendix)
- Extremities (arms, legs, hands, feet)
- Systems (blood, immune, nervous, lymphatic, skin)

### Severity Levels
- **Normal** (0-2): Green
- **Mild** (2-4): Yellow
- **Moderate** (4-6): Orange
- **Severe** (6-8): Red
- **Critical** (8-10): Dark Red

### Expert Specialties
- Cardiologist, Neurologist, Pulmonologist
- Gastroenterologist, Orthopedist, Endocrinologist
- Nephrologist, Dermatologist, Hematologist
- Internal Medicine (General)

## Development

### Code Quality
```bash
# Format code
black src/
isort src/

# Lint code
flake8 src/

# Run tests
pytest
```

### Database Setup

**MongoDB Collections**:
- `documents` - Document metadata and status
- `chat_history` - Conversation history
- `reports` - Generated reports
- `expert_opinions` - Expert consultation records

**Neo4j Graph Schema**:
- `Patient` nodes with relationships to:
- `Document`, `BodyPart`, `Condition`, `Treatment`, `Event` nodes

**Redis Usage**:
- Job queue for background processing
- Caching for frequently accessed data
- Rate limiting counters

## Deployment

### Docker Deployment
```bash
# Build and run with docker-compose
docker-compose up -d
```

### Environment Variables
See `.env.example` for complete configuration options.

### Health Monitoring
- Health check endpoint: `/health`
- Prometheus metrics: `/metrics`
- Application logs in `logs/` directory

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please contact the development team.
