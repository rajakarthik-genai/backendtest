# MediTwin Agents

A multi-agent medical analysis system powered by AI specialists for comprehensive healthcare insights.

## Overview

MediTwin Agents is an intelligent backend system that orchestrates multiple AI specialists to provide comprehensive medical analysis. The system includes specialized agents for different medical domains and provides secure, authenticated access to medical knowledge and analysis capabilities.

## Features

- **LLM-Driven Dynamic Logic**: All region mapping, severity calculation, and timeline summaries are powered by advanced language models (OpenAI GPT).
- **Centralized Prompt Management**: All prompts are versioned, hallucination-guarded, and easily updatable for best practices.
- **Strict Patient Data Isolation**: Every layer (MongoDB, Neo4j, Milvus, Redis) enforces HIPAA-compliant, per-patient data isolation—no cross-patient linkage is possible.
- **Comprehensive Document Deletion**: Full deletion of documents and all derived data across all databases and disk.
- **Long-Term Memory & User Profile**: Persistent, updatable user profile and medical history for personalized care.
- **Multi-Agent Architecture**: Specialized AI agents for different medical domains.
- **Secure Authentication**: JWT-based authentication with role-based access.
- **Medical Knowledge Base**: Advanced RAG system for medical information retrieval.
- **Timeline Analysis**: Automated medical history timeline generation.
- **Document Processing**: Upload and analysis of medical documents.
- **Analytics Dashboard**: Comprehensive analytics and insights.

## Security & Compliance

- **JWT Authentication**: All endpoints require secure JWT tokens.
- **Patient Data Isolation**: All data is strictly isolated per patient using hashed IDs and unique constraints.
- **Admin Controls**: Admin-only endpoints for privileged operations.
- **HIPAA-Compliant Logging**: All logs are sanitized for PII/PHI and user IDs are masked.

## Prompt Management

- **Versioned Prompts**: All LLM prompts are versioned and stored centrally for traceability.
- **Hallucination Guards**: Prompts include explicit instructions to avoid hallucination and enforce output schemas.
- **Update Workflow**: Prompts can be updated independently of code for rapid iteration and best-practice alignment.

## Quick Start

### Prerequisites

- Python 3.10+
- Docker (optional)
- MongoDB, Redis, Milvus, Neo4j databases

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd meditwin-agents
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run the application:
```bash
python src/main.py
```

## Project Structure

```
├── src/                    # Source code
│   ├── agents/            # AI agent implementations
│   ├── api/               # REST API endpoints
│   ├── auth/              # Authentication system
│   ├── chat/              # Chat and conversation handling
│   ├── config/            # Configuration management
│   ├── db/                # Database connections
│   ├── memory/            # Memory management
│   └── utils/             # Utility functions
├── tests/                 # Test suite
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
├── docs/                  # Documentation
├── deployment/            # Deployment configurations
└── scripts/               # Utility scripts
```

## Documentation

- [API Reference](docs/API_REFERENCE.md) - Complete API documentation
- [API Purpose & Architecture](docs/API_PURPOSE.md) - System architecture and design
- [Development Guide](docs/DEVELOPMENT.md) - Development setup and guidelines
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment instructions
- [Testing Guide](docs/TESTING.md) - Testing strategies and guidelines

## API Endpoints

The system provides RESTful APIs for:

- **Authentication**: User login and JWT token management
- **Chat**: Interactive conversations with AI specialists
- **Medical Analysis**: Comprehensive medical analysis and insights
- **Document Upload**: Medical document processing and analysis
- **Knowledge Base**: Medical information retrieval
- **Timeline**: Medical history timeline generation
- **Analytics**: System analytics and insights
- **Admin**: Administrative functions and system management

See [API Reference](docs/API_REFERENCE.md) for detailed endpoint documentation.

## Testing

Run the test suite:

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Endpoint tests
pytest tests/test_all_endpoints.py
```

### Additional Test Coverage
- **LLM-Driven Endpoints**: Tests for region mapping, severity calculation, timeline summaries, and chat log persistence.
- **Document Deletion**: Tests for full document deletion across MongoDB, Neo4j, Milvus, and disk.
- **User Profile**: Tests for profile persistence and retrieval.
- **Security**: Tests to ensure no cross-user access is possible.
- **Prompt Management**: Tests to ensure all prompts are versioned and hallucination-guarded.

## Note

All endpoints are now LLM-driven, dynamic, and production-ready. The system is designed for extensibility, security, and compliance with modern healthcare data standards.

## Deployment

Multiple deployment options are available:

- **Docker**: Use the provided Docker configuration
- **Systemd**: Use the provided service files
- **Manual**: Follow the deployment guide

See [Deployment Guide](docs/DEPLOYMENT.md) for detailed instructions.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

[Add your license information here]

## Support

For questions and support, please [create an issue](../../issues) or contact the development team.
