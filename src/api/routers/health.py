"""
Health status endpoints
Handles body parts health status, severity levels, and health summaries
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, List, Optional
from datetime import datetime
import logging

from src.api.dependencies import get_current_user, get_db_clients, require_patient_access
from src.auth.dependencies import get_authenticated_patient_id, AuthenticatedPatientId
from src.models.health import BodyPartHealth, SeverityLevel, HealthSummary, VisualizationData
from src.core.config import settings
from src.core.limiter import limiter

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/body-parts", response_model=Dict[str, BodyPartHealth])
@limiter.limit("1000/hour")
async def get_all_body_parts_health(
    request: Request,
    patient_id: AuthenticatedPatientId,
    include_empty: bool = True,
    current_user: dict = Depends(get_current_user),
    db_clients: dict = Depends(get_db_clients),
    _: str = Depends(require_patient_access)
):
    """
    Get health status for all body parts, including severity levels
    for the digital twin visualization.
    """
    try:
        body_parts_health = {}
        
        # Get body part health data from Neo4j
        neo4j = db_clients["neo4j"]
        
        # Query for body parts with health data
        health_result = await neo4j.execute_query("""
            MATCH (p:Patient {patient_id: $patient_id})-[:HAS_BODY_PART]->(bp:BodyPart)
            OPTIONAL MATCH (bp)<-[:AFFECTS]-(e:Entity)
            OPTIONAL MATCH (bp)<-[:AFFECTS]-(c:Condition)
            OPTIONAL MATCH (bp)<-[:TARGETS]-(t:Treatment)
            
            WITH bp, 
                 collect(DISTINCT e.text) as entities,
                 collect(DISTINCT c.name) as conditions,
                 collect(DISTINCT t.name) as treatments,
                 avg(e.severity) as avg_severity,
                 max(e.date) as last_updated,
                 count(DISTINCT e) as data_points
            
            RETURN bp.name as body_part,
                   avg_severity,
                   last_updated,
                   data_points,
                   conditions,
                   treatments
            ORDER BY bp.name
        """, {"patient_id": patient_id})
        
        # Process results
        for record in health_result:
            body_part = record["body_part"]
            severity = record["avg_severity"] or 0
            
            # Determine severity level
            severity_level = _get_severity_level(severity)
            
            # Parse last updated
            last_updated = None
            if record["last_updated"]:
                try:
                    if isinstance(record["last_updated"], str):
                        last_updated = datetime.fromisoformat(record["last_updated"])
                    else:
                        last_updated = record["last_updated"]
                except:
                    pass
            
            body_parts_health[body_part] = BodyPartHealth(
                body_part=body_part,
                severity=severity if severity > 0 else None,
                severity_level=severity_level,
                last_updated=last_updated,
                data_points=record["data_points"] or 0,
                conditions=record["conditions"] or [],
                treatments=record["treatments"] or []
            )
        
        # Add empty body parts if requested
        if include_empty:
            for body_part in settings.BODY_PARTS:
                if body_part not in body_parts_health:
                    body_parts_health[body_part] = BodyPartHealth(
                        body_part=body_part,
                        severity=None,
                        severity_level=SeverityLevel.UNKNOWN,
                        last_updated=None,
                        data_points=0,
                        conditions=[],
                        treatments=[]
                    )
        
        return body_parts_health
        
    except Exception as e:
        logger.error(f"Failed to get body parts health: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary", response_model=HealthSummary)
@limiter.limit("1000/hour")
async def get_patient_health_summary(
    request: Request,
    patient_id: str = Depends(get_authenticated_patient_id),
    db_clients: dict = Depends(get_db_clients)
):
    """
    Get summary data for the digital twin dashboard.
    """
    try:
        # Get summary statistics from various sources
        mongodb = db_clients["mongodb"]
        neo4j = db_clients["neo4j"]
        
        # Get document count
        recent_documents = await mongodb.documents.count_documents({
            "patient_id": patient_id,
            "status": "completed"
        })
        
        # Get health statistics from Neo4j
        stats_result = await neo4j.execute_query("""
            MATCH (p:Patient {patient_id: $patient_id})
            OPTIONAL MATCH (p)-[:HAS_CONDITION]->(c:Condition {status: 'active'})
            OPTIONAL MATCH (p)-[:HAS_MEDICATION]->(m:Medication {status: 'active'})
            OPTIONAL MATCH (p)-[:HAS_BODY_PART]->(bp:BodyPart)<-[:AFFECTS]-(e:Entity)
            OPTIONAL MATCH (p)-[:HAS_EVENT]->(ev:Event)
            
            WITH p,
                 count(DISTINCT c) as active_conditions,
                 count(DISTINCT m) as medications_count,
                 count(DISTINCT bp) as body_parts_affected,
                 count(DISTINCT ev) as timeline_events_count,
                 avg(e.severity) as overall_health_score
            
            RETURN active_conditions,
                   medications_count,
                   body_parts_affected,
                   timeline_events_count,
                   COALESCE(overall_health_score, 8.0) as overall_health_score
        """, {"patient_id": patient_id})
        
        # Default values
        stats = {
            "active_conditions": 0,
            "medications_count": 0,
            "body_parts_affected": 0,
            "timeline_events_count": 0,
            "overall_health_score": 8.0
        }
        
        if stats_result:
            record = stats_result[0]
            stats.update({
                "active_conditions": record["active_conditions"] or 0,
                "medications_count": record["medications_count"] or 0,
                "body_parts_affected": record["body_parts_affected"] or 0,
                "timeline_events_count": record["timeline_events_count"] or 0,
                "overall_health_score": 10 - (record["overall_health_score"] or 2.0)  # Invert severity to health score
            })
        
        # Get critical alerts
        critical_alerts = []
        alerts_result = await neo4j.execute_query("""
            MATCH (p:Patient {patient_id: $patient_id})-[:HAS_CONDITION]->(c:Condition)
            WHERE c.severity >= 8 AND c.status = 'active'
            RETURN c.name as condition, c.severity as severity
            ORDER BY c.severity DESC
            LIMIT 5
        """, {"patient_id": patient_id})
        
        for record in alerts_result:
            critical_alerts.append(f"Critical: {record['condition']} (Severity: {record['severity']}/10)")
        
        return HealthSummary(
            patient_id=patient_id,
            last_updated=datetime.utcnow(),
            overall_health_score=min(10, max(0, stats["overall_health_score"])),
            active_conditions=stats["active_conditions"],
            upcoming_appointments=0,  # Would come from appointment system
            medications_count=stats["medications_count"],
            recent_documents=recent_documents,
            critical_alerts=critical_alerts,
            body_parts_affected=stats["body_parts_affected"],
            timeline_events_count=stats["timeline_events_count"]
        )
        
    except Exception as e:
        logger.error(f"Failed to get health summary: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/3d-visualization")
@limiter.limit("1000/hour")
async def get_3d_visualization_data(
    request: Request,
    patient_id: str = Depends(get_authenticated_patient_id),
    db_clients: dict = Depends(get_db_clients)
):
    """
    Get body part health data formatted for 3D visualization.
    Returns coordinates and severity for the digital twin model.
    """
    try:
        # Get body part health data
        neo4j = db_clients["neo4j"]
        
        health_result = await neo4j.execute_query("""
            MATCH (p:Patient {patient_id: $patient_id})-[:HAS_BODY_PART]->(bp:BodyPart)
            OPTIONAL MATCH (bp)<-[:AFFECTS]-(e:Entity)
            OPTIONAL MATCH (bp)<-[:AFFECTS]-(c:Condition {status: 'active'})
            
            WITH bp,
                 avg(e.severity) as avg_severity,
                 collect(DISTINCT c.name) as conditions,
                 max(e.date) as last_updated
            
            WHERE avg_severity IS NOT NULL OR size(conditions) > 0
            
            RETURN bp.name as body_part,
                   COALESCE(avg_severity, 0) as severity,
                   conditions,
                   last_updated
        """, {"patient_id": patient_id})
        
        # Map body parts to 3D coordinates and colors
        visualization_data = {}
        
        for record in health_result:
            body_part = record["body_part"]
            severity = record["severity"]
            conditions = record["conditions"] or []
            
            # Get 3D position for body part
            position = _get_body_part_position(body_part)
            
            # Get color based on severity
            color = _get_severity_color(severity)
            
            # Parse last updated
            last_updated = None
            if record["last_updated"]:
                try:
                    if isinstance(record["last_updated"], str):
                        last_updated = datetime.fromisoformat(record["last_updated"])
                    else:
                        last_updated = record["last_updated"]
                except:
                    pass
            
            visualization_data[body_part] = VisualizationData(
                position=position,
                severity=severity,
                color=color,
                label=body_part.replace("_", " ").title(),
                conditions=conditions,
                last_updated=last_updated
            )
        
        return visualization_data
        
    except Exception as e:
        logger.error(f"Failed to get 3D visualization data: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/body-part/{body_part}")
@limiter.limit("1000/hour")
async def get_body_part_details(
    request: Request,
    body_part: str,
    patient_id: str = Depends(get_authenticated_patient_id),
    db_clients: dict = Depends(get_db_clients)
):
    """
    Get detailed information for a specific body part
    """
    try:
        if body_part not in settings.BODY_PARTS:
            raise HTTPException(status_code=400, detail="Invalid body part")
        
        neo4j = db_clients["neo4j"]
        
        # Get detailed body part information
        detail_result = await neo4j.execute_query("""
            MATCH (p:Patient {patient_id: $patient_id})-[:HAS_BODY_PART]->(bp:BodyPart {name: $body_part})
            OPTIONAL MATCH (bp)<-[:AFFECTS]-(e:Entity)
            OPTIONAL MATCH (bp)<-[:AFFECTS]-(c:Condition)
            OPTIONAL MATCH (bp)<-[:TARGETS]-(t:Treatment)
            OPTIONAL MATCH (bp)<-[:AFFECTS]-(ev:Event)
            
            RETURN bp,
                   collect(DISTINCT {
                       type: e.type,
                       text: e.text,
                       severity: e.severity,
                       date: e.date,
                       confidence: e.confidence
                   }) as entities,
                   collect(DISTINCT {
                       name: c.name,
                       severity: c.severity,
                       status: c.status,
                       diagnosed_date: c.diagnosed_date
                   }) as conditions,
                   collect(DISTINCT {
                       name: t.name,
                       type: t.type,
                       start_date: t.start_date,
                       status: t.status
                   }) as treatments,
                   collect(DISTINCT {
                       date: ev.date,
                       type: ev.event_type,
                       description: ev.description
                   }) as events
        """, {"patient_id": patient_id, "body_part": body_part})
        
        if not detail_result:
            return {
                "body_part": body_part,
                "severity": 0,
                "severity_level": SeverityLevel.UNKNOWN,
                "entities": [],
                "conditions": [],
                "treatments": [],
                "events": []
            }
        
        record = detail_result[0]
        
        # Calculate overall severity
        entities = [e for e in record["entities"] if e["severity"] is not None]
        avg_severity = sum(e["severity"] for e in entities) / len(entities) if entities else 0
        
        return {
            "body_part": body_part,
            "severity": avg_severity,
            "severity_level": _get_severity_level(avg_severity),
            "entities": record["entities"],
            "conditions": record["conditions"],
            "treatments": record["treatments"],
            "events": record["events"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get body part details: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions

def _get_severity_level(severity: float) -> SeverityLevel:
    """Convert numeric severity to severity level"""
    if severity >= 8:
        return SeverityLevel.CRITICAL
    elif severity >= 6:
        return SeverityLevel.SEVERE
    elif severity >= 4:
        return SeverityLevel.MODERATE
    elif severity >= 2:
        return SeverityLevel.MILD
    elif severity > 0:
        return SeverityLevel.NORMAL
    else:
        return SeverityLevel.UNKNOWN

def _get_severity_color(severity: float) -> str:
    """Get color based on severity level"""
    severity_level = _get_severity_level(severity)
    return settings.SEVERITY_LEVELS[severity_level.value]["color"]

def _get_body_part_position(body_part: str) -> Dict[str, float]:
    """Get 3D position for body part (simplified mapping)"""
    # This would be a comprehensive mapping to 3D coordinates
    # For now, providing basic positioning
    positions = {
        # Head and Neck
        "brain": {"x": 0, "y": 1.7, "z": 0},
        "eyes": {"x": 0, "y": 1.65, "z": 0.1},
        "ears": {"x": 0.15, "y": 1.65, "z": 0},
        "nose": {"x": 0, "y": 1.6, "z": 0.1},
        "throat": {"x": 0, "y": 1.5, "z": 0},
        "neck": {"x": 0, "y": 1.45, "z": 0},
        
        # Torso - Upper
        "shoulder_left": {"x": -0.3, "y": 1.4, "z": 0},
        "shoulder_right": {"x": 0.3, "y": 1.4, "z": 0},
        "chest": {"x": 0, "y": 1.2, "z": 0.1},
        "heart": {"x": -0.05, "y": 1.2, "z": 0},
        "lungs": {"x": 0, "y": 1.2, "z": 0},
        
        # Torso - Mid
        "liver": {"x": 0.1, "y": 0.9, "z": 0},
        "stomach": {"x": -0.05, "y": 0.9, "z": 0},
        "pancreas": {"x": 0, "y": 0.85, "z": -0.05},
        "spleen": {"x": -0.15, "y": 0.9, "z": 0},
        
        # Torso - Lower
        "kidneys": {"x": 0, "y": 0.8, "z": -0.1},
        "bladder": {"x": 0, "y": 0.6, "z": 0},
        "intestines_small": {"x": 0, "y": 0.7, "z": 0},
        "intestines_large": {"x": 0, "y": 0.65, "z": 0},
        
        # Extremities
        "arm_left": {"x": -0.5, "y": 1.0, "z": 0},
        "arm_right": {"x": 0.5, "y": 1.0, "z": 0},
        "leg_left": {"x": -0.15, "y": 0.3, "z": 0},
        "leg_right": {"x": 0.15, "y": 0.3, "z": 0},
        "hand_left": {"x": -0.7, "y": 0.8, "z": 0},
        "hand_right": {"x": 0.7, "y": 0.8, "z": 0},
        "foot_left": {"x": -0.15, "y": 0, "z": 0},
        "foot_right": {"x": 0.15, "y": 0, "z": 0},
    }
    
    return positions.get(body_part, {"x": 0, "y": 1, "z": 0})
