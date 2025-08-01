"""
Medical Analysis API endpoints for symptoms and diagnostic analysis.

Provides medical analysis functionality including:
- Symptom analysis and interpretation
- Diagnostic suggestions based on symptoms
- Treatment recommendations
- Health insights and analysis
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from src.auth.dependencies import get_authenticated_patient_id
from src.core.limiter import limiter
from src.core.config import settings
import openai

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/")
@limiter.limit("100/minute")
async def get_symptoms_info(
    request: Request,
    patient_id: str = Depends(get_authenticated_patient_id)
):
    """
    Get available symptoms analysis endpoints and information.
    
    Returns information about available symptoms analysis features:
    - Supported analysis types
    - Available endpoints
    - Usage guidelines
    """
    return {
        "message": "Symptoms Analysis API",
        "patient_id": patient_id,
        "available_endpoints": {
            "analyze": "POST /symptoms/analyze - Analyze symptoms using AI",
            "history": "GET /symptoms/history - Get patient symptom history", 
            "search": "GET /symptoms/search - Search symptom database"
        },
        "supported_features": [
            "AI-powered symptom analysis",
            "Severity assessment",
            "Condition suggestions",
            "Treatment recommendations",
            "Symptom tracking over time"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/analyze")
@limiter.limit("50/hour")
async def analyze_symptoms(
    request: Request,
    symptoms_data: Dict[str, Any],
    patient_id: str = Depends(get_authenticated_patient_id)
):
    """
    Analyze symptoms and provide medical insights.
    
    Analyzes reported symptoms using AI to provide:
    - Symptom interpretation
    - Possible conditions
    - Severity assessment
    - Recommended actions
    """
    try:
        symptoms = symptoms_data.get("symptoms", [])
        severity = symptoms_data.get("severity", "unknown")
        duration = symptoms_data.get("duration", "unknown")
        
        if not symptoms:
            raise HTTPException(
                status_code=400,
                detail="No symptoms provided for analysis"
            )
        
        # Initialize OpenAI client
        openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Build analysis prompt
        prompt = f"""
        Analyze the following symptoms:
        
        Symptoms: {', '.join(symptoms)}
        Severity: {severity}
        Duration: {duration}
        
        Provide a medical analysis including:
        1. Symptom interpretation
        2. Possible conditions (with likelihood)
        3. Severity assessment
        4. Recommended next steps
        5. When to seek medical attention
        
        Format as JSON with clear sections.
        """
        
        # Get AI analysis
        response = await openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL_COMPLEX,
            messages=[
                {"role": "system", "content": "You are a medical AI assistant providing symptom analysis. Always recommend consulting healthcare professionals for proper diagnosis."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.3
        )
        
        analysis_text = response.choices[0].message.content
        
        return {
            "analysis": analysis_text,
            "symptoms": symptoms,
            "severity": severity,
            "duration": duration,
            "patient_id": patient_id,
            "timestamp": datetime.utcnow().isoformat(),
            "disclaimer": "This analysis is for informational purposes only. Please consult a healthcare professional for proper medical diagnosis and treatment."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Symptom analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to analyze symptoms"
        )

@router.post("/diagnostic/suggestions")
@limiter.limit("30/hour")
async def get_diagnostic_suggestions(
    request: Request,
    diagnostic_data: Dict[str, Any],
    patient_id: str = Depends(get_authenticated_patient_id)
):
    """Get diagnostic suggestions based on symptoms and medical history"""
    try:
        symptoms = diagnostic_data.get("symptoms", [])
        medical_history = diagnostic_data.get("medical_history", [])
        
        if not symptoms:
            raise HTTPException(
                status_code=400,
                detail="No symptoms provided for diagnostic suggestions"
            )
        
        # Initialize OpenAI client
        openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Build diagnostic prompt
        prompt = f"""
        Based on the following information, provide diagnostic suggestions:
        
        Current Symptoms: {', '.join(symptoms)}
        Medical History: {', '.join(medical_history) if medical_history else 'None provided'}
        
        Provide:
        1. Most likely diagnoses (with confidence levels)
        2. Differential diagnoses to consider
        3. Recommended diagnostic tests
        4. Risk factors assessment
        5. Urgency level
        
        Format as structured JSON.
        """
        
        response = await openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL_COMPLEX,
            messages=[
                {"role": "system", "content": "You are a medical AI providing diagnostic suggestions. Always emphasize the need for professional medical evaluation."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1200,
            temperature=0.2
        )
        
        suggestions_text = response.choices[0].message.content
        
        return {
            "diagnostic_suggestions": suggestions_text,
            "symptoms": symptoms,
            "medical_history": medical_history,
            "patient_id": patient_id,
            "timestamp": datetime.utcnow().isoformat(),
            "warning": "These are suggestions only. Professional medical evaluation is required for accurate diagnosis."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Diagnostic suggestions failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate diagnostic suggestions"
        )

@router.post("/treatment/recommendations")
@limiter.limit("30/hour") 
async def get_treatment_recommendations(
    request: Request,
    treatment_data: Dict[str, Any],
    patient_id: str = Depends(get_authenticated_patient_id)
):
    """Get treatment recommendations based on diagnosis and patient data"""
    try:
        diagnosis = treatment_data.get("diagnosis", "")
        symptoms = treatment_data.get("symptoms", [])
        allergies = treatment_data.get("allergies", [])
        
        if not diagnosis and not symptoms:
            raise HTTPException(
                status_code=400,
                detail="Diagnosis or symptoms required for treatment recommendations"
            )
        
        # Initialize OpenAI client
        openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Build treatment prompt
        prompt = f"""
        Provide treatment recommendations for:
        
        Diagnosis: {diagnosis or 'Not specified'}
        Symptoms: {', '.join(symptoms) if symptoms else 'Not specified'}
        Allergies: {', '.join(allergies) if allergies else 'None reported'}
        
        Include:
        1. First-line treatment options
        2. Alternative treatments
        3. Lifestyle recommendations
        4. Monitoring requirements
        5. When to seek follow-up care
        6. Allergy considerations
        
        Format as structured JSON.
        """
        
        response = await openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL_COMPLEX,
            messages=[
                {"role": "system", "content": "You are a medical AI providing treatment recommendations. Always emphasize that these are general guidelines and proper medical supervision is required."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1200,
            temperature=0.2
        )
        
        recommendations_text = response.choices[0].message.content
        
        return {
            "treatment_recommendations": recommendations_text,
            "diagnosis": diagnosis,
            "symptoms": symptoms,
            "allergies": allergies,
            "patient_id": patient_id,
            "timestamp": datetime.utcnow().isoformat(),
            "important_note": "These recommendations are general guidelines. Treatment should always be supervised by qualified healthcare professionals."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Treatment recommendations failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate treatment recommendations"
        )

@router.get("/health/insights")
@limiter.limit("100/hour")
async def get_health_insights(
    request: Request,
    patient_id: str = Depends(get_authenticated_patient_id)
):
    """Get general health insights and recommendations"""
    try:
        # This would typically integrate with patient data from the database
        # For now, providing general health insights
        
        insights = {
            "general_health": {
                "status": "Good",
                "recommendations": [
                    "Maintain regular exercise routine",
                    "Follow a balanced diet",
                    "Get adequate sleep (7-9 hours)",
                    "Stay hydrated",
                    "Schedule regular health checkups"
                ]
            },
            "preventive_care": {
                "upcoming_screenings": [],
                "vaccination_status": "Unknown",
                "last_checkup": "Unknown"
            },
            "risk_factors": {
                "lifestyle": [],
                "genetic": [],
                "environmental": []
            },
            "patient_id": patient_id,
            "timestamp": datetime.utcnow().isoformat(),
            "note": "Insights are general recommendations. Consult healthcare providers for personalized medical advice."
        }
        
        return insights
        
    except Exception as e:
        logger.error(f"Health insights failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate health insights"
        )
