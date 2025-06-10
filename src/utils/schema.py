"""
Central Pydantic (v2) models shared by multiple endpoints / agents.

Add new DTOs here as needed to avoid duplicate class definitions.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., description="user | assistant | system | function")
    content: str


class TimelineRecord(BaseModel):
    patient_id: str
    timestamp: datetime
    metric_name: str
    value: str | float | int | bool | None = None
    unit: str | None = ""
    source: str = "Document"


class ExpertPanelRequest(BaseModel):
    message: str
    user_id: str
    conv_id: Optional[str] = None


class UploadResponse(BaseModel):
    ingest_id: str
    status: str = "queued"
