"""
Central Pydantic (v2) models shared by multiple endpoints / agents.

Add new DTOs here as needed to avoid duplicate class definitions.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Chat message model for conversations."""
    role: str = Field(..., description="user | assistant | system")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class MedicalRecord(BaseModel):
    """Medical record data model."""
    record_id: Optional[str] = None
    user_id: str
    record_type: str = Field(default="general")
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = Field(default="user_input")


class UserPII(BaseModel):
    """User personally identifiable information."""
    user_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    emergency_contact: Optional[str] = None


class TimelineEvent(BaseModel):
    """Timeline event model."""
    event_id: Optional[str] = None
    user_id: str
    event_type: str = Field(default="general")
    title: str
    description: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    severity: str = Field(default="medium", description="low | medium | high | critical")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class DocumentMetadata(BaseModel):
    """Document metadata model."""
    document_id: Optional[str] = None
    user_id: str
    filename: str
    file_path: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)
    processed: bool = False
    processing_status: str = Field(default="pending")
    extracted_text: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class BodyPart(BaseModel):
    """Body part representation."""
    name: str
    category: Optional[str] = None
    laterality: Optional[str] = None  # left, right, bilateral
    description: Optional[str] = None


class MedicalCondition(BaseModel):
    """Medical condition model."""
    condition_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    severity: str = Field(default="medium")
    icd_code: Optional[str] = None
    affected_body_parts: List[str] = Field(default_factory=list)


class VitalSigns(BaseModel):
    """Vital signs measurement."""
    user_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    heart_rate: Optional[int] = None
    temperature: Optional[float] = None
    respiratory_rate: Optional[int] = None
    oxygen_saturation: Optional[float] = None
    weight: Optional[float] = None
    height: Optional[float] = None


class ChatSession(BaseModel):
    """Chat session model."""
    session_id: str
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="active")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


# API Request/Response Models

class ExpertPanelRequest(BaseModel):
    """Expert panel consultation request."""
    message: str = Field(..., description="User's medical question")
    user_id: str = Field(..., description="User identifier")
    session_id: Optional[str] = Field(None, description="Chat session ID")
    include_history: bool = Field(True, description="Include chat history in analysis")
    specialties: Optional[List[str]] = Field(None, description="Requested specialist types")


class UploadRequest(BaseModel):
    """File upload request."""
    user_id: str = Field(..., description="User identifier")
    filename: str = Field(..., description="Original filename")
    description: Optional[str] = Field(None, description="Optional file description")


class UploadResponse(BaseModel):
    """File upload response."""
    document_id: str = Field(..., description="Generated document ID")
    status: str = Field(default="queued", description="Processing status")
    message: str = Field(default="File uploaded successfully")


class ChatRequest(BaseModel):
    """Chat message request."""
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Chat session ID")
    stream: bool = Field(False, description="Enable streaming response")


class ChatResponse(BaseModel):
    """Chat message response."""
    response: str = Field(..., description="Assistant response")
    session_id: str = Field(..., description="Chat session ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class TimelineRequest(BaseModel):
    """Timeline request."""
    start_date: Optional[datetime] = Field(None, description="Timeline start date")
    end_date: Optional[datetime] = Field(None, description="Timeline end date")
    event_types: Optional[List[str]] = Field(None, description="Filter by event types")
    limit: int = Field(50, description="Maximum number of events to return")


class TimelineResponse(BaseModel):
    """Timeline response."""
    events: List[TimelineEvent] = Field(..., description="Timeline events")
    total_count: int = Field(..., description="Total number of events")
    date_range: Dict[str, datetime] = Field(..., description="Actual date range returned")


class AnatomyRequest(BaseModel):
    """Anatomy query request."""
    user_id: str = Field(..., description="User identifier")
    body_part: Optional[str] = Field(None, description="Specific body part to query")
    condition: Optional[str] = Field(None, description="Medical condition to analyze")


class AnatomyResponse(BaseModel):
    """Anatomy query response."""
    body_parts: List[Dict[str, Any]] = Field(..., description="Related body parts")
    conditions: List[Dict[str, Any]] = Field(..., description="Associated conditions")
    relationships: List[Dict[str, Any]] = Field(..., description="Body part relationships")


class EventsRequest(BaseModel):
    """Events query request."""
    user_id: str = Field(..., description="User identifier")
    event_type: Optional[str] = Field(None, description="Filter by event type")
    body_part: Optional[str] = Field(None, description="Filter by affected body part")
    limit: int = Field(20, description="Maximum number of events to return")


class EventsResponse(BaseModel):
    """Events query response."""
    events: List[Dict[str, Any]] = Field(..., description="Medical events")
    summary: Dict[str, Any] = Field(..., description="Events summary statistics")


class AgentResponse(BaseModel):
    """Agent execution response."""
    result: str = Field(..., description="Agent response")
    agent_type: str = Field(..., description="Type of agent that generated response")
    confidence: float = Field(0.0, description="Confidence score 0-1")
    sources: List[str] = Field(default_factory=list, description="Source documents/data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ProcessingStatus(BaseModel):
    """Processing status model."""
    task_id: str = Field(..., description="Task identifier")
    status: str = Field(..., description="Current status")
    progress: float = Field(0.0, description="Progress percentage 0-100")
    message: str = Field("", description="Status message")
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


# Legacy compatibility
TimelineRecord = TimelineEvent  # For backward compatibility
