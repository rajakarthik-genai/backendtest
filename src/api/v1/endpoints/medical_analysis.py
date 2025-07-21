"""
Medical Analysis endpoints for symptom analysis, diagnostic suggestions, and treatment recommendations.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from src.auth.dependencies import CurrentUser
from src.utils.logging import logger
from src.api.v1.endpoints.chat import ChatRequest, send_message

router = APIRouter(tags=["medical-analysis"])

class SymptomAnalysisRequest(BaseModel):
    symptoms: List[str] = Field(..., description="List of symptoms")
    duration: str = Field("", description="Duration of symptoms")
    severity: str = Field("moderate", description="Severity level")
    context: str = Field("", description="Additional context")

class DiagnosticSuggestionsRequest(BaseModel):
    symptoms: List[str] = Field(..., description="List of symptoms")
    medical_history: Optional[str] = Field("", description="Medical history")

class TreatmentRequest(BaseModel):
    condition: str = Field(..., description="Medical condition")
    symptoms: Optional[List[str]] = Field([], description="Associated symptoms")
    severity: Optional[str] = Field("moderate", description="Severity")

@router.post("/symptoms/analyze")
async def analyze_symptoms(
    request: SymptomAnalysisRequest,
    current_user: CurrentUser
):
    """Analyze symptoms using AI agents"""
    try:
        chat_request = ChatRequest(
            message=f"Please analyze these symptoms: {', '.join(request.symptoms)}. Duration: {request.duration}. Severity: {request.severity}. Additional context: {request.context}"
        )
        
        response = await send_message(chat_request, current_user)
        
        return {
            "analysis": response.response,
            "symptoms": request.symptoms,
            "severity": request.severity,
            "recommendations": ["Consult with a healthcare professional", "Monitor symptoms"],
            "confidence": 0.8,
            "patient_id": current_user.patient_id
        }
    except Exception as e:
        logger.error(f"Symptom analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/diagnostic/suggestions")
async def get_diagnostic_suggestions(
    request: DiagnosticSuggestionsRequest,
    current_user: CurrentUser
):
    """Get diagnostic suggestions based on symptoms"""
    try:
        chat_request = ChatRequest(
            message=f"Provide diagnostic suggestions for symptoms: {', '.join(request.symptoms)}. Medical history: {request.medical_history}"
        )
        
        response = await send_message(chat_request, current_user)
        
        return {
            "suggestions": [
                {"condition": "Further evaluation needed", "probability": 0.8, "reasoning": response.response}
            ],
            "symptoms": request.symptoms,
            "disclaimer": "This is AI-generated information. Please consult a healthcare professional.",
            "patient_id": current_user.patient_id
        }
    except Exception as e:
        logger.error(f"Diagnostic suggestions failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/treatment/recommendations")
async def get_treatment_recommendations(
    request: TreatmentRequest,
    current_user: CurrentUser
):
    """Get treatment recommendations"""
    try:
        chat_request = ChatRequest(
            message=f"Provide treatment recommendations for condition: {request.condition}. Symptoms: {', '.join(request.symptoms)}. Severity: {request.severity}"
        )
        
        response = await send_message(chat_request, current_user)
        
        return {
            "recommendations": [
                {"treatment": "Professional consultation", "priority": "high", "details": response.response}
            ],
            "condition": request.condition,
            "disclaimer": "Always consult with healthcare professionals before starting treatment.",
            "patient_id": current_user.patient_id
        }
    except Exception as e:
        logger.error(f"Treatment recommendations failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health/insights")
async def get_health_insights(current_user: CurrentUser):
    """Get health insights for the user"""
    return {
        "insights": [
            {"type": "general", "message": "Regular exercise improves overall health", "priority": "medium"},
            {"type": "nutrition", "message": "Balanced diet supports immune system", "priority": "medium"}
        ],
        "health_score": 75,
        "last_updated": datetime.utcnow().isoformat(),
        "patient_id": current_user.patient_id
    }
