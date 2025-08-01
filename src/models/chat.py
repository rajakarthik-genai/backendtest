"""
Chat response models
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime


class ChatRequest(BaseModel):
    message: str = Field(description="User's message or question")
    query: str | None = Field(default=None, description="Deprecated. Use 'message' instead.")
    include_context: bool = True
    context_window: int = 10
    include_severity_data: bool = True
    include_timeline_data: bool = True
    expert_opinion: bool = Field(default=False, description="Enable deep research mode with dynamic multi-specialist agent orchestration and comprehensive analysis")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID for maintaining context")
    
    def __init__(self, **data):
        # Handle backward compatibility for 'query' field
        if 'query' in data and 'message' not in data:
            data['message'] = data['query']
        super().__init__(**data)


class ChatMessage(BaseModel):
    message_id: str
    timestamp: datetime
    user_message: str
    assistant_message: str
    context_used: bool = False
    model: str = "unknown"


class ExpertAnalysis(BaseModel):
    """Analysis from a specific medical expert"""
    specialist: str = Field(description="Type of specialist (cardiologist, neurologist, etc.)")
    analysis: str = Field(description="Detailed analysis from this specialist")
    confidence: float = Field(description="Confidence level 0.0-1.0")
    recommendations: List[str] = Field(default_factory=list, description="Specific recommendations")
    priority: str = Field(description="Priority level: low, medium, high, critical")


class ComprehensiveResponse(BaseModel):
    """Comprehensive response with expert analysis"""
    response: str = Field(description="Main aggregated response")
    expert_analyses: List[ExpertAnalysis] = Field(default_factory=list, description="Individual expert analyses")
    summary: str = Field(description="Executive summary of all expert opinions")
    key_insights: List[str] = Field(default_factory=list, description="Key insights from analysis")
    recommended_actions: List[str] = Field(default_factory=list, description="Recommended next steps")
    confidence_score: float = Field(description="Overall confidence in the analysis")
    specialists_consulted: List[str] = Field(default_factory=list, description="List of specialists involved")


class ChatResponse(BaseModel):
    """Unified chat response model"""
    message: str = Field(description="Main response message")
    conversation_id: str = Field(description="Conversation ID for context tracking")
    expert_mode: bool = Field(default=False, description="Whether expert opinion mode was used")
    comprehensive_analysis: Optional[ComprehensiveResponse] = None
    context_used: bool = Field(default=False, description="Whether medical context was used")
    sources: List[str] = Field(default_factory=list, description="Sources of information used")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ExpertOpinionRequest(BaseModel):
    patient_id: Optional[str] = Field(default=None, description="Patient ID - will be extracted from auth if not provided")
    query: str
    urgency: str = Field(default="normal", description="normal, urgent, critical")
    include_full_history: bool = True
    focus_body_parts: Optional[List[str]] = None
