# MediTwin Agents API Documentation

## Overview

The MediTwin Agents API provides a comprehensive medical AI platform with the following key features:

- **Multi-Agent Orchestration**: Specialized medical AI agents for different medical domains
- **HIPAA Compliance**: Patient data isolation using secure patient_id tokens
- **Real-time Chat**: Streaming conversations with medical AI assistants
- **Document Processing**: Medical document upload and AI analysis
- **Timeline Management**: Chronological medical event tracking
- **Admin Tools**: Patient data management and system monitoring

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All endpoints require JWT authentication with patient_id embedded in the token for HIPAA compliance and data isolation.

**Header Required:**
```
Authorization: Bearer <JWT_TOKEN>
```

---

## Chat Endpoints

### POST `/chat/message`

Send a chat message and get a response from medical AI agents.

**Request Body:**
```json
{
  "message": "I have been experiencing headaches for the past week",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "response": "I understand you've been experiencing headaches for a week. Can you tell me more about the nature of these headaches?",
  "session_id": "uuid-session-id",
  "metadata": {
    "agent_type": "general_physician",
    "confidence": 0.9
  }
}
```

### POST `/chat/stream`

Stream chat responses using Server-Sent Events (SSE) for real-time interaction.

**Request Body:**
```json
{
  "message": "What could be causing my persistent cough?",
  "session_id": "optional-session-id"
}
```

**Response:** Stream of Server-Sent Events
```
data: {"type": "metadata", "session_id": "uuid-session-id"}

data: {"type": "content", "content": "A persistent cough can have several causes..."}

data: {"type": "content", "content": " Let me help you understand the possibilities."}

data: {"type": "done"}
```

### GET `/chat/history/{session_id}`

Retrieve chat history for a specific session.

**Parameters:**
- `session_id` (path): Chat session identifier
- `limit` (query): Maximum number of messages (default: 50)

**Response:**
```json
{
  "session_id": "uuid-session-id",
  "messages": [
    {
      "role": "user",
      "content": "I have a headache",
      "timestamp": "2024-01-15T10:30:00Z"
    },
    {
      "role": "assistant",
      "content": "Can you describe the headache?",
      "timestamp": "2024-01-15T10:30:05Z"
    }
  ],
  "total_messages": 2
}
```

### DELETE `/chat/history/{session_id}`

Clear chat history for a specific session.

**Response:**
```json
{
  "message": "Chat history cleared successfully"
}
```

### GET `/chat/sessions`

Get all chat sessions for the authenticated user.

**Response:**
```json
{
  "patient_id": "patient-uuid",
  "sessions": [],
  "message": "Session management not fully implemented"
}
```

---

## Upload Endpoints

### POST `/upload/document`

Upload medical documents (PDF, images) for AI processing.

**Request:**
- Content-Type: `multipart/form-data`
- `file`: Document file (max 50MB)
- `description`: Optional description

**Supported File Types:** PDF, PNG, JPG, JPEG, TIFF, BMP

**Response:**
```json
{
  "document_id": "uuid-document-id",
  "status": "queued",
  "message": "Document 'report.pdf' uploaded successfully and queued for processing"
}
```

### GET `/upload/status/{document_id}`

Get processing status of an uploaded document.

**Response:**
```json
{
  "task_id": "uuid-document-id",
  "status": "processing",
  "progress": 0.75,
  "message": "Extracting text and analyzing content",
  "started_at": "2024-01-15T10:30:00Z",
  "completed_at": null,
  "error": null
}
```

### GET `/upload/documents`

List all uploaded documents for the authenticated user.

**Parameters:**
- `limit` (query): Maximum number of documents (default: 20)

**Response:**
```json
{
  "patient_id": "patient-uuid",
  "documents": [
    {
      "document_id": "uuid-1",
      "filename": "blood_test.pdf",
      "upload_date": "2024-01-15T10:30:00Z",
      "status": "completed"
    }
  ],
  "total": 1
}
```

### DELETE `/upload/document/{document_id}`

Delete an uploaded document and its processed data.

**Response:**
```json
{
  "message": "Document deletion not fully implemented",
  "document_id": "uuid-document-id"
}
```

---

## Medical Analysis Endpoints

### POST `/medical_analysis/symptoms/analyze`

Analyze symptoms using specialized medical AI agents.

**Request Body:**
```json
{
  "symptoms": ["headache", "nausea", "dizziness"],
  "duration": "3 days",
  "severity": "moderate",
  "context": "Started after working long hours"
}
```

**Response:**
```json
{
  "analysis": "Based on your symptoms of headache, nausea, and dizziness persisting for 3 days...",
  "symptoms": ["headache", "nausea", "dizziness"],
  "severity": "moderate",
  "recommendations": [
    "Consult with a healthcare professional",
    "Monitor symptoms"
  ],
  "confidence": 0.8,
  "patient_id": "patient-uuid"
}
```

### POST `/medical_analysis/diagnostic/suggestions`

Get diagnostic suggestions based on symptoms and medical history.

**Request Body:**
```json
{
  "symptoms": ["chest pain", "shortness of breath"],
  "medical_history": "History of hypertension"
}
```

**Response:**
```json
{
  "suggestions": [
    {
      "condition": "Further evaluation needed",
      "probability": 0.8,
      "reasoning": "Given your symptoms and medical history..."
    }
  ],
  "symptoms": ["chest pain", "shortness of breath"],
  "disclaimer": "This is AI-generated information. Please consult a healthcare professional.",
  "patient_id": "patient-uuid"
}
```

### POST `/medical_analysis/treatment/recommendations`

Get treatment recommendations for a specific condition.

**Request Body:**
```json
{
  "condition": "migraine",
  "symptoms": ["headache", "light sensitivity"],
  "severity": "severe"
}
```

**Response:**
```json
{
  "recommendations": [
    {
      "treatment": "Professional consultation",
      "priority": "high",
      "details": "For severe migraines, consider consulting a neurologist..."
    }
  ],
  "condition": "migraine",
  "disclaimer": "Always consult with healthcare professionals before starting treatment.",
  "patient_id": "patient-uuid"
}
```

---

## Timeline Endpoints

### GET `/timeline/timeline`

Get chronological timeline of medical events.

**Parameters:**
- `start_date` (query): Start date in ISO format
- `end_date` (query): End date in ISO format
- `event_types` (query): Comma-separated event types
- `limit` (query): Maximum events (default: 50)

**Response:**
```json
{
  "patient_id": "patient-uuid",
  "events": [
    {
      "event_id": "uuid-event-id",
      "timestamp": "2024-01-15T10:30:00Z",
      "event_type": "symptom",
      "description": "Reported headache",
      "metadata": {
        "severity": "moderate",
        "duration": "2 hours"
      }
    }
  ],
  "total_events": 1,
  "timeline_period": "30 days"
}
```

---

## Knowledge Base Endpoints

### GET `/knowledge_base/knowledge/search`

Search medical knowledge base for information.

**Parameters:**
- `query` (query): Search query

**Response:**
```json
{
  "results": [
    {
      "title": "Information about migraine",
      "content": "Migraines are severe headaches that can cause...",
      "source": "AI Medical Assistant",
      "relevance": 0.9
    }
  ],
  "query": "migraine",
  "total_results": 1,
  "patient_id": "patient-uuid"
}
```

### GET `/knowledge_base/medical/information`

Get detailed medical information about a specific topic.

**Parameters:**
- `topic` (query): Medical topic

**Response:**
```json
{
  "topic": "diabetes",
  "information": "Diabetes is a group of metabolic disorders...",
  "last_updated": "2024-01-15T10:30:00Z",
  "sources": ["Medical AI Database"],
  "patient_id": "patient-uuid"
}
```

### POST `/knowledge_base/drugs/interactions`

Check for drug interactions between medications.

**Request Body:**
```json
{
  "medications": ["aspirin", "warfarin", "ibuprofen"]
}
```

**Response:**
```json
{
  "medications": ["aspirin", "warfarin", "ibuprofen"],
  "interactions": [
    {
      "severity": "info",
      "description": "Potential interactions detected between aspirin and warfarin..."
    }
  ],
  "safe_combination": true,
  "disclaimer": "Always consult with a pharmacist or doctor about drug interactions.",
  "patient_id": "patient-uuid"
}
```

---

## Analytics Endpoints

### GET `/analytics/analytics/trends`

Get health analytics trends over time.

**Parameters:**
- `period` (query): Time period (default: "30d")

**Response:**
```json
{
  "period": "30d",
  "trends": [
    {
      "metric": "activity_level",
      "trend": "stable",
      "change": 0.05
    },
    {
      "metric": "sleep_quality",
      "trend": "improving",
      "change": 0.15
    }
  ],
  "data_points": 30,
  "patient_id": "patient-uuid"
}
```

### GET `/analytics/analytics/dashboard`

Get analytics dashboard data overview.

**Response:**
```json
{
  "overview": {
    "health_score": 75,
    "active_goals": 3,
    "completed_goals": 7
  },
  "recent_activity": [],
  "upcoming_reminders": [],
  "patient_id": "patient-uuid"
}
```

### GET `/analytics/health/score`

Get user's calculated health score.

**Response:**
```json
{
  "score": 75,
  "category": "Good",
  "factors": [
    {
      "name": "Exercise",
      "score": 80,
      "weight": 0.3
    },
    {
      "name": "Nutrition",
      "score": 70,
      "weight": 0.3
    }
  ],
  "last_calculated": "2024-01-15T10:30:00Z",
  "patient_id": "patient-uuid"
}
```

### GET `/analytics/health/risk-assessment`

Get health risk assessment analysis.

**Response:**
```json
{
  "risk_level": "Low",
  "factors": [
    {
      "factor": "Age",
      "risk": "low",
      "description": "Age-related risk is minimal"
    }
  ],
  "recommendations": [
    "Maintain regular exercise routine",
    "Continue healthy diet choices"
  ],
  "patient_id": "patient-uuid"
}
```

---

## System Information Endpoints

### GET `/system_info/system/status`

Get overall system status and health.

**Response:**
```json
{
  "status": "operational",
  "version": "1.0.0",
  "uptime": "24h",
  "services": {
    "ai_agents": "healthy",
    "database": "healthy",
    "authentication": "healthy"
  }
}
```

### GET `/system_info/info`

Get API information and available endpoints.

**Response:**
```json
{
  "api_version": "1.0.0",
  "service": "MediTwin Agents API",
  "endpoints": [
    "/api/v1/expert-opinion",
    "/api/v1/timeline",
    "/api/v1/symptoms/analyze",
    "/api/v1/user/profile"
  ],
  "documentation": "/docs"
}
```

### GET `/system_info/metrics`

Get service performance metrics (requires authentication).

**Response:**
```json
{
  "requests_per_minute": 15,
  "average_response_time": "250ms",
  "active_users": 1,
  "system_load": "low",
  "patient_id": "patient-uuid"
}
```

### GET `/system_info/database/status`

Get database connectivity status (requires authentication).

**Response:**
```json
{
  "mongodb": "connected",
  "redis": "connected",
  "neo4j": "connected",
  "milvus": "connected",
  "last_check": "2024-01-15T10:30:00Z",
  "patient_id": "patient-uuid"
}
```

---

## Admin Endpoints

**Warning:** Admin endpoints are for administrative use only and should be properly secured in production.

### GET `/admin/patients/mongo`

List all patient IDs with data in MongoDB.

**Response:**
```json
{
  "patient_ids": ["patient-uuid-1", "patient-uuid-2"],
  "total_count": 2
}
```

### GET `/admin/patients/neo4j`

List all patient IDs with data in Neo4j.

**Response:**
```json
{
  "patient_ids": ["patient-uuid-1"],
  "total_count": 1
}
```

### GET `/admin/patients/milvus`

List all patient IDs with data in Milvus vector database.

**Response:**
```json
{
  "patient_ids": ["patient-uuid-1"],
  "total_count": 1
}
```

### GET `/admin/patients/all`

List all patient IDs across all databases.

**Response:**
```json
{
  "mongo": {
    "patient_ids": ["patient-uuid-1", "patient-uuid-2"],
    "total_count": 2
  },
  "neo4j": {
    "patient_ids": ["patient-uuid-1"],
    "total_count": 1
  },
  "milvus": {
    "patient_ids": ["patient-uuid-1"],
    "total_count": 1
  }
}
```

### GET `/admin/patient/{patient_id}/mongo`

Get patient's data from MongoDB.

**Response:**
```json
{
  "patient_id": "patient-uuid",
  "success": true,
  "data": {
    "medical_records": [],
    "timeline_events": [],
    "pii_data": null,
    "total_records": 0,
    "total_events": 0
  },
  "error": null
}
```

---

## OpenAI Compatible Endpoints

### POST `/openai_compatible/v1/chat/completions`

OpenAI-compatible chat completions endpoint for CrewAI integration.

**Request Body:**
```json
{
  "model": "gpt-3.5-turbo",
  "messages": [
    {
      "role": "user",
      "content": "What are the symptoms of diabetes?"
    }
  ],
  "stream": false,
  "user": "optional-user-id"
}
```

**Response:**
```json
{
  "id": "chatcmpl-uuid",
  "object": "chat.completion",
  "created": 1642284600,
  "model": "gpt-3.5-turbo",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "The common symptoms of diabetes include..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 150,
    "total_tokens": 162
  }
}
```

**Streaming Response:** When `stream: true`
```
data: {"id":"chatcmpl-uuid","object":"chat.completion.chunk","created":1642284600,"model":"gpt-3.5-turbo","choices":[{"index":0,"delta":{"content":"The"},"finish_reason":null}]}

data: {"id":"chatcmpl-uuid","object":"chat.completion.chunk","created":1642284600,"model":"gpt-3.5-turbo","choices":[{"index":0,"delta":{"content":" common"},"finish_reason":null}]}

data: [DONE]
```

---

## Error Responses

All endpoints return standardized error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication required"
}
```

### 403 Forbidden
```json
{
  "detail": "Access denied"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 413 Payload Too Large
```json
{
  "detail": "File too large. Maximum size: 50MB"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

### 503 Service Unavailable
```json
{
  "detail": "Service temporarily unavailable"
}
```

---

## Rate Limiting

- **Default Rate Limit:** 100 requests per minute per user
- **Upload Endpoints:** 10 uploads per minute per user
- **Admin Endpoints:** 20 requests per minute per admin

---

## Data Models

### ChatRequest
```json
{
  "message": "string (required)",
  "session_id": "string (optional)"
}
```

### ChatResponse
```json
{
  "response": "string",
  "session_id": "string",
  "metadata": "object"
}
```

### UploadResponse
```json
{
  "document_id": "string",
  "status": "string",
  "message": "string"
}
```

### ProcessingStatus
```json
{
  "task_id": "string",
  "status": "string",
  "progress": "number",
  "message": "string",
  "started_at": "string (ISO datetime)",
  "completed_at": "string (ISO datetime, nullable)",
  "error": "string (nullable)"
}
```

---

## Security Considerations

1. **JWT Authentication:** All endpoints require valid JWT tokens
2. **Patient Data Isolation:** HIPAA-compliant patient_id ensures data privacy
3. **File Upload Security:** File type validation and size limits
4. **Rate Limiting:** Prevents abuse and ensures service availability
5. **CORS:** Properly configured for cross-origin requests
6. **HTTPS:** All production traffic should use HTTPS encryption

---

## Integration Examples

### Python Client Example
```python
import requests

# Authentication
headers = {
    "Authorization": "Bearer YOUR_JWT_TOKEN",
    "Content-Type": "application/json"
}

# Send a chat message
response = requests.post(
    "http://localhost:8000/api/v1/chat/message",
    headers=headers,
    json={
        "message": "I have a persistent cough for 2 weeks"
    }
)

print(response.json())
```

### JavaScript/React Example
```javascript
const sendMessage = async (message) => {
  const response = await fetch('/api/v1/chat/message', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ message })
  });
  
  return response.json();
};
```

### cURL Example
```bash
curl -X POST "http://localhost:8000/api/v1/chat/message" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the symptoms of flu?"}'
```

---

## Support and Documentation

- **Interactive API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI Specification:** [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

For additional support or questions about the API, please refer to the development team or check the project repository.
