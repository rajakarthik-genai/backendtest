# MediTwin API - Quick Reference Guide

## Authentication
```bash
# Login to get token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123"}'

# Use token in requests
curl -H "Authorization: Bearer <token>" <endpoint>
```

## Key Endpoints Summary

### 📄 Documents
- `POST /api/v1/documents/upload` - Upload medical document
- `GET /api/v1/documents` - List documents
- `GET /api/v1/documents/status` - Get processing status
- `GET /api/v1/documents/document/{id}` - Get document details
- `DELETE /api/v1/documents/delete/{id}` - Delete document

### 💬 Chat
- `POST /api/v1/chat/message` - Send chat message
- `POST /api/v1/chat/stream` - Streaming chat
- `GET /api/v1/chat/history` - Get chat history

### 👤 User
- `GET /api/v1/user/profile` - Get user profile

### 📅 Timeline & Events
- `GET /api/v1/events` - Get medical events
- `GET /api/v1/timeline/events` - Get timeline events
- `GET /api/v1/timeline/summary` - Get timeline summary

### 🔍 Analysis
- `GET /api/v1/symptoms` - Symptoms info
- `POST /api/v1/symptoms/analyze` - Analyze symptoms
- `GET /api/v1/anatomy/body-parts/severities` - Body part analysis

### 🏥 System
- `GET /health` - System health check
- `GET /api/v1/admin/health` - Admin health check
- `GET /api/v1/system/endpoints` - List endpoints

## Test Credentials
- `test@example.com` / `test123`
- `user@example.com` / `Raja@1234`
- `admin@example.com` / `admin123`

## Response Status Codes
- `200` - Success
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `422` - Validation Error
- `503` - Service Unavailable (database issues)

## Rate Limits
- Authentication: 100/hour
- Document Upload: 100/hour
- Document Operations: 1000/hour
- Chat: 1000/hour
- System: 1000/hour

## Frontend Integration Tips
1. Store JWT tokens securely
2. Use FormData for file uploads (don't set Content-Type)
3. Handle 503 errors for database unavailability
4. Implement retry logic with exponential backoff
5. Patient ID is extracted from token automatically
6. Use EventSource for streaming endpoints

## Example Upload
```javascript
const formData = new FormData();
formData.append('file', file);

fetch('/api/v1/documents/upload', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: formData
});
```

## Example Chat
```javascript
fetch('/api/v1/chat/message', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: "What does my latest blood test show?",
    include_context: true
  })
});
```
