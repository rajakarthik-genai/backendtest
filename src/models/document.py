"""
Document-related Pydantic models for medical document management.

This module defines the data structures for medical document processing,
including upload responses, document metadata, processing status tracking,
and comprehensive document information with extracted entities.

Models support:
- Document upload and processing status
- Medical entity extraction results
- File metadata and provenance
- Processing pipeline tracking
- Integration with MongoDB and Neo4j storage
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentUploadResponse(BaseModel):
    """
    Response model for document upload requests.
    
    Provides comprehensive information about uploaded document including
    processing status, estimated completion time, and unique identifiers.
    """
    document_id: str = Field(..., description="Unique document identifier")
    patient_id: str = Field(..., description="Associated patient identifier")
    status: DocumentStatus = Field(..., description="Current processing status")
    message: str = Field(..., description="Status message or processing details")
    uploaded_at: datetime = Field(..., description="Upload timestamp")
    estimated_processing_time: int = Field(
        default=120, 
        description="Estimated processing time in seconds based on document complexity"
    )


class PatientDocument(BaseModel):
    """
    Complete patient document model with extracted medical data.
    
    Represents a fully processed medical document with all extracted entities,
    metadata, and relationships stored across multiple databases.
    """
    document_id: str = Field(..., description="Unique document identifier")
    patient_id: str = Field(..., description="Associated patient identifier")
    filename: str = Field(..., description="Original filename")
    content_type: Optional[str] = Field(None, description="MIME type of document")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    upload_date: datetime = Field(..., description="Document upload timestamp")
    processing_status: DocumentStatus = Field(..., description="Current processing state")
    extracted_text: Optional[str] = Field(None, description="Full extracted text content")
    medical_entities: Optional[Dict[str, Any]] = Field(
        None, 
        description="Structured medical entities including conditions, medications, procedures"
    )
    body_parts: Optional[List[str]] = Field(
        None, 
        description="Identified body parts mentioned in document"
    )
    confidence_score: Optional[float] = Field(
        None, 
        description="AI confidence score for entity extraction (0.0-1.0)"
    )
    processing_metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Processing pipeline metadata including timing, errors, versions"
    )
    file_type: str
    status: DocumentStatus
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    extracted_data_summary: Optional[Dict[str, Any]] = None
    affected_body_parts: Optional[List[str]] = None
    error_message: Optional[str] = None


class DocumentProcessingRequest(BaseModel):
    document_id: str
    patient_id: str
    file_path: str
    file_type: str
    priority: str = "normal"  # normal, high, urgent
    metadata: Dict[str, Any] = {}


class DocumentExtractionResult(BaseModel):
    document_id: str
    patient_id: str
    extraction_timestamp: datetime
    entities: List[Dict[str, Any]]
    timeline_events: List[Dict[str, Any]]
    body_part_severity: Dict[str, float]
    statistics: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None
