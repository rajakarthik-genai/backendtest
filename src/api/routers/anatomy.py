"""
Anatomy API endpoints for body part analysis and severity tracking.

Provides anatomical analysis functionality including:
- Body part severity levels
- Anatomical region details
- Medical condition mapping to body parts
- Severity tracking over time
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from src.auth.dependencies import get_authenticated_patient_id
from src.core.limiter import limiter
from src.api.dependencies import get_db_clients
from src.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/body-parts/severities")
@limiter.limit("100/hour")
async def get_body_parts_severities(
    request: Request,
    patient_id: str = Depends(get_authenticated_patient_id),  # Fixed: use patient_id instead of user_id
    db_clients: dict = Depends(get_db_clients)
):
    """
    Get severity levels for all body parts for the authenticated patient.
    
    Returns severity analysis including:
    - Individual body part severity scores
    - Overall health trends
    - Critical areas requiring attention
    - Historical severity changes
    """
    try:
        if not db_clients.get("neo4j"):
            raise HTTPException(
                status_code=503,
                detail="Neo4j not available"
            )
            
        neo4j = db_clients["neo4j"]
        
        # Query body part severities using patient_id (not user_id)
        severity_query = """
            MATCH (p:Patient {patient_id: $patient_id})-[:HAS_BODY_PART]->(bp:BodyPart)
            OPTIONAL MATCH (bp)<-[:AFFECTS]-(e:Event)
            WHERE e.severity IS NOT NULL
            
            RETURN bp.name as body_part,
                   avg(e.severity) as avg_severity,
                   max(e.severity) as max_severity,
                   min(e.severity) as min_severity,
                   count(e) as event_count
            ORDER BY avg_severity DESC
        """
        
        results = neo4j.execute_query(severity_query, {"patient_id": patient_id})
        
        severities = {}
        for record in results:
            body_part = record["body_part"]
            severities[body_part] = {
                "average_severity": float(record["avg_severity"] or 0),
                "max_severity": float(record["max_severity"] or 0),
                "min_severity": float(record["min_severity"] or 0),
                "event_count": record["event_count"],
                "risk_level": _calculate_risk_level(record["avg_severity"] or 0)
            }
        
        return {
            "patient_id": patient_id,  # Use patient_id consistently
            "body_part_severities": severities,
            "total_body_parts": len(severities),
            "high_risk_parts": [bp for bp, data in severities.items() if data["risk_level"] == "high"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get body part severities: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve body part severity data"
        )

@router.get("/body-part/{body_part}/details")
@limiter.limit("100/hour") 
async def get_body_part_details(
    request: Request,
    body_part: str,
    patient_id: str = Depends(get_authenticated_patient_id),  # Fixed: use patient_id instead of user_id
    db_clients: dict = Depends(get_db_clients)
):
    """
    Get detailed analysis for a specific body part for the authenticated patient.
    
    Provides comprehensive body part information including:
    - Current health status
    - Associated conditions and symptoms
    - Treatment history
    - Severity trends over time
    - Recommendations
    """
    try:
        if not db_clients.get("neo4j"):
            raise HTTPException(
                status_code=503,
                detail="Neo4j not available"
            )
            
        neo4j = db_clients["neo4j"]
        
        # Query detailed body part information using patient_id (not user_id)
        detail_query = """
            MATCH (p:Patient {patient_id: $patient_id})-[:HAS_BODY_PART]->(bp:BodyPart {name: $body_part})
            OPTIONAL MATCH (bp)<-[:AFFECTS]-(c:Condition)
            OPTIONAL MATCH (bp)<-[:TARGETS]-(t:Treatment)
            OPTIONAL MATCH (bp)<-[:AFFECTS]-(e:Event)
            
            RETURN bp,
                   collect(DISTINCT {
                       name: c.name,
                       severity: c.severity,
                       status: c.status
                   }) as conditions,
                   collect(DISTINCT {
                       name: t.name,
                       type: t.type,
                       effectiveness: t.effectiveness
                   }) as treatments,
                   collect(DISTINCT {
                       event_id: e.event_id,
                       date: e.date,
                       type: e.event_type,
                       severity: e.severity,
                       description: e.description
                   }) as events
        """
        
        results = neo4j.execute_query(
            detail_query, 
            {"patient_id": patient_id, "body_part": body_part}  # Use patient_id consistently
        )
        
        if not results:
            raise HTTPException(
                status_code=404,
                detail=f"Body part '{body_part}' not found for patient"
            )
            
        record = results[0]
        
        # Calculate health metrics
        events = record["events"]
        avg_severity = sum(float(e.get("severity", 0)) for e in events) / len(events) if events else 0
        recent_events = sorted(events, key=lambda x: x.get("date", ""), reverse=True)[:5]
        
        return {
            "patient_id": patient_id,  # Use patient_id consistently
            "body_part": body_part,
            "health_status": {
                "average_severity": avg_severity,
                "risk_level": _calculate_risk_level(avg_severity),
                "total_events": len(events),
                "active_conditions": len([c for c in record["conditions"] if c.get("status") == "active"])
            },
            "conditions": record["conditions"],
            "treatments": record["treatments"],
            "recent_events": recent_events,
            "recommendations": _generate_body_part_recommendations(body_part, avg_severity),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get body part details: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve body part details"
        )

@router.get("/severity-trends/{body_part}")
@limiter.limit("50/hour")
async def get_severity_trends(
    request: Request,
    body_part: str,
    patient_id: str = Depends(get_authenticated_patient_id),
    db_clients: dict = Depends(get_db_clients),
    days: int = 30
):
    """Get severity trends over time for a specific body part"""
    try:
        if not db_clients.get("neo4j"):
            raise HTTPException(
                status_code=503,
                detail="Neo4j not available"
            )
            
        neo4j = db_clients["neo4j"]
        
        # Query severity trends
        trends_query = """
            MATCH (p:Patient {patient_id: $patient_id})-[:HAS_BODY_PART]->(bp:BodyPart {name: $body_part})
            MATCH (bp)<-[:AFFECTS]-(e:Event)
            WHERE e.date >= date() - duration({days: $days})
            AND e.severity IS NOT NULL
            
            RETURN e.date as date,
                   e.severity as severity,
                   e.event_type as event_type
            ORDER BY e.date ASC
        """
        
        results = neo4j.execute_query(
            trends_query,
            {"patient_id": patient_id, "body_part": body_part, "days": days}
        )
        
        trends = []
        for record in results:
            trends.append({
                "date": record["date"],
                "severity": float(record["severity"]),
                "event_type": record["event_type"]
            })
            
        # Calculate trend statistics
        severities = [t["severity"] for t in trends]
        avg_severity = sum(severities) / len(severities) if severities else 0
        trend_direction = "stable"
        
        if len(severities) >= 2:
            if severities[-1] > severities[0]:
                trend_direction = "increasing"
            elif severities[-1] < severities[0]:
                trend_direction = "decreasing"
        
        return {
            "patient_id": patient_id,
            "body_part": body_part,
            "period_days": days,
            "trend_data": trends,
            "statistics": {
                "average_severity": avg_severity,
                "trend_direction": trend_direction,
                "total_events": len(trends),
                "max_severity": max(severities) if severities else 0,
                "min_severity": min(severities) if severities else 0
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get severity trends: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve severity trends"
        )

def _calculate_risk_level(severity: float) -> str:
    """Calculate risk level based on severity score"""
    if severity >= 8:
        return "critical"
    elif severity >= 6:
        return "high"
    elif severity >= 4:
        return "moderate"
    elif severity >= 2:
        return "low"
    else:
        return "minimal"

def _generate_body_part_recommendations(body_part: str, severity: float) -> List[str]:
    """Generate recommendations based on body part and severity"""
    recommendations = []
    
    if severity >= 6:
        recommendations.extend([
            "Consider immediate medical consultation",
            "Monitor symptoms closely",
            "Follow prescribed treatment plan"
        ])
    elif severity >= 4:
        recommendations.extend([
            "Schedule follow-up appointment",
            "Monitor for changes",
            "Continue current treatment"
        ])
    else:
        recommendations.extend([
            "Maintain preventive care",
            "Regular health monitoring",
            "Healthy lifestyle practices"
        ])
    
    # Body part specific recommendations
    if body_part.lower() in ["heart", "chest"]:
        recommendations.append("Monitor cardiovascular health")
    elif body_part.lower() in ["brain", "head"]:
        recommendations.append("Ensure adequate rest and stress management")
    elif body_part.lower() in ["joints", "knee", "shoulder"]:
        recommendations.append("Consider physical therapy exercises")
        
    return recommendations
