"""
Health status models
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class SeverityLevel(str, Enum):
    NORMAL = "normal"  # Green
    MILD = "mild"      # Yellow
    MODERATE = "moderate"  # Orange
    SEVERE = "severe"  # Red
    CRITICAL = "critical"  # Dark Red
    UNKNOWN = "unknown"  # Grey


class BodyPartHealth(BaseModel):
    body_part: str
    severity: Optional[float] = Field(None, ge=0, le=10)
    severity_level: SeverityLevel
    last_updated: Optional[datetime] = None
    data_points: int = 0
    conditions: List[str] = []
    treatments: List[str] = []
    notes: Optional[str] = None


class HealthSummary(BaseModel):
    patient_id: str
    last_updated: datetime
    overall_health_score: float = Field(..., ge=0, le=10)
    active_conditions: int
    upcoming_appointments: int
    medications_count: int
    recent_documents: int
    critical_alerts: List[str] = []
    body_parts_affected: int
    timeline_events_count: int


class VisualizationData(BaseModel):
    position: Dict[str, float]  # x, y, z coordinates
    severity: float
    color: str
    label: str
    conditions: List[str] = []
    last_updated: Optional[datetime] = None
