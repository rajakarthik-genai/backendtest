# MediTwin Agents API - Core Endpoints Documentation

## Overview

The MediTwin Agents API provides a comprehensive medical assistant service with AI-powered health analysis, document processing, expert consultations, and personalized health insights.

**Base URL:** `https://mackerel-liberal-loosely.ngrok-free.app`  
**API Version:** 1.0.0  
**Authentication:** Bearer Token (JWT)

## Authentication

### Login Service
**Endpoint:** `https://lenient-sunny-grouse.ngrok-free.app/auth/login`

```bash
curl -X POST https://lenient-sunny-grouse.ngrok-free.app/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "Raja@1234"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

## Core Endpoints

### 1. Document Management

#### Upload Medical Document
**POST** `/v1/documents/upload`

Upload a medical document (PDF) for processing and analysis.

```bash
curl -X POST https://mackerel-liberal-loosely.ngrok-free.app/v1/documents/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@medical_report.pdf" \
  -F "document_title=Blood Test Results"
```

**Response:**
```json
{
  "document_id": "doc_patient123_1703123456_abc12345",
  "filename": "medical_report.pdf",
  "file_size": 245760,
  "status": "uploaded",
  "processing_started": true
}
```

#### Get Documents Status
**GET** `/v1/documents/status`

Get status of all uploaded documents for the patient.

```bash
curl -X GET https://mackerel-liberal-loosely.ngrok-free.app/v1/documents/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "documents": [
    {
      "document_id": "doc_patient123_1703123456_abc12345",
      "filename": "medical_report.pdf",
      "status": "completed",
      "uploaded_at": "2024-01-15T10:30:00Z",
      "processed_at": "2024-01-15T10:32:15Z",
      "file_size": 245760,
      "extracted_text_length": 15420,
      "medical_entities_found": 45
    }
  ],
  "total_count": 1
}
```

#### Get Document Status
**GET** `/v1/documents/status/{document_id}`

Get status of a specific document.

```bash
curl -X GET https://mackerel-liberal-loosely.ngrok-free.app/v1/documents/status/doc_patient123_1703123456_abc12345 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 2. Chat Endpoints

#### Send Chat Message (Streaming)
**POST** `/v1/chat/message`

Send a message and get a personalized streaming response with context from medical history.

```bash
curl -X POST https://mackerel-liberal-loosely.ngrok-free.app/v1/chat/message \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the symptoms of diabetes?",
    "session_id": "session_123"
  }'
```

**Streaming Response:**
```
data: {"type": "start", "session_id": "session_123"}

data: {"type": "chunk", "content": "Diabetes symptoms typically include..."}

data: {"type": "chunk", "content": " increased thirst, frequent urination..."}

data: {"type": "complete", "session_id": "session_123"}
```

#### Get Chat History
**GET** `/v1/chat/history/{session_id}`

Get chat history for a specific session.

```bash
curl -X GET https://mackerel-liberal-loosely.ngrok-free.app/v1/chat/history/session_123 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Expert Opinion Endpoints

#### Get Available Specialties
**GET** `/v1/expert_opinion/specialties`

Get list of available medical specialties for consultation.

```bash
curl -X GET https://mackerel-liberal-loosely.ngrok-free.app/v1/expert_opinion/specialties \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "specialties": [
    "cardiology",
    "endocrinology",
    "neurology",
    "orthopedics",
    "dermatology",
    "gastroenterology",
    "pulmonology",
    "nephrology",
    "rheumatology",
    "oncology",
    "psychiatry",
    "pediatrics",
    "geriatrics",
    "emergency_medicine",
    "general_medicine"
  ],
  "total_count": 15,
  "description": "Available medical specialties for expert consultation"
}
```

#### Request Expert Consultation (Streaming)
**POST** `/v1/expert_opinion/consultation`

Get expert medical consultation from multiple specialists with streaming responses.

```bash
curl -X POST https://mackerel-liberal-loosely.ngrok-free.app/v1/expert_opinion/consultation \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I am experiencing chest pain and shortness of breath",
    "specialties": ["cardiology", "pulmonology"],
    "include_context": true,
    "priority": "high"
  }'
```

**Streaming Response:**
```
data: {"type": "start", "conversation_id": "expert_patient123_1703123456"}

data: {"type": "specialist_opinion", "data": {"specialist": "cardiology", "opinion": "..."}}

data: {"type": "specialist_opinion", "data": {"specialist": "pulmonology", "opinion": "..."}}

data: {"type": "aggregated_chunk", "content": "Based on the consultation..."}

data: {"type": "complete", "conversation_id": "expert_patient123_1703123456"}
```

#### Get Consultation History
**GET** `/v1/expert_opinion/consultation/{conversation_id}`

Get history of a specific expert consultation.

```bash
curl -X GET https://mackerel-liberal-loosely.ngrok-free.app/v1/expert_opinion/consultation/expert_patient123_1703123456 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. Body Parts Endpoints

#### Get Available Body Parts
**GET** `/v1/body_parts/list`

Get list of all available body parts for severity tracking.

```bash
curl -X GET https://mackerel-liberal-loosely.ngrok-free.app/v1/body_parts/list \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "body_parts": [
    "Brain", "Heart", "Lungs", "Liver", "Kidneys", "Stomach", "Intestines",
    "Pancreas", "Spleen", "Gallbladder", "Bladder", "Uterus", "Ovaries",
    "Testes", "Prostate", "Breasts", "Thyroid", "Adrenal glands", "Pituitary",
    "Spine", "Joints", "Muscles", "Skin", "Eyes", "Ears", "Nose", "Throat",
    "Teeth", "Hair", "Nails", "Blood vessels", "Lymph nodes"
  ],
  "total_count": 32,
  "severity_levels": ["NA", "normal", "mild", "moderate", "severe", "critical"],
  "description": "Available body parts for severity tracking and timeline analysis"
}
```

#### Get Body Parts Severity
**GET** `/v1/body_parts/severity`

Get severity status for all 30+ body parts for the patient.

```bash
curl -X GET https://mackerel-liberal-loosely.ngrok-free.app/v1/body_parts/severity \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "patient_id": "patient123",
  "body_parts": [
    {
      "name": "Brain",
      "severity": "mild",
      "event_count": 3,
      "last_updated": "2024-01-15T10:30:00Z"
    },
    {
      "name": "Heart",
      "severity": "normal",
      "event_count": 1,
      "last_updated": "2024-01-10T14:20:00Z"
    },
    {
      "name": "Lungs",
      "severity": "NA",
      "event_count": 0,
      "last_updated": "2024-01-15T10:30:00Z"
    }
  ],
  "total_parts": 32,
  "last_updated": "2024-01-15T10:30:00Z"
}
```

#### Get Body Part Timeline
**GET** `/v1/body_parts/timeline/{body_part}`

Get timeline of events for a specific body part.

```bash
curl -X GET https://mackerel-liberal-loosely.ngrok-free.app/v1/body_parts/timeline/Brain \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "body_part": "Brain",
  "patient_id": "patient123",
  "events": [
    {
      "event_id": "event_123",
      "timestamp": "2024-01-15T10:30:00Z",
      "title": "Headache episode",
      "description": "Patient reported severe headache lasting 2 hours",
      "severity": "moderate",
      "source": "document"
    }
  ],
  "total_events": 1,
  "severity_summary": {
    "NA": 0,
    "normal": 0,
    "mild": 0,
    "moderate": 1,
    "severe": 0,
    "critical": 0
  }
}
```

#### Get Body Part Timeline Range
**GET** `/v1/body_parts/timeline/{body_part}/range`

Get timeline of events for a specific body part within a date range.

```bash
curl -X GET "https://mackerel-liberal-loosely.ngrok-free.app/v1/body_parts/timeline/Heart/range?start_date=2020-01-01&end_date=2021-12-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 5. Reports Endpoints

#### Generate Health Report
**POST** `/v1/reports/generate`

Generate a comprehensive health report with expert opinion integration.

```bash
curl -X POST https://mackerel-liberal-loosely.ngrok-free.app/v1/reports/generate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "comprehensive",
    "title": "Comprehensive Health Report",
    "include_expert_opinion": true,
    "date_range": {
      "start_date": "2023-01-01",
      "end_date": "2024-01-15"
    },
    "format": "markdown"
  }'
```

**Response:**
```json
{
  "report_id": "report_patient123_1703123456_abc12345",
  "title": "Comprehensive Health Report",
  "content": "# Comprehensive Health Report\n\n## Executive Summary\n\nThis report provides a comprehensive analysis...",
  "generated_at": "2024-01-15T10:30:00Z",
  "report_type": "comprehensive",
  "file_size": 15420,
  "download_url": "/api/v1/reports/download/report_patient123_1703123456_abc12345"
}
```

#### Generate Body Part Report
**POST** `/v1/reports/generate`

Generate a focused report for a specific body part.

```bash
curl -X POST https://mackerel-liberal-loosely.ngrok-free.app/v1/reports/generate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "body_part",
    "title": "Brain Health Report",
    "body_part": "Brain",
    "include_expert_opinion": true,
    "format": "markdown"
  }'
```

#### Get Report Status
**GET** `/v1/reports/status/{report_id}`

Get status of a report generation.

```bash
curl -X GET https://mackerel-liberal-loosely.ngrok-free.app/v1/reports/status/report_patient123_1703123456_abc12345 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Download Report
**GET** `/v1/reports/download/{report_id}`

Download a generated report in PDF or markdown format.

```bash
# Download as PDF
curl -X GET "https://mackerel-liberal-loosely.ngrok-free.app/v1/reports/download/report_patient123_1703123456_abc12345?format=pdf" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  --output health_report.pdf

# Download as Markdown
curl -X GET "https://mackerel-liberal-loosely.ngrok-free.app/v1/reports/download/report_patient123_1703123456_abc12345?format=markdown" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  --output health_report.md
```

#### List Reports
**GET** `/v1/reports/list`

List generated reports for the patient.

```bash
curl -X GET "https://mackerel-liberal-loosely.ngrok-free.app/v1/reports/list?limit=10&skip=0" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 6. Health Check Endpoints

#### Main Health Check
**GET** `/health`

Check overall system health.

```bash
curl -X GET https://mackerel-liberal-loosely.ngrok-free.app/health
```

#### Service Health Checks
Each service has its own health check endpoint:

```bash
# Documents service
curl -X GET https://mackerel-liberal-loosely.ngrok-free.app/v1/documents/health

# Chat service
curl -X GET https://mackerel-liberal-loosely.ngrok-free.app/v1/chat/health

# Expert opinion service
curl -X GET https://mackerel-liberal-loosely.ngrok-free.app/v1/expert_opinion/health

# Body parts service
curl -X GET https://mackerel-liberal-loosely.ngrok-free.app/v1/body_parts/health

# Reports service
curl -X GET https://mackerel-liberal-loosely.ngrok-free.app/v1/reports/health
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- **200**: Success
- **400**: Bad Request (invalid parameters)
- **401**: Unauthorized (invalid or missing token)
- **404**: Not Found
- **500**: Internal Server Error

Error responses include a message describing the issue:

```json
{
  "detail": "Error description"
}
```

## Rate Limiting

- Document uploads: 10 per hour per user
- Chat messages: 100 per hour per user
- Expert consultations: 20 per hour per user
- Report generation: 5 per hour per user

## Data Models

### Common Fields
- `patient_id`: Unique patient identifier
- `timestamp`: ISO 8601 formatted timestamp
- `status`: Current status of the resource

### Severity Levels
- `NA`: No information available
- `normal`: Normal condition
- `mild`: Mild condition
- `moderate`: Moderate condition
- `severe`: Severe condition
- `critical`: Critical condition

## Testing

Use the provided test script to verify all endpoints:

```bash
python test_core_endpoints.py
```

This will test all core endpoints and provide a detailed report of their functionality.

## Support

For technical support or questions about the API, please refer to the system documentation or contact the development team. 