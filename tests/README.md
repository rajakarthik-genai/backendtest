# MediTwin Agents - Test Suite

## 🧪 Test Structure

```
tests/
├── test_all_endpoints.py      # Comprehensive API endpoint tests
├── unit/                      # Unit tests
│   ├── test_models.py        # Data model validation tests
│   └── test_auth.py          # Authentication tests
├── integration/               # Integration tests
│   └── test_api_integration.py # API integration tests
├── requirements.txt           # Test dependencies
└── README.md                 # This file
```

## 🚀 Running Tests

### Install Test Dependencies
```bash
pip install -r tests/requirements.txt
```

### Run All Tests
```bash
# Run with pytest
pytest tests/

# Run specific test file
pytest tests/test_all_endpoints.py

# Run with coverage
pytest tests/ --cov=src

# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest tests/integration/
```

### Run Direct Test Script
```bash
# Run comprehensive endpoint test
python tests/test_all_endpoints.py

# Make executable and run
chmod +x tests/test_all_endpoints.py
./tests/test_all_endpoints.py
```

## 📊 Test Categories

### Comprehensive Endpoint Tests (`test_all_endpoints.py`)
Tests all API endpoints including:
- ✅ **Chat Endpoints**: Message, history, sessions, streaming
- ✅ **Medical Analysis**: Symptom analysis, diagnostics, treatment recommendations
- ✅ **Upload Endpoints**: Document upload, status tracking, file management
- ✅ **Knowledge Base**: Medical search, drug interactions, information lookup
- ✅ **Analytics**: Health trends, dashboard, risk assessment, health score
- ✅ **Timeline**: Events, history, summary
- ✅ **System Info**: Status, metrics, database health
- ✅ **Authentication**: Token validation, patient ID isolation

### Unit Tests (`tests/unit/`)
- **Data Models** (`test_models.py`): Validation of request/response models
- **Authentication** (`test_auth.py`): JWT token handling, patient ID isolation
- **Individual Components**: No external dependencies
- **HIPAA Compliance**: Data isolation validation

### Integration Tests (`tests/integration/`)
- **API Integration** (`test_api_integration.py`): Full system integration
- **Database Connections**: MongoDB, Redis, Neo4j, Milvus
- **Service Communications**: Agent orchestration, file processing
- **End-to-End Workflows**: Complete user journey testing

## 🔧 Test Configuration

- **Base URL**: `http://localhost:8000/api/v1`
- **Timeout**: 30 seconds per request
- **Authentication**: JWT Bearer token (configurable)
- **Expected Status Codes**: 
  - `200`: Successful response (with valid authentication)
  - `401`: Unauthorized (expected without valid JWT token)
  - `422`: Validation error (for malformed requests)

## 📋 Test Results

Tests are designed to validate:
1. **Endpoint Accessibility**: All endpoints respond appropriately
2. **Authentication Security**: Proper JWT token validation
3. **Data Validation**: Request/response format validation
4. **Error Handling**: Appropriate error responses
5. **HIPAA Compliance**: Patient data isolation

### Expected Outcomes
- ✅ **200 OK**: Endpoint works with valid authentication
- ✅ **401 Unauthorized**: Proper security (expected without valid token)
- ❌ **404 Not Found**: Endpoint doesn't exist (needs investigation)
- ❌ **500 Internal Error**: Server error (needs fixing)

## 🎯 Running Specific Tests

### Test Individual Endpoints
```bash
# Test only chat endpoints
pytest tests/test_all_endpoints.py::TestMediTwinAPI::test_chat_message

# Test only medical analysis
pytest tests/test_all_endpoints.py::TestMediTwinAPI::test_symptom_analysis

# Test only authentication
pytest tests/unit/test_auth.py
```

### Test with Real Authentication
```bash
# Set environment variable for real token
export TEST_JWT_TOKEN="your-real-jwt-token"
python tests/test_all_endpoints.py
```

## 🔍 Debugging Failed Tests

### Common Issues
1. **Service Not Running**: Start with `docker compose up -d`
2. **Authentication Errors**: Use valid JWT token
3. **Timeout Errors**: Check service health
4. **Connection Refused**: Verify port 8000 is accessible

### Debug Commands
```bash
# Check service status
docker compose ps

# Check backend logs
docker compose logs backend

# Test basic connectivity
curl http://localhost:8000/docs

# Check specific endpoint
curl -H "Authorization: Bearer test-token" \
     http://localhost:8000/api/v1/system_info/system/status
```

## 📊 Test Coverage

The test suite covers:
- **25+ API Endpoints**: All major functionality
- **Authentication**: JWT token validation
- **Data Models**: Request/response validation
- **Error Handling**: Proper error responses
- **Integration**: Database and service connectivity
- **HIPAA Compliance**: Patient data isolation

## 🎉 Success Criteria

A successful test run indicates:
- ✅ All endpoints are accessible
- ✅ Authentication is properly implemented
- ✅ Data validation is working
- ✅ Services are healthy and responding
- ✅ HIPAA compliance is maintained
