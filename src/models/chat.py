"""
Chat request/response models
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime


class ChatRequest(BaseModel):
    query: str
    # patient_id field deprecated; patient id is now extracted from JWT
    patient_id: str | None = Field(default=None, description="Deprecated. Ignored. Patient ID is inferred from JWT.")
    include_context: bool = True
    context_window: int = 10
    include_severity_data: bool = True
    include_timeline_data: bool = True


class ChatMessage(BaseModel):
    message_id: str
    timestamp: datetime
    user_message: str
    assistant_message: str
    context_used: bool = False
    model: str = "unknown"


class ExpertOpinionRequest(BaseModel):
    patient_id: str
    query: str
    urgency: str = Field(default="normal", description="normal, urgent, critical")
    include_full_history: bool = True
    focus_body_parts: Optional[List[str]] = None
