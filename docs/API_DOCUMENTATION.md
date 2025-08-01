# MediTwin Agents Service - API Documentation

## Overview

The MediTwin Agents Service is a comprehensive medical digital twin API that provides document processing, medical analysis, timeline management, and intelligent chat capabilities. This documentation covers all available endpoints for frontend integration.

## Base URL
```
http://localhost:8000
```

## Authentication

All endpoints (except authentication endpoints) require a Bearer token in the Authorization header.

### Headers Required
```http
Authorization: Bearer <your_jwt_token>
Content-Type: application/json
```

---

## � Authentication Endpoints

### POST /api/v1/auth/login
Authenticate and obtain a JWT token.

**Request Body:**
```json
{
  "email": "test@example.com",
  "password": "test123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900,
  "user_id": "user_test_20250730",
  "patient_id": "PT_1C774437F95C5A44"
}
```

**Test Credentials:**
- `test@example.com` / `test123`
- `user@example.com` / `Raja@1234`
- `admin@example.com` / `admin123`

### POST /api/v1/auth/refresh
Refresh an existing token.

**Request Body:**
```json
{
  "refresh_token": "your_refresh_token"
}
```

### POST /api/v1/auth/logout
Logout and invalidate token.

---

## �📄 Document Management Endpoints

### POST /api/v1/documents/upload
Upload a medical document for processing.

**Request:**
- **Content-Type:** `multipart/form-data`
- **File Field:** `file`
- **Supported Formats:** PDF, DOCX, TXT, JPG, PNG
- **Max Size:** 50MB

**Example with curl:**
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Authorization: Bearer <token>" \
  -F "file=@medical_report.pdf"
```

**Response (200):**
```json
{
  "document_id": "doc_PT_1C774437F95C5A44_0da41c57",
  "patient_id": "PT_1C774437F95C5A44",
  "status": "pending",
  "message": "Document medical_report.pdf uploaded successfully and queued for processing",
  "uploaded_at": "2025-07-30T13:55:30.123Z",
  "estimated_processing_time": 120
}
```

### GET /api/v1/documents
List all documents for the authenticated patient.

**Query Parameters:**
- `status_filter` (optional): Filter by status (`pending`, `processing`, `completed`, `failed`)
- `limit` (optional): Number of documents to return (default: 50)
- `skip` (optional): Number of documents to skip (default: 0)

**Response (200):**
```json
[
  {
    "document_id": "doc_PT_1C774437F95C5A44_0da41c57",
    "filename": "medical_report.pdf",
    "file_type": ".pdf",
    "file_size": 64616,
    "status": "pending",
    "uploaded_at": "2025-07-30T13:55:30.123Z",
    "processed_at": null
  }
]
```

### GET /api/v1/documents/status
Get detailed status of all documents with extraction summaries.

**Response (200):**
```json
[
  {
    "document_id": "doc_PT_1C774437F95C5A44_0da41c57",
    "patient_id": "PT_1C774437F95C5A44",
    "filename": "medical_report.pdf",
    "file_type": ".pdf",
    "status": "completed",
    "uploaded_at": "2025-07-30T13:55:30.123Z",
    "processed_at": "2025-07-30T13:57:45.678Z",
    "extracted_data_summary": {
      "entities_found": 15,
      "entity_types": ["diagnosis", "medication", "symptom"],
      "average_severity": 6.5
    },
    "affected_body_parts": ["heart", "lungs"],
    "error_message": null
  }
]
```

### GET /api/v1/documents/document/{document_id}
Get detailed information about a specific document.

**Response (200):**
```json
{
  "document_id": "doc_PT_1C774437F95C5A44_0da41c57",
  "patient_id": "PT_1C774437F95C5A44",
  "filename": "medical_report.pdf",
  "status": "completed",
  "extraction_details": {
    "entities": [
      {
        "type": "diagnosis",
        "text": "Hypertension",
        "severity": 7,
        "date": "2025-07-30",
        "body_parts": ["heart"],
        "confidence": 0.95
      }
    ],
    "timeline_events": [
      {
        "event_type": "diagnosis",
        "description": "Patient diagnosed with hypertension",
        "date": "2025-07-30",
        "body_parts": ["heart"]
      }
    ]
  }
}
```

### POST /api/v1/documents/reprocess/{document_id}
Reprocess a failed or completed document.

**Response (200):**
```json
{
  "message": "Document queued for reprocessing",
  "document_id": "doc_PT_1C774437F95C5A44_0da41c57",
  "status": "pending"
}
```

### DELETE /api/v1/documents/delete/{document_id}
Delete a document and all associated data.

**Response (200):**
```json
{
  "message": "Document deleted successfully",
  "document_id": "doc_PT_1C774437F95C5A44_0da41c57"
}
```

---

## 👤 User Management Endpoints

### GET /api/v1/user/profile
Get current user profile information.

**Response (200):**
```json
{
  "user_id": "user_test_20250730",
  "patient_id": "PT_1C774437F95C5A44",
  "email": "test@example.com",
  "username": "test",
  "is_provider": false,
  "created_at": "2025-07-30T13:55:30.123Z"
}
```

---

## 📅 Events & Timeline Endpoints

### GET /api/v1/events
Get medical events for the patient.

**Response (200):**
```json
{
  "patient_id": "PT_1C774437F95C5A44",
  "events": [
    {
      "event_id": "evt_001",
      "event_type": "diagnosis",
      "date": "2025-07-30",
      "description": "Hypertension diagnosis",
      "severity": 7,
      "body_parts": ["heart"]
    }
  ],
  "total_events": 2
}
```

### GET /api/v1/timeline/events
Get chronological timeline events.

**Query Parameters:**
- `start_date` (optional): Filter events from this date (YYYY-MM-DD)
- `end_date` (optional): Filter events to this date (YYYY-MM-DD)
- `event_types` (optional): Filter by event types (array)
- `limit` (optional): Number of events to return (default: 100)

**Response (200):**
```json
[
  {
    "event_id": "evt_001",
    "event_type": "diagnosis",
    "date": "2025-07-30",
    "description": "Patient diagnosed with hypertension",
    "severity": 7,
    "body_parts": ["heart"],
    "patient_id": "PT_1C774437F95C5A44"
  }
]
```

### GET /api/v1/timeline/summary
Get timeline summary statistics.

**Response (200):**
```json
{
  "patient_id": "PT_1C774437F95C5A44",
  "total_events": 25,
  "affected_body_parts": 8,
  "event_types": ["diagnosis", "treatment", "medication", "test"],
  "date_range": {
    "earliest": "2024-01-15",
    "latest": "2025-07-30"
  },
  "average_severity": 5.2
}
```

---

## 🔍 Symptoms & Analysis Endpoints

### GET /api/v1/symptoms
Get symptoms analysis information.

**Response (200):**
```json
{
  "patient_id": "PT_1C774437F95C5A44",
  "analysis_info": "Symptoms analysis based on medical history",
  "available_services": ["symptom_analysis", "severity_assessment", "recommendations"]
}
```

### POST /api/v1/symptoms/analyze
Analyze symptoms and provide medical insights.

**Request Body:**
```json
{
  "symptoms": ["chest pain", "shortness of breath"],
  "severity": 7,
  "duration": "2 days",
  "additional_info": "Pain increases with activity"
}
```

**Response (200):**
```json
{
  "patient_id": "PT_1C774437F95C5A44",
  "analysis": {
    "primary_concerns": ["cardiac", "respiratory"],
    "severity_assessment": 8,
    "recommendations": ["Seek immediate medical attention", "Monitor vital signs"],
    "related_conditions": ["angina", "myocardial infarction"],
    "body_parts_affected": ["heart", "lungs"]
  },
  "timestamp": "2025-07-30T13:55:30.123Z"
}
```

---

## 🏥 Anatomy & Body Parts Endpoints

### GET /api/v1/anatomy/body-parts/severities
Get severity analysis for different body parts.

**Response (200):**
```json
{
  "patient_id": "PT_1C774437F95C5A44",
  "body_parts": [
    {
      "body_part": "heart",
      "avg_severity": 7.2,
      "max_severity": 9,
      "min_severity": 5,
      "event_count": 12
    },
    {
      "body_part": "lungs",
      "avg_severity": 4.8,
      "max_severity": 8,
      "min_severity": 2,
      "event_count": 6
    }
  ]
}
```

---

## 💬 Chat & AI Endpoints

### POST /api/v1/chat/message
Send a message to the medical AI assistant.

**Request Body:**
```json
{
  "query": "What does my latest blood test show?",
  "include_context": true,
  "include_severity_data": true,
  "include_timeline_data": true,
  "context_window": 10
}
```

**Response (200):**
```json
{
  "response": "Based on your latest blood test from July 28th, your cholesterol levels show improvement since your last test. Your LDL cholesterol has decreased from 180 to 155 mg/dL, which is moving in the right direction. However, it's still above the recommended level of 100 mg/dL for someone with your cardiac history...",
  "patient_id": "PT_1C774437F95C5A44",
  "context_used": true,
  "model": "gpt-4o-mini",
  "timestamp": "2025-07-30T13:55:30.123Z"
}
```

### POST /api/v1/chat/stream
Get streaming chat responses (Server-Sent Events).

**Request Body:**
```json
{
  "query": "Explain my medication interactions",
  "include_context": true
}
```

**Response:** Server-Sent Events stream
```
data: {"id":"chat-123-0","object":"chat.completion.chunk","choices":[{"delta":{"content":"Based on"}}]}

data: {"id":"chat-123-1","object":"chat.completion.chunk","choices":[{"delta":{"content":" your current"}}]}

data: [DONE]
```

### GET /api/v1/chat/history
Get chat conversation history.

**Query Parameters:**
- `limit` (optional): Number of messages to return (default: 50)
- `offset` (optional): Number of messages to skip (default: 0)

**Response (200):**
```json
{
  "patient_id": "PT_1C774437F95C5A44",
  "messages": [
    {
      "message_id": "msg_001",
      "timestamp": "2025-07-30T13:55:30.123Z",
      "user_message": "What does my latest blood test show?",
      "assistant_message": "Based on your latest blood test...",
      "context_used": true,
      "model": "gpt-4o-mini"
    }
  ],
  "total": 15
}
```

---

## 🏥 System & Health Endpoints

### GET /health
Check system health and database connectivity.

**Response (200):**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "services": {
    "mongodb": true,
    "neo4j": true,
    "redis": true
  },
  "timestamp": 1753883812.0432684
}
```

### GET /api/v1/admin/health
Detailed admin health check (requires provider access).

### GET /api/v1/system/endpoints
List all available API endpoints.

**Response (200):**
```json
{
  "endpoints": [
    {
      "path": "/api/v1/documents/upload",
      "method": "POST",
      "description": "Upload medical document"
    }
  ],
  "total_endpoints": 25
}
```

---

## 📊 Error Responses

### Standard Error Format
```json
{
  "detail": "Error description",
  "error": "ERROR_CODE",
  "request_id": "req_1753883890078"
}
```

### Common HTTP Status Codes
- **200**: Success
- **400**: Bad Request - Invalid input data
- **401**: Unauthorized - Invalid or missing token
- **403**: Forbidden - Insufficient permissions
- **404**: Not Found - Resource not found
- **405**: Method Not Allowed - HTTP method not supported
- **422**: Validation Error - Request data validation failed
- **429**: Too Many Requests - Rate limit exceeded
- **500**: Internal Server Error - Server-side error
- **503**: Service Unavailable - Database or service unavailable

---

## 🚀 Frontend Integration Examples

### JavaScript/TypeScript Example
```javascript
const API_BASE_URL = 'http://localhost:8000';

class MediTwinAPI {
  constructor(token) {
    this.token = token;
    this.headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  async uploadDocument(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/api/v1/documents/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`
      },
      body: formData
    });
    
    return await response.json();
  }

  async getDocuments() {
    const response = await fetch(`${API_BASE_URL}/api/v1/documents`, {
      headers: this.headers
    });
    return await response.json();
  }

  async sendChatMessage(message) {
    const response = await fetch(`${API_BASE_URL}/api/v1/chat/message`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({
        query: message,
        include_context: true
      })
    });
    return await response.json();
  }

  async getUserProfile() {
    const response = await fetch(`${API_BASE_URL}/api/v1/user/profile`, {
      headers: this.headers
    });
    return await response.json();
  }
}

// Usage
const api = new MediTwinAPI('your_jwt_token');
const profile = await api.getUserProfile();
```

### React Hook Example
```javascript
import { useState, useEffect } from 'react';

export const useDocuments = (token) => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        const response = await fetch('/api/v1/documents', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        const data = await response.json();
        setDocuments(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (token) {
      fetchDocuments();
    }
  }, [token]);

  return { documents, loading, error };
};
```

---

## 🔧 Rate Limits

- **Authentication**: 100 requests per hour
- **Document Upload**: 100 uploads per hour
- **Document Operations**: 1000 requests per hour
- **Chat Messages**: 1000 messages per hour
- **Chat Streaming**: 1000 requests per hour
- **Chat History**: 100 requests per hour
- **System Endpoints**: 1000 requests per hour

---

## 📝 Notes for Frontend Development

1. **Token Management**: Store JWT tokens securely and handle token expiration
2. **File Upload**: Use FormData for document uploads, don't set Content-Type header
3. **Error Handling**: Always handle 503 errors for database unavailability
4. **Rate Limiting**: Implement retry logic with exponential backoff
5. **Streaming**: Use EventSource for chat streaming endpoints
6. **Patient ID**: Automatically extracted from JWT token, no need to pass manually
7. **CORS**: Configure your frontend domain in backend CORS settings for production

---

## 🔗 WebSocket Support

Currently not implemented, but planned for future releases for real-time document processing updates.

---

This documentation covers all the available endpoints in the MediTwin Agents Service. For additional support or feature requests, please refer to the project repository.
