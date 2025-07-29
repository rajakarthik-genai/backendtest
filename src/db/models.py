"""
Database models for Medical Digital Twin API
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

from src.models.document import DocumentStatus


class Document(BaseModel):
    """Document model for MongoDB"""
    document_id: str
    patient_id: str
    filename: str
    file_type: str
    file_size: int
    status: DocumentStatus
    minio_path: str
    uploaded_by: str
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = {}
    error_message: Optional[str] = None


class Patient(BaseModel):
    """Patient model for MongoDB"""
    patient_id: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = {}


class ChatHistory(BaseModel):
    """Chat history model for MongoDB"""
    patient_id: str
    timestamp: datetime
    user_message: str
    assistant_message: str
    context_used: bool = False
    model: str
    metadata: Dict[str, Any] = {}


class ExtractionResult(BaseModel):
    """Extraction result model for MongoDB"""
    document_id: str
    patient_id: str
    extraction_timestamp: datetime
    entities: List[Dict[str, Any]]
    timeline_events: List[Dict[str, Any]]
    body_part_severity: Dict[str, float]
    statistics: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None


class ProcessingJob(BaseModel):
    """Background processing job model for Redis"""
    job_id: str
    document_id: str
    patient_id: str
    job_type: str  # extraction, report_generation, etc.
    status: str  # pending, processing, completed, failed
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
