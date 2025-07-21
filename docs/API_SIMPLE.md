# MediTwin Agents - Core API Documentation

## Overview

MediTwin Agents is a multi-agent medical AI system providing core medical analysis functionality through specialized AI agents.

**Base URL:** `http://localhost:8000/api/v1`

**Authentication:** All endpoints require JWT token in header:
```
Authorization: Bearer <JWT_TOKEN>
```

---

## Core Working Endpoints

### 1. Chat with Medical AI
**POST** `/chat/message`

Interactive chat with specialized medical AI agents.

**Request:**
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

---

### 2. Medical Timeline
**GET** `/timeline/timeline`

Get chronological timeline of medical events and interactions.

**Parameters:**
- `limit` (query): Maximum events (default: 50)
- `start_date` (query): Start date (ISO format)
- `end_date` (query): End date (ISO format)

**Response:**
```json
{
  "patient_id": "patient-uuid",
  "events": [
    {
      "event_id": "uuid-event-id",
      "timestamp": "2024-01-15T10:30:00Z",
      "event_type": "chat_interaction",
      "description": "Patient reported headache symptoms",
      "metadata": {
        "severity": "moderate",
        "agent": "general_physician"
      }
    }
  ],
  "total_events": 1,
  "timeline_period": "30 days"
}
```

---

### 3. Expert Medical Opinion
**POST** `/medical_analysis/symptoms/analyze`

Get expert analysis from specialized medical agents for symptom assessment.

**Request:**
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
  "analysis": "Based on your symptoms of headache, nausea, and dizziness persisting for 3 days, this could indicate stress-related tension headaches or possible dehydration. The timing after long work hours supports this assessment.",
  "symptoms": ["headache", "nausea", "dizziness"],
  "severity": "moderate",
  "recommendations": [
    "Take regular breaks during work",
    "Ensure adequate hydration",
    "Consider stress management techniques",
    "Consult healthcare professional if symptoms persist"
  ],
  "confidence": 0.8,
  "patient_id": "patient-uuid"
}
```

---

### 4. Document Upload & Analysis
**POST** `/upload/document`

Upload medical documents for AI analysis and processing.

**Request:**
- Content-Type: `multipart/form-data`
- `file`: Medical document (PDF, PNG, JPG - max 50MB)
- `description`: Optional description

**Response:**
```json
{
  "document_id": "uuid-document-id",
  "status": "queued",
  "message": "Document 'blood_test_report.pdf' uploaded successfully and queued for processing"
}
```

**Check Processing Status:**
**GET** `/upload/status/{document_id}`

```json
{
  "task_id": "uuid-document-id",
  "status": "completed",
  "progress": 1.0,
  "message": "Document analysis completed",
  "started_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:32:00Z",
  "error": null
}
```

---

### 5. System Health Status
**GET** `/system_info/system/status`

Get current system status and service health.

**Response:**
```json
{
  "status": "operational",
  "version": "1.0.0",
  "uptime": "24h 15m",
  "services": {
    "ai_agents": "healthy",
    "database": "healthy",
    "authentication": "healthy",
    "document_processing": "healthy"
  },
  "last_check": "2024-01-15T10:30:00Z"
}
```

---

### 6. Chat History
**GET** `/chat/history/{session_id}`

Retrieve conversation history for a specific chat session.

**Parameters:**
- `session_id` (path): Chat session identifier
- `limit` (query): Maximum messages (default: 50)

**Response:**
```json
{
  "session_id": "uuid-session-id",
  "messages": [
    {
      "role": "user",
      "content": "I have a persistent headache",
      "timestamp": "2024-01-15T10:30:00Z"
    },
    {
      "role": "assistant",
      "content": "Can you describe the headache? When did it start and how severe is it?",
      "timestamp": "2024-01-15T10:30:05Z",
      "metadata": {
        "agent": "general_physician"
      }
    }
  ],
  "total_messages": 2
}
```

---

## Quick Start Example

```bash
# 1. Get system status
curl -X GET "http://localhost:8000/api/v1/system_info/system/status"

# 2. Send a chat message (requires auth)
curl -X POST "http://localhost:8000/api/v1/chat/message" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "I have chest pain and shortness of breath"}'

# 3. Get medical timeline (requires auth)
curl -X GET "http://localhost:8000/api/v1/timeline/timeline?limit=10" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 4. Analyze symptoms (requires auth)
curl -X POST "http://localhost:8000/api/v1/medical_analysis/symptoms/analyze" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "symptoms": ["chest pain", "shortness of breath"],
    "duration": "2 hours",
    "severity": "high"
  }'
```

---

## Error Responses

**401 Unauthorized:**
```json
{
  "detail": "Authentication required"
}
```

**400 Bad Request:**
```json
{
  "detail": "Invalid request parameters"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Internal server error"
}
```

---

## Key Features

- **Multi-Agent System**: Specialized medical AI agents (GP, Cardiologist, Neurologist)
- **Real-time Chat**: Interactive medical consultations
- **Document Processing**: AI-powered medical document analysis
- **Timeline Tracking**: Chronological medical event management
- **HIPAA Compliant**: Patient data isolation and security
- **Expert Analysis**: Symptom analysis with confidence scoring

---

## Integration

This API is designed for integration with:
- Healthcare applications
- Medical practice management systems
- Patient portals
- Telemedicine platforms

**Documentation:** Full interactive docs available at `/docs` endpoint.
