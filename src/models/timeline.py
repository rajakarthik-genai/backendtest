"""
Timeline event models
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime, date


class TimelineEvent(BaseModel):
    event_id: str
    date: datetime
    body_part: str
    event_type: str  # diagnosis, treatment, test_result, symptom
    description: str
    severity: Optional[float] = None
    source_document_id: str
    metadata: Dict[str, Any] = {}


class TimelineRequest(BaseModel):
    patient_id: str
    body_part: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    event_types: Optional[List[str]] = None
