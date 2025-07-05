# MediTwin Backend - Testing Guide

## Overview

This project now uses a consolidated testing approach with one comprehensive test suite and organized unit/integration tests.

## Test Structure

```
/
├── comprehensive_test_suite.py    # Main comprehensive test suite (CREATED)
└── tests/
    ├── conftest.py               # pytest configuration and fixtures
    ├── data/                     # Test data files
    ├── unit/                     # Unit tests
    │   ├── test_agents.py
    │   ├── test_database.py
    │   ├── test_prompts.py
    │   └── test_timeline.py
    └── integration/              # Integration tests
        ├── test_api.py
        └── test_api_endpoints.py
```

## Running Tests

### 1. Comprehensive Test Suite

The main test suite (`comprehensive_test_suite.py`) tests all API endpoints with real HTTP requests:

```bash
# Run the comprehensive test suite
python comprehensive_test_suite.py

# This will:
# - Test all API endpoints (health, auth, chat, timeline, events, upload, etc.)
# - Validate database connections
# - Check system functionality
# - Generate detailed reports
```

### 2. Unit Tests

Run individual unit tests using pytest:

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific unit test files
pytest tests/unit/test_agents.py -v
pytest tests/unit/test_database.py -v
pytest tests/unit/test_timeline.py -v
```

### 3. Integration Tests

Run integration tests that test API endpoints with mocked dependencies:

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run specific integration test files
pytest tests/integration/test_api.py -v
pytest tests/integration/test_api_endpoints.py -v
```

### 4. All Tests

Run all pytest-based tests:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html -v
```

## Test Categories

### Comprehensive Test Suite Features

The main test suite (`comprehensive_test_suite.py`) includes:

1. **Health Endpoints**: Root, health check
2. **Authentication**: Signup, login, user info
3. **Timeline**: Get timeline, create events, search, summary
4. **Chat**: Messages, streaming, history, sessions
5. **Expert Opinion**: Consultations, specialties
6. **Anatomy**: Overview, organ timelines
7. **Events**: CRUD operations for medical events
8. **Upload**: Document upload and management
9. **API Documentation**: OpenAPI docs, ReDoc
10. **Database Connections**: MongoDB, Neo4j, Redis validation
11. **Configuration**: OpenAI API key validation

### Test Reports

The comprehensive test suite generates:

- **JSON Report**: Detailed test results (`comprehensive_test_report_TIMESTAMP.json`)
- **Markdown Summary**: Human-readable summary (`test_summary_TIMESTAMP.md`)

## Test Configuration

### Environment Variables

Tests use the same environment variables as the main application (`.env` file):

```env
# Database connections
MONGO_URI=mongodb://admin:secure_password_123@mongo:27017/meditwin?authSource=admin
NEO4J_URI=bolt://neo4j:7687
REDIS_HOST=redis
REDIS_PORT=6379

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# JWT
JWT_SECRET_KEY=your_jwt_secret_key
```

### Test Data

- Test data is generated dynamically with unique IDs
- Sample medical data, chat messages, and timeline events
- Test images created in-memory for upload testing

## Test Prerequisites

### 1. Docker Services Running

Ensure all backend services are running:

```bash
docker compose up -d
```

### 2. Dependencies Installed

```bash
# Install dependencies
uv sync

# Or with pip
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov httpx
```

### 3. Server Running

The comprehensive test suite requires the MediTwin backend server to be running:

```bash
# Server should be accessible at http://localhost:8000
curl http://localhost:8000/health
```

## Expected Test Results

### Success Criteria

- **95%+ Success Rate**: Excellent - all core functionality working
- **80-94% Success Rate**: Good - minor issues to address
- **<80% Success Rate**: Needs attention - significant issues

### Common Test Scenarios

1. **All Passing (100%)**: Perfect setup, all services working
2. **High Success (95-99%)**: Minor endpoint issues, core functionality works
3. **Moderate Success (80-94%)**: Some service issues, authentication working
4. **Low Success (<80%)**: Major configuration or service issues

## Troubleshooting

### Common Issues

1. **Connection Refused**: Backend server not running
   ```bash
   docker compose up -d
   ```

2. **Authentication Failures**: JWT configuration issues
   - Check JWT_SECRET_KEY in .env
   - Verify JWT_REQUIRE_AUTH setting

3. **Database Connection Issues**: Services not accessible
   ```bash
   docker compose ps  # Check service status
   docker compose logs backend  # Check backend logs
   ```

4. **OpenAI API Issues**: Invalid API key
   - Verify OPENAI_API_KEY in .env
   - Check API key permissions

### Debug Mode

Run tests with debug information:

```bash
# Comprehensive test suite with verbose output
python comprehensive_test_suite.py

# Pytest with detailed output
pytest tests/ -v -s --tb=long
```

## Maintenance

### Adding New Tests

1. **Endpoint Tests**: Add to `comprehensive_test_suite.py`
2. **Unit Tests**: Add to appropriate file in `tests/unit/`
3. **Integration Tests**: Add to appropriate file in `tests/integration/`

### Updating Test Data

Modify the `sample_data` dictionary in `MediTwinTestSuite` class for new test scenarios.

### Performance Considerations

- Tests use 30-second timeouts for HTTP requests
- Database connections are tested but not heavily loaded
- Large file uploads use minimal test data

## CI/CD Integration

The test suite is designed for CI/CD integration:

```bash
# Exit code 0 for success, 1 for failure
python comprehensive_test_suite.py
echo $?  # Check exit code
```

For automated testing, the comprehensive test suite provides:
- Machine-readable JSON reports
- Clear success/failure exit codes
- Detailed error logging
- Performance metrics
