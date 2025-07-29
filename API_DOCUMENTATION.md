# Medical Digital Twin API Documentation

Comprehensive API documentation for the Medical Digital Twin platform with sample requests and responses for all endpoints.

## 📋 Table of Contents

1. [Authentication](#authentication)
2. [Document Management](#document-management)
3. [Chat Interface](#chat-interface)
4. [Expert Opinion](#expert-opinion)
5. [Health Status](#health-status)
6. [Timeline Analysis](#timeline-analysis)
7. [Report Generation](#report-generation)
8. [3D Visualization](#3d-visualization)

---

## 🔐 Authentication

All endpoints require JWT authentication via the `Authorization` header:
```
Authorization: Bearer <jwt_token>
```

---

## 📄 Document Management

### Upload Document

**POST** `/api/v1/documents/upload`

Upload a medical document (PDF, image) for processing.

#### Request
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/medical_report.pdf" \
  -F "patient_id=patient_123" \
  -F "metadata={\"source\":\"hospital_records\",\"type\":\"lab_report\"}"
```

#### Response (200 OK)
```json
{
  "document_id": "doc_7f8a9b2c",
  "patient_id": "patient_123",
  "status": "pending",
  "message": "Document uploaded successfully. Processing initiated.",
  "uploaded_at": "2024-01-15T10:30:00Z",
  "estimated_processing_time": 120
}
```

### Get Document Status

**GET** `/api/v1/documents/{document_id}/status`

#### Request
```bash
curl -X GET "http://localhost:8000/api/v1/documents/doc_7f8a9b2c/status" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

#### Response (200 OK)
```json
{
  "document_id": "doc_7f8a9b2c",
  "status": "completed",
  "processing_started": "2024-01-15T10:30:05Z",
  "processing_completed": "2024-01-15T10:31:45Z",
  "extracted_entities": {
    "conditions": ["Hypertension", "Type 2 Diabetes"],
    "medications": ["Metformin", "Lisinopril"],
    "body_parts": ["heart", "kidneys"],
    "severity": "moderate"
  },
  "confidence_score": 0.92
}
```

### Get Document Details

**GET** `/api/v1/documents/{document_id}`

#### Request
```bash
curl -X GET "http://localhost:8000/api/v1/documents/doc_7f8a9b2c" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

#### Response (200 OK)
```json
{
  "document_id": "doc_7f8a9b2c",
  "patient_id": "patient_123",
  "filename": "medical_report.pdf",
  "content_type": "application/pdf",
  "file_size": 245760,
  "status": "completed",
  "uploaded_at": "2024-01-15T10:30:00Z",
  "processed_at": "2024-01-15T10:31:45Z",
  "extracted_text": "Patient shows signs of hypertension...",
  "medical_entities": {
    "conditions": [
      {
        "name": "Hypertension",
        "body_part": "cardiovascular",
        "severity": "moderate",
        "confidence": 0.95
      }
    ],
    "medications": ["Metformin 500mg", "Lisinopril 10mg"],
    "procedures": ["Blood pressure monitoring"],
    "lifestyle_factors": ["sedentary lifestyle", "high sodium diet"]
  }
}
```

### Delete Document

**DELETE** `/api/v1/documents/{document_id}`

#### Request
```bash
curl -X DELETE "http://localhost:8000/api/v1/documents/doc_7f8a9b2c" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

#### Response (200 OK)
```json
{
  "message": "Document deleted successfully",
  "document_id": "doc_7f8a9b2c",
  "deleted_at": "2024-01-15T11:00:00Z"
}
```

---

## 💬 Chat Interface

### Send Chat Message (Streaming)

**POST** `/api/v1/chat/stream`

#### Request
```bash
curl -X POST "http://localhost:8000/api/v1/chat/stream" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "patient_123",
    "message": "I've been experiencing chest pain for the past 2 days",
    "session_id": "session_456",
    "include_medical_history": true
  }'
```

#### Response (Streaming)
```
data: {"type": "start", "timestamp": "2024-01-15T11:00:00Z"}

data: {"type": "content", "text": "Based on your symptoms..."}

data: {"type": "content", "text": "This could be related to your hypertension..."}

data: {"type": "end", "response": "Complete response", "metadata": {"confidence": 0.89}}
```

### Get Chat History

**GET** `/api/v1/chat/history/{patient_id}`

#### Request
```bash
curl -X GET "http://localhost:8000/api/v1/chat/history/patient_123?limit=10" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

#### Response (200 OK)
```json
{
  "patient_id": "patient_123",
  "messages": [
    {
      "id": "msg_1",
      "role": "user",
      "content": "I've been experiencing chest pain",
      "timestamp": "2024-01-15T10:45:00Z"
    },
    {
      "id": "msg_2",
      "role": "assistant",
      "content": "Based on your symptoms and medical history...",
      "timestamp": "2024-01-15T10:45:30Z"
    }
  ],
  "total_messages": 25,
  "has_more": true
}
```

---

## 🏥 Expert Opinion

### Get Expert Medical Opinion (Streaming)

**POST** `/api/v1/expert-opinion/stream`

#### Request
```bash
curl -X POST "http://localhost:8000/api/v1/expert-opinion/stream" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "patient_123",
    "query": "Should I be concerned about my recent blood pressure readings?",
    "include_full_history": true,
    "urgency_level": "moderate"
  }'
```

#### Response (Streaming)
```
data: {"type": "specialist_selection", "specialists": ["cardiologist", "general_physician"]}

data: {"type": "analysis_start", "timestamp": "2024-01-15T11:05:00Z"}

data: {"type": "content", "specialist": "cardiologist", "text": "Based on your BP readings of 140/90..."}

data: {"type": "content", "specialist": "general_physician", "text": "I agree with the cardiologist's assessment..."}

data: {"type": "consensus", "text": "Consensus: Monitor closely, lifestyle changes recommended", "confidence": 0.87}
```

### Quick Consultation

**POST** `/api/v1/expert-opinion/quick`

#### Request
```bash
curl -X POST "http://localhost:8000/api/v1/expert-opinion/quick" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "patient_123",
    "query": "Is my medication dosage appropriate?",
    "specialty": "cardiology"
  }'
```

#### Response (200 OK)
```json
{
  "response": "Based on your current medications and recent lab results...",
  "specialist": "cardiologist",
  "confidence": 0.91,
  "sources": ["patient_history", "current_medications", "lab_results"],
  "recommendations": [
    "Continue current medication regimen",
    "Monitor blood pressure weekly",
    "Schedule follow-up in 3 months"
  ],
  "timestamp": "2024-01-15T11:10:00Z"
}
```

---

## 🫀 Health Status

### Get Body Parts Health Overview

**GET** `/api/v1/health/body-parts/{patient_id}`

#### Request
```bash
curl -X GET "http://localhost:8000/api/v1/health/body-parts/patient_123" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

#### Response (200 OK)
```json
{
  "patient_id": "patient_123",
  "body_parts": [
    {
      "name": "cardiovascular",
      "status": "moderate",
      "severity": "moderate",
      "last_updated": "2024-01-15T10:31:45Z",
      "conditions": ["Hypertension", "High cholesterol"],
      "confidence": 0.89
    },
    {
      "name": "kidneys",
      "status": "mild",
      "severity": "mild",
      "last_updated": "2024-01-15T10:31:45Z",
      "conditions": ["Stage 2 CKD"],
      "confidence": 0.85
    }
  ],
  "overall_health_score": 65,
  "last_full_assessment": "2024-01-15T10:31:45Z"
}
```

### Get Health Summary

**GET** `/api/v1/health/summary/{patient_id}`

#### Request
```bash
curl -X GET "http://localhost:8000/api/v1/health/summary/patient_123" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

#### Response (200 OK)
```json
{
  "patient_id": "patient_123",
  "summary": {
    "overall_status": "moderate_concern",
    "critical_body_parts": ["cardiovascular"],
    "monitoring_required": ["kidneys", "blood_sugar"],
    "key_findings": [
      "Uncontrolled hypertension requiring medication adjustment",
      "Early stage kidney disease - monitor creatinine levels",
      "Diabetes management appears adequate"
    ],
    "recommendations": [
      "Schedule cardiology consultation within 2 weeks",
      "Increase BP medication dosage",
      "Monthly kidney function monitoring"
    ]
  },
  "generated_at": "2024-01-15T11:15:00Z",
  "confidence": 0.88
}
```

### Get 3D Visualization Data

**GET** `/api/v1/health/3d-visualization/{patient_id}`

#### Request
```bash
curl -X GET "http://localhost:8000/api/v1/health/3d-visualization/patient_123" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

#### Response (200 OK)
```json
{
  "patient_id": "patient_123",
  "visualization_data": {
    "body_model": "human_anatomy",
    "affected_areas": [
      {
        "body_part": "heart",
        "position": [0.2, 0.4, 0.1],
        "severity": "moderate",
        "color": "#ff6b6b",
        "conditions": ["hypertension"],
        "size": 0.8
      },
      {
        "body_part": "kidneys",
        "position": [-0.3, 0.1, -0.2],
        "severity": "mild",
        "color": "#ffd93d",
        "conditions": ["CKD_stage_2"],
        "size": 0.6
      }
    ],
    "heatmap_data": {
      "severity_gradient": ["#00ff00", "#ffff00", "#ff0000"],
      "values": [0.3, 0.6, 0.8]
    }
  }
}
```

---

## 📊 Timeline Analysis

### Get Body Part Timeline

**POST** `/api/v1/timeline/events`

#### Request
```bash
curl -X POST "http://localhost:8000/api/v1/timeline/events" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "patient_123",
    "body_part": "cardiovascular",
    "start_date": "2023-01-01",
    "end_date": "2024-01-15"
  }'
```

#### Response (200 OK)
```json
{
  "patient_id": "patient_123",
  "body_part": "cardiovascular",
  "events": [
    {
      "id": "event_1",
      "type": "diagnosis",
      "title": "Hypertension Diagnosis",
      "description": "Diagnosed with essential hypertension",
      "date": "2023-03-15",
      "severity": "moderate",
      "source": "hospital_records",
      "metadata": {
        "systolic_bp": 160,
        "diastolic_bp": 95,
        "medication_started": "Lisinopril 10mg"
      }
    },
    {
      "id": "event_2",
      "type": "medication_change",
      "title": "Dosage Increase",
      "description": "Lisinopril increased to 20mg due to inadequate response",
      "date": "2023-06-20",
      "severity": "moderate",
      "source": "cardiology_visit"
    }
  ],
  "timeline_span": "2023-01-01 to 2024-01-15",
  "total_events": 8
}
```

### Get Patient Timeline

**GET** `/api/v1/timeline/patient-timeline`

#### Request
```bash
curl -X GET "http://localhost:8000/api/v1/timeline/patient-timeline?patient_id=patient_123" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

#### Response (200 OK)
```json
{
  "patient_id": "patient_123",
  "timeline": [
    {
      "date": "2023-03-15",
      "events": [
        {
          "type": "diagnosis",
          "body_part": "cardiovascular",
          "title": "Hypertension Diagnosis",
          "severity": "moderate"
        }
      ]
    },
    {
      "date": "2023-06-20",
      "events": [
        {
          "type": "medication_change",
          "body_part": "cardiovascular",
          "title": "Lisinopril Dosage Increase",
          "severity": "moderate"
        },
        {
          "type": "lab_result",
          "body_part": "kidneys",
          "title": "Creatinine Elevated",
          "severity": "mild"
        }
      ]
    }
  ],
  "chronological_order": "oldest_to_newest",
  "total_events": 15
}
```

---

## 📈 Report Generation

### Generate Health Report

**POST** `/api/v1/reports/generate`

#### Request
```bash
curl -X POST "http://localhost:8000/api/v1/reports/generate" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "patient_123",
    "report_type": "comprehensive",
    "date_range": {
      "start": "2023-01-01",
      "end": "2024-01-15"
    },
    "include_charts": true,
    "format": "pdf"
  }'
```

#### Response (200 OK)
```json
{
  "report_id": "report_9a8b7c6d",
  "patient_id": "patient_123",
  "status": "generating",
  "report_type": "comprehensive",
  "estimated_completion": "2024-01-15T11:30:00Z",
  "download_url": "/api/v1/reports/download/report_9a8b7c6d"
}
```

### Get Report Status

**GET** `/api/v1/reports/status/{report_id}`

#### Request
```bash
curl -X GET "http://localhost:8000/api/v1/reports/status/report_9a8b7c6d" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

#### Response (200 OK)
```json
{
  "report_id": "report_9a8b7c6d",
  "status": "completed",
  "patient_id": "patient_123",
  "report_type": "comprehensive",
  "generated_at": "2024-01-15T11:25:00Z",
  "file_size": 184320,
  "download_url": "/api/v1/reports/download/report_9a8b7c6d",
  "expires_at": "2024-01-22T11:25:00Z"
}
```

### List Reports

**GET** `/api/v1/reports/list/{patient_id}`

#### Request
```bash
curl -X GET "http://localhost:8000/api/v1/reports/list/patient_123" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

#### Response (200 OK)
```json
{
  "patient_id": "patient_123",
  "reports": [
    {
      "report_id": "report_9a8b7c6d",
      "type": "comprehensive",
      "generated_at": "2024-01-15T11:25:00Z",
      "status": "completed",
      "file_size": 184320
    },
    {
      "report_id": "report_8d7c6b5a",
      "type": "timeline",
      "generated_at": "2024-01-10T09:15:00Z",
      "status": "completed",
      "file_size": 95240
    }
  ],
  "total_reports": 5
}
```

---

## 🎮 3D Visualization

### Get 3D Model Data

**GET** `/api/v1/visualization/3d-model/{patient_id}`

#### Request
```bash
curl -X GET "http://localhost:8000/api/v1/visualization/3d-model/patient_123" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

#### Response (200 OK)
```json
{
  "patient_id": "patient_123",
  "model_data": {
    "version": "1.0",
    "anatomy_type": "human_male",
    "scale": 1.0,
    "affected_areas": [
      {
        "organ": "heart",
        "position": {"x": 0.2, "y": 0.4, "z": 0.1},
        "condition": "hypertension",
        "severity": "moderate",
        "color_hex": "#ff6b6b",
        "size_multiplier": 1.2
      }
    ],
    "connections": [
      {
        "from": "heart",
        "to": "kidneys",
        "relationship": "cardio_renal_syndrome",
        "strength": 0.7
      }
    ]
  }
}
```

### Get Heatmap Data

**GET** `/api/v1/visualization/heatmap/{patient_id}`

#### Request
```bash
curl -X GET "http://localhost:8000/api/v1/visualization/heatmap/patient_123" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

#### Response (200 OK)
```json
{
  "patient_id": "patient_123",
  "heatmap_data": {
    "severity_scale": ["normal", "mild", "moderate", "severe", "critical"],
    "color_gradient": ["#00ff00", "#ffff00", "#ff9900", "#ff0000", "#8b0000"],
    "body_parts": {
      "cardiovascular": {
        "severity": "moderate",
        "value": 0.75,
        "color": "#ff6b6b",
        "conditions": ["hypertension"]
      },
      "kidneys": {
        "severity": "mild",
        "value": 0.45,
        "color": "#ffd93d",
        "conditions": ["stage_2_ckd"]
      }
    },
    "trend_data": {
      "time_range": "6_months",
      "improvements": ["kidneys"],
      "declines": ["cardiovascular"],
      "stable": ["liver", "lungs"]
    }
  }
}
```

---

## 🚨 Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request format",
  "error_code": "INVALID_FORMAT",
  "timestamp": "2024-01-15T11:30:00Z"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid or expired token",
  "error_code": "UNAUTHORIZED",
  "timestamp": "2024-01-15T11:30:00Z"
}
```

### 404 Not Found
```json
{
  "detail": "Patient not found",
  "error_code": "PATIENT_NOT_FOUND",
  "patient_id": "patient_999",
  "timestamp": "2024-01-15T11:30:00Z"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error",
  "error_code": "INTERNAL_ERROR",
  "timestamp": "2024-01-15T11:30:00Z",
  "request_id": "req_abc123"
}
```

---

## 📊 Rate Limits

| Endpoint | Rate Limit | Window |
|----------|------------|--------|
| Document Upload | 50/hour | per user |
| Chat Messages | 1000/hour | per user |
| Expert Opinion | 100/hour | per user |
| Health Data | 1000/hour | per user |
| Reports | 20/hour | per user |

---

## 🔄 Pagination

List endpoints support pagination using `limit` and `offset` parameters:

```bash
curl -X GET "http://localhost:8000/api/v1/documents/list/patient_123?limit=10&offset=20" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

---

## 📞 Support

For API support and documentation updates, please refer to:
- API Base URL: `http://localhost:8000/api/v1`
- Health Check: `GET /health`
- OpenAPI Schema: `GET /docs` (Swagger UI)
- ReDoc: `GET /redoc`

---

*Last updated: July 26, 2025*
*API Version: 1.0*
