"""
Report generation models
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime, date


class ReportRequest(BaseModel):
    patient_id: str
    report_type: str = Field(default="comprehensive", description="comprehensive, summary, body_part_specific")
    include_visualizations: bool = True
    include_recommendations: bool = True
    format: str = Field(default="pdf", description="pdf, markdown, html")
    focus_body_parts: Optional[List[str]] = None
    time_range: Optional[str] = Field(None, description="last_month, last_year, all_time, custom")
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ReportResponse(BaseModel):
    report_id: str
    status: str
    estimated_time: int
    download_url: str
    preview_url: str
    message: str
