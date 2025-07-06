# MediTwin Backend API Documentation

## Table of Contents

1. [Authentication](#authentication)
2. [Core Endpoints](#core-endpoints)
3. [Document Upload](#document-upload)
4. [Chat System](#chat-system)
5. [Medical Timeline](#medical-timeline)
6. [Expert Consultation](#expert-consultation)
7. [Anatomy & Body Parts](#anatomy--body-parts)
8. [Error Handling](#error-handling)
9. [Rate Limiting](#rate-limiting)
10. [Examples](#examples)

## Authentication

All API endpoints require JWT authentication except for health checks.

### Authentication Flow

```
Client → Login Service → JWT Token → MediTwin Backend
```

### Headers
```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

### JWT Token Structure
```json
{
  "user_id": "unique_user_identifier",
  "email": "user@example.com",
  "username": "username",
  "iat": 1640995200,
  "exp": 1641081600
}
```

## Core Endpoints

### Health Check
```http
GET /health
GET /
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-07-06T13:40:00Z",
  "version": "1.0.0",
  "databases": {
    "mongodb": "connected",
    "neo4j": "connected",
    "redis": "connected",
    "milvus": "connected"
  }
}
```

## Document Upload

### Upload Document
```http
POST /upload/document
Content-Type: multipart/form-data
Authorization: Bearer <jwt_token>
```

**Parameters:**
- `file`: Document file (PDF, PNG, JPG, JPEG, TIFF, BMP)
- `description`: Optional description

**Response:**
```json
{
  "document_id": "uuid-string",
  "status": "queued",
  "message": "Document uploaded successfully and queued for processing"
}
```

### Check Processing Status
```http
GET /upload/status/{document_id}
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "task_id": "uuid-string",
  "status": "completed",
  "progress": 100.0,
  "message": "Processing completed successfully",
  "started_at": "2025-07-06T13:30:00Z",
  "completed_at": "2025-07-06T13:35:00Z"
}
```

### List User Documents
```http
GET /upload/documents?limit=20
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "user_id": "user_123",
  "documents": [
    {
      "document_id": "uuid-string",
      "filename": "medical_report.pdf",
      "upload_date": "2025-07-06T13:30:00Z",
      "processing_status": "completed",
      "entities_count": 5
    }
  ],
  "total": 1
}
```

### Delete Document
```http
DELETE /upload/document/{document_id}
Authorization: Bearer <jwt_token>
```

## Chat System

### Send Message
```http
POST /chat/message
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request:**
```json
{
  "message": "I have chest pain and shortness of breath",
  "session_id": "session_123"
}
```

**Response:**
```json
{
  "response": "Based on your symptoms, I recommend consulting with a cardiologist...",
  "session_id": "session_123",
  "specialists_consulted": ["cardiologist", "general_physician"],
  "confidence": 0.85,
  "timestamp": "2025-07-06T13:40:00Z"
}
```

### Stream Chat Response
```http
POST /chat/stream
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request:**
```json
{
  "message": "What does my recent blood work indicate?",
  "session_id": "session_123"
}
```

**Response (Server-Sent Events):**
```
data: {"type": "metadata", "content": "Analyzing your query..."}

data: {"type": "metadata", "content": "Consulting: Cardiologist, General Physician"}

data: {"type": "partial_insight", "content": "**Cardiologist**: Your cholesterol levels show..."}

data: {"type": "response", "content": "Based on your blood work results..."}

data: {"type": "complete", "session_id": "session_123"}
```

### Get Chat History
```http
GET /chat/history/{session_id}?limit=50
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "session_id": "session_123",
  "messages": [
    {
      "role": "user",
      "content": "I have chest pain",
      "timestamp": "2025-07-06T13:30:00Z"
    },
    {
      "role": "assistant",
      "content": "I understand your concern...",
      "timestamp": "2025-07-06T13:30:30Z",
      "specialists": ["cardiologist"]
    }
  ],
  "total": 2
}
```

## Medical Timeline

### Get Timeline
```http
GET /timeline/?start_date=2025-01-01&end_date=2025-12-31
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "timeline": [
    {
      "event_id": "event_123",
      "title": "Blood Pressure Check",
      "description": "Routine blood pressure monitoring",
      "date": "2025-07-06",
      "event_type": "vital_signs",
      "severity": "normal",
      "body_parts": ["heart"],
      "source": "document_upload"
    }
  ],
  "total_events": 1,
  "date_range": {
    "start": "2025-01-01",
    "end": "2025-12-31"
  }
}
```

### Create Timeline Event
```http
POST /timeline/event
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request:**
```json
{
  "title": "Medication Started",
  "description": "Started taking Lisinopril 10mg daily",
  "date": "2025-07-06",
  "event_type": "medication",
  "severity": "mild",
  "body_parts": ["heart"]
}
```

### Update Timeline Event
```http
PUT /timeline/event/{event_id}
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

### Delete Timeline Event
```http
DELETE /timeline/event/{event_id}
Authorization: Bearer <jwt_token>
```

## Expert Consultation

### Get Expert Opinion
```http
POST /expert-opinion/consult
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request:**
```json
{
  "query": "Should I be concerned about my irregular heartbeat?",
  "specialist": "cardiologist",
  "context": {
    "symptoms": ["irregular heartbeat", "occasional dizziness"],
    "duration": "2 weeks"
  }
}
```

**Response:**
```json
{
  "specialist": "cardiologist",
  "opinion": "Irregular heartbeat can have various causes...",
  "confidence": 0.88,
  "recommendations": [
    "Schedule an ECG test",
    "Monitor symptoms daily",
    "Avoid caffeine and stress"
  ],
  "urgency": "moderate",
  "follow_up": "Schedule appointment within 1-2 weeks"
}
```

## Anatomy & Body Parts

### Get Body Parts Overview
```http
GET /anatomy/
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "user_id": "user_123",
  "body_parts": {
    "heart": {
      "name": "Heart",
      "current_severity": "mild",
      "event_count": 3,
      "last_updated": "2025-07-06T13:30:00Z",
      "conditions": ["hypertension", "irregular heartbeat"]
    },
    "brain": {
      "name": "Brain",
      "current_severity": "normal",
      "event_count": 1,
      "last_updated": "2025-07-05T10:00:00Z",
      "conditions": ["headache"]
    }
  },
  "total_body_parts": 2
}
```

### Get Specific Body Part
```http
GET /anatomy/{body_part}
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "body_part": "heart",
  "name": "Heart",
  "current_severity": "mild",
  "conditions": [
    {
      "condition": "hypertension",
      "severity": "mild",
      "first_detected": "2025-06-01",
      "last_updated": "2025-07-06"
    }
  ],
  "recent_events": [
    {
      "event_id": "event_123",
      "title": "Blood Pressure Check",
      "date": "2025-07-06",
      "severity": "normal"
    }
  ]
}
```

## Error Handling

### Standard Error Response
```json
{
  "error": "Invalid request",
  "message": "The provided document ID does not exist",
  "code": "DOCUMENT_NOT_FOUND",
  "timestamp": "2025-07-06T13:40:00Z"
}
```

### HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `413` - Payload Too Large
- `422` - Validation Error
- `429` - Too Many Requests
- `500` - Internal Server Error

### Common Error Codes
- `AUTHENTICATION_REQUIRED` - JWT token required
- `INVALID_TOKEN` - JWT token invalid or expired
- `DOCUMENT_NOT_FOUND` - Document ID not found
- `FILE_TOO_LARGE` - File exceeds 50MB limit
- `UNSUPPORTED_FORMAT` - File format not supported
- `PROCESSING_FAILED` - Document processing failed
- `RATE_LIMIT_EXCEEDED` - Too many requests

## Rate Limiting

### Default Limits
- **Authentication**: 10 requests per minute
- **Document Upload**: 5 uploads per minute
- **Chat Messages**: 20 messages per minute
- **General API**: 100 requests per minute

### Rate Limit Headers
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 85
X-RateLimit-Reset: 1641081600
```

## Examples

### Complete Document Upload Flow
```bash
# 1. Upload document
curl -X POST "http://localhost:8000/upload/document" \
  -H "Authorization: Bearer <jwt_token>" \
  -F "file=@medical_report.pdf" \
  -F "description=Blood test results"

# 2. Check processing status
curl -X GET "http://localhost:8000/upload/status/document_id" \
  -H "Authorization: Bearer <jwt_token>"

# 3. Get processed timeline
curl -X GET "http://localhost:8000/timeline/" \
  -H "Authorization: Bearer <jwt_token>"
```

### Chat Consultation Example
```bash
# Send message to medical agents
curl -X POST "http://localhost:8000/chat/message" \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I have been experiencing chest pain for 2 days",
    "session_id": "session_123"
  }'
```

### Expert Opinion Request
```bash
curl -X POST "http://localhost:8000/expert-opinion/consult" \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Should I be concerned about my irregular heartbeat?",
    "specialist": "cardiologist",
    "context": {
      "symptoms": ["irregular heartbeat", "dizziness"],
      "duration": "2 weeks"
    }
  }'
```

---

## Notes

- All timestamps are in ISO 8601 format (UTC)
- File uploads are limited to 50MB
- JWT tokens must be included in all authenticated requests
- Response times may vary based on LLM processing complexity
- Background document processing provides status updates via `/upload/status/{id}`
