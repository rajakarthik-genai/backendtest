# MediTwin Agents API Endpoints

This document lists all FastAPI endpoints in the codebase, grouped by category, with a brief use case for each endpoint.

---

## Root and Health

- **GET /**  
  _Returns API info and available documentation links._

- **GET /health**  
  _Health check for the API server._

---

## Versioned API (`/v1`) Endpoints

### Admin
- **GET /v1/admin/patients/mongo**  
  _List all patient IDs with data in MongoDB._
- **GET /v1/admin/patients/neo4j**  
  _List all patient IDs with data in Neo4j._
- **GET /v1/admin/patients/milvus**  
  _List all patient IDs with data in Milvus._
- **GET /v1/admin/patients/all**  
  _List all patient IDs across all databases._
- **GET /v1/admin/patient/{patient_id}/mongo**  
  _Get a patient's data from MongoDB._
- **GET /v1/admin/patient/{patient_id}/neo4j**  
  _Get a patient's data from Neo4j._
- **GET /v1/admin/patient/{patient_id}/milvus**  
  _Get a patient's data from Milvus._
- **GET /v1/admin/patient/{patient_id}/all**  
  _Get a patient's data from all databases._
- **DELETE /v1/admin/patient/{patient_id}**  
  _Delete all patient data across all databases._
- **GET /v1/admin/system/health**  
  _Check health of all database systems._
- **GET /v1/admin/stats/overview**  
  _Get system-wide statistics overview._

### Anatomy
- **GET /v1/anatomy/body-parts**  
  _Get severity status for all 30 body parts for 3D visualization._

### Analytics
- **GET /v1/analytics/analytics/trends**  
  _Get analytics trends for a given period._
- **GET /v1/analytics/analytics/dashboard**  
  _Get analytics dashboard data._
- **GET /v1/analytics/health/score**  
  _Get health score analytics._
- **GET /v1/analytics/health/risk-assessment**  
  _Get health risk assessment analytics._

### Chat
- **POST /v1/chat/message**  
  _Send a chat message and get a response (non-streaming)._ 
- **POST /v1/chat**  
  _Alias for /message; basic chat endpoint for frontend compatibility._

### Documents
- **POST /v1/documents/upload**  
  _Upload a medical document for processing._
- **DELETE /v1/documents/document/{document_id}**  
  _Delete an uploaded document and its processed data._

### Events
- **POST /v1/events/**  
  _Create a new manual health event._
- **PUT /v1/events/{event_id}**  
  _Update an existing event._
- **DELETE /v1/events/{event_id}**  
  _Delete an event._

### Expert Opinion
- **POST /v1/expert_opinion/expert-opinion**  
  _Get expert medical opinion from multiple specialist agents._

### Knowledge Base
- **GET /v1/knowledge_base/knowledge/search**  
  _Search the medical knowledge base._
- **GET /v1/knowledge_base/medical/information**  
  _Get medical information on a specific topic._
- **POST /v1/knowledge_base/drugs/interactions**  
  _Check for drug interactions._

### Medical Analysis
- **POST /v1/medical_analysis/symptoms/analyze**  
  _Analyze symptoms for possible conditions._
- **POST /v1/medical_analysis/diagnostic/suggestions**  
  _Get diagnostic suggestions based on symptoms and history._
- **POST /v1/medical_analysis/treatment/recommendations**  
  _Get treatment recommendations for a condition._

### OpenAI-Compatible
- **POST /v1/openai-compatible/chat/completions**  
  _OpenAI-compatible chat completions endpoint for CrewAI integration._

### System Info
- **GET /v1/system_info/system/status**  
  _Get system status and service health._
- **GET /v1/system_info/info**  
  _Get system information._
- **GET /v1/system_info/metrics**  
  _Get system metrics._
- **GET /v1/system_info/database/status**  
  _Get database status information._

### Timeline
- **GET /v1/timeline/timeline**  
  _Get a user's medical event timeline._
- **GET /v1/timeline/summary**  
  _Get a summary of timeline events._
- **POST /v1/timeline/timeline**  
  _Create a new timeline event for a user._

### Tools
- _Various endpoints for internal tools._

### Upload
- **POST /v1/upload/document**  
  _Upload a document for ingestion._
- **GET /v1/upload/status/{document_id}**  
  _Get the status of an uploaded document._
- **GET /v1/upload/documents**  
  _List all uploaded documents for a user._
- **DELETE /v1/upload/document/{document_id}**  
  _Delete an uploaded document._

### User Profile
- _Endpoints for user profile management._

---

**If you need request/response models or more details for any endpoint, let me know!** 