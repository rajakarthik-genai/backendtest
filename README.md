# MediTwin Agents

A multi-agent medical analysis system powered by AI specialists for comprehensive healthcare insights.

## Overview

MediTwin Agents is an intelligent backend system that orchestrates multiple AI specialists to provide comprehensive medical analysis. The system includes specialized agents for different medical domains and provides secure, authenticated access to medical knowledge and analysis capabilities.

## Features

- **Multi-Agent Architecture**: Specialized AI agents for different medical domains
- **Secure Authentication**: JWT-based authentication with role-based access
- **Medical Knowledge Base**: Advanced RAG system for medical information retrieval
- **Timeline Analysis**: Automated medical history timeline generation
- **Document Processing**: Upload and analysis of medical documents
- **Analytics Dashboard**: Comprehensive analytics and insights

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
