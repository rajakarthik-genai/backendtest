"""
3D Visualization endpoints
Handles digital twin visualization data and body part mapping
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, List, Optional
from datetime import datetime
import logging

from src.api.dependencies import get_current_user, get_db_clients, require_patient_access
from src.auth.dependencies import get_authenticated_patient_id, AuthenticatedPatientId
from src.models.health import VisualizationData
from src.core.config import settings
from src.core.limiter import limiter

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/3d-model")
@limiter.limit("1000/hour")
async def get_3d_visualization_data(
    request: Request,
    include_inactive: bool = False,
    patient_id: str = Depends(get_authenticated_patient_id),
    db_clients: dict = Depends(get_db_clients)
):
    """
    Get body part health data formatted for 3D visualization.
    Returns coordinates and severity for the digital twin model.
    """
    try:
        neo4j = db_clients["neo4j"]
        
        # Build query based on include_inactive flag
        if include_inactive:
            health_query = """
                MATCH (p:Patient {patient_id: $patient_id})-[:HAS_BODY_PART]->(bp:BodyPart)
                OPTIONAL MATCH (bp)<-[:AFFECTS]-(e:Entity)
                OPTIONAL MATCH (bp)<-[:AFFECTS]-(c:Condition)
                
                WITH bp,
                     avg(e.severity) as avg_severity,
                     collect(DISTINCT c.name) as conditions,
                     max(e.date) as last_updated,
                     count(DISTINCT e) as data_points
                
                RETURN bp.name as body_part,
                       COALESCE(avg_severity, 0) as severity,
                       conditions,
                       last_updated,
                       data_points
                ORDER BY bp.name
            """
        else:
            health_query = """
                MATCH (p:Patient {patient_id: $patient_id})-[:HAS_BODY_PART]->(bp:BodyPart)
                OPTIONAL MATCH (bp)<-[:AFFECTS]-(e:Entity)
                OPTIONAL MATCH (bp)<-[:AFFECTS]-(c:Condition {status: 'active'})
                
                WITH bp,
                     avg(e.severity) as avg_severity,
                     collect(DISTINCT c.name) as conditions,
                     max(e.date) as last_updated,
                     count(DISTINCT e) as data_points
                
                WHERE avg_severity IS NOT NULL OR size(conditions) > 0
                
                RETURN bp.name as body_part,
                       COALESCE(avg_severity, 0) as severity,
                       conditions,
                       last_updated,
                       data_points
                ORDER BY severity DESC
            """
        
        health_result = await neo4j.execute_query(health_query, {"patient_id": patient_id})
        
        # Map body parts to 3D coordinates and colors
        visualization_data = {}
        
        for record in health_result:
            body_part = record["body_part"]
            severity = record["severity"]
            conditions = record["conditions"] or []
            data_points = record["data_points"] or 0
            
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
        
        return {
            "patient_id": patient_id,
            "visualization_data": visualization_data,
            "total_body_parts": len(visualization_data),
            "affected_parts": len([v for v in visualization_data.values() if v.severity > 0]),
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get 3D visualization data: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/body-part-map")
@limiter.limit("1000/hour")
async def get_body_part_mapping(
    request: Request,
    patient_id: AuthenticatedPatientId,
    current_user: dict = Depends(get_current_user),
    db_clients: dict = Depends(get_db_clients),
    _: str = Depends(require_patient_access)
):
    """
    Get body part mapping with severity levels for 2D visualization
    """
    try:
        neo4j = db_clients["neo4j"]
        
        # Get body part health data
        mapping_query = """
            MATCH (p:Patient {patient_id: $patient_id})-[:HAS_BODY_PART]->(bp:BodyPart)
            OPTIONAL MATCH (bp)<-[:AFFECTS]-(e:Entity)
            OPTIONAL MATCH (bp)<-[:AFFECTS]-(c:Condition {status: 'active'})
            
            WITH bp,
                 avg(e.severity) as avg_severity,
                 count(DISTINCT c) as active_conditions,
                 max(e.date) as last_updated
            
            RETURN bp.name as body_part,
                   COALESCE(avg_severity, 0) as severity,
                   active_conditions,
                   last_updated
            ORDER BY severity DESC
        """
        
        mapping_result = await neo4j.execute_query(mapping_query, {"patient_id": patient_id})
        
        # Create body part mapping
        body_part_map = {}
        
        for record in mapping_result:
            body_part = record["body_part"]
            severity = record["severity"]
            active_conditions = record["active_conditions"] or 0
            
            # Get severity level and color
            severity_level = _get_severity_level(severity)
            color = _get_severity_color(severity)
            
            body_part_map[body_part] = {
                "severity": severity,
                "severity_level": severity_level,
                "color": color,
                "active_conditions": active_conditions,
                "label": body_part.replace("_", " ").title(),
                "category": _get_body_part_category(body_part)
            }
        
        # Group by categories
        categories = {}
        for body_part, data in body_part_map.items():
            category = data["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append({
                "name": body_part,
                **data
            })
        
        return {
            "patient_id": patient_id,
            "body_part_map": body_part_map,
            "categories": categories,
            "summary": {
                "total_parts": len(body_part_map),
                "affected_parts": len([p for p in body_part_map.values() if p["severity"] > 0]),
                "critical_parts": len([p for p in body_part_map.values() if p["severity"] >= 8]),
                "severe_parts": len([p for p in body_part_map.values() if 6 <= p["severity"] < 8])
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get body part mapping: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/severity-heatmap")
@limiter.limit("1000/hour")
async def get_severity_heatmap(
    request: Request,
    patient_id: AuthenticatedPatientId,
    time_range: Optional[str] = "all_time",
    current_user: dict = Depends(get_current_user),
    db_clients: dict = Depends(get_db_clients),
    _: str = Depends(require_patient_access)
):
    """
    Get severity heatmap data for temporal visualization
    """
    try:
        neo4j = db_clients["neo4j"]
        
        # Build time filter
        time_filter = ""
        if time_range == "last_week":
            time_filter = "AND ev.date >= date() - duration('P7D')"
        elif time_range == "last_month":
            time_filter = "AND ev.date >= date() - duration('P1M')"
        elif time_range == "last_year":
            time_filter = "AND ev.date >= date() - duration('P1Y')"
        
        # Get severity data over time
        heatmap_query = f"""
            MATCH (p:Patient {{patient_id: $patient_id}})-[:HAS_EVENT]->(ev:Event)
            OPTIONAL MATCH (ev)-[:AFFECTS]->(bp:BodyPart)
            WHERE ev.severity IS NOT NULL {time_filter}
            
            WITH date(ev.date) as event_date,
                 bp.name as body_part,
                 avg(ev.severity) as avg_severity
            
            RETURN event_date,
                   body_part,
                   avg_severity
            ORDER BY event_date DESC, avg_severity DESC
        """
        
        heatmap_result = await neo4j.execute_query(heatmap_query, {"patient_id": patient_id})
        
        # Process heatmap data
        heatmap_data = {}
        date_range = set()
        body_parts = set()
        
        for record in heatmap_result:
            event_date = str(record["event_date"])
            body_part = record["body_part"]
            severity = record["avg_severity"]
            
            if event_date not in heatmap_data:
                heatmap_data[event_date] = {}
            
            heatmap_data[event_date][body_part] = severity
            date_range.add(event_date)
            body_parts.add(body_part)
        
        # Fill missing data points with 0
        for date in date_range:
            for body_part in body_parts:
                if body_part not in heatmap_data[date]:
                    heatmap_data[date][body_part] = 0
        
        return {
            "patient_id": patient_id,
            "time_range": time_range,
            "heatmap_data": heatmap_data,
            "date_range": sorted(list(date_range)),
            "body_parts": sorted(list(body_parts)),
            "summary": {
                "total_dates": len(date_range),
                "total_body_parts": len(body_parts),
                "max_severity": max([max(day_data.values()) for day_data in heatmap_data.values()]) if heatmap_data else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get severity heatmap: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trends")
@limiter.limit("1000/hour")
async def get_health_trends(
    request: Request,
    patient_id: AuthenticatedPatientId,
    body_parts: Optional[List[str]] = None,
    days: int = 30,
    current_user: dict = Depends(get_current_user),
    db_clients: dict = Depends(get_db_clients),
    _: str = Depends(require_patient_access)
):
    """
    Get health trends over time for specific body parts
    """
    try:
        neo4j = db_clients["neo4j"]
        
        # Build body parts filter
        body_parts_filter = ""
        query_params = {"patient_id": patient_id, "days": days}
        
        if body_parts:
            body_parts_filter = "AND bp.name IN $body_parts"
            query_params["body_parts"] = body_parts
        
        # Get trend data
        trends_query = f"""
            MATCH (p:Patient {{patient_id: $patient_id}})-[:HAS_EVENT]->(ev:Event)
            OPTIONAL MATCH (ev)-[:AFFECTS]->(bp:BodyPart)
            WHERE ev.severity IS NOT NULL 
            AND ev.date >= date() - duration({{days: $days}})
            {body_parts_filter}
            
            WITH date(ev.date) as event_date,
                 bp.name as body_part,
                 avg(ev.severity) as avg_severity,
                 count(ev) as event_count
            
            RETURN event_date,
                   body_part,
                   avg_severity,
                   event_count
            ORDER BY event_date ASC
        """
        
        trends_result = await neo4j.execute_query(trends_query, query_params)
        
        # Process trends data
        trends_data = {}
        
        for record in trends_result:
            body_part = record["body_part"]
            event_date = str(record["event_date"])
            severity = record["avg_severity"]
            
            if body_part not in trends_data:
                trends_data[body_part] = {
                    "dates": [],
                    "severities": [],
                    "trend": "stable"
                }
            
            trends_data[body_part]["dates"].append(event_date)
            trends_data[body_part]["severities"].append(severity)
        
        # Calculate trends
        for body_part, data in trends_data.items():
            if len(data["severities"]) >= 2:
                # Simple trend calculation
                first_half = data["severities"][:len(data["severities"])//2]
                second_half = data["severities"][len(data["severities"])//2:]
                
                avg_first = sum(first_half) / len(first_half)
                avg_second = sum(second_half) / len(second_half)
                
                if avg_second > avg_first + 0.5:
                    data["trend"] = "worsening"
                elif avg_second < avg_first - 0.5:
                    data["trend"] = "improving"
                else:
                    data["trend"] = "stable"
        
        return {
            "patient_id": patient_id,
            "time_period_days": days,
            "trends_data": trends_data,
            "summary": {
                "body_parts_tracked": len(trends_data),
                "improving_trends": len([t for t in trends_data.values() if t["trend"] == "improving"]),
                "worsening_trends": len([t for t in trends_data.values() if t["trend"] == "worsening"]),
                "stable_trends": len([t for t in trends_data.values() if t["trend"] == "stable"])
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get health trends: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions

def _get_body_part_position(body_part: str) -> Dict[str, float]:
    """Get 3D position for body part (comprehensive mapping)"""
    positions = {
        # Head and Neck
        "brain": {"x": 0, "y": 1.7, "z": 0},
        "eyes": {"x": 0, "y": 1.65, "z": 0.1},
        "ears": {"x": 0.15, "y": 1.65, "z": 0},
        "nose": {"x": 0, "y": 1.6, "z": 0.1},
        "throat": {"x": 0, "y": 1.5, "z": 0},
        "neck": {"x": 0, "y": 1.45, "z": 0},
        "face": {"x": 0, "y": 1.6, "z": 0.05},
        "skull": {"x": 0, "y": 1.7, "z": -0.05},
        
        # Torso - Upper
        "shoulder_left": {"x": -0.3, "y": 1.4, "z": 0},
        "shoulder_right": {"x": 0.3, "y": 1.4, "z": 0},
        "chest": {"x": 0, "y": 1.2, "z": 0.1},
        "heart": {"x": -0.05, "y": 1.2, "z": 0},
        "lungs": {"x": 0, "y": 1.2, "z": 0},
        "thyroid": {"x": 0, "y": 1.45, "z": 0.05},
        
        # Torso - Mid
        "liver": {"x": 0.1, "y": 0.9, "z": 0},
        "stomach": {"x": -0.05, "y": 0.9, "z": 0},
        "pancreas": {"x": 0, "y": 0.85, "z": -0.05},
        "spleen": {"x": -0.15, "y": 0.9, "z": 0},
        "gallbladder": {"x": 0.1, "y": 0.85, "z": 0},
        
        # Torso - Lower
        "kidneys": {"x": 0, "y": 0.8, "z": -0.1},
        "bladder": {"x": 0, "y": 0.6, "z": 0},
        "intestines_small": {"x": 0, "y": 0.7, "z": 0},
        "intestines_large": {"x": 0, "y": 0.65, "z": 0},
        "appendix": {"x": 0.1, "y": 0.65, "z": 0},
        "reproductive_system": {"x": 0, "y": 0.55, "z": 0},
        
        # Musculoskeletal
        "spine": {"x": 0, "y": 1.0, "z": -0.15},
        "ribs": {"x": 0, "y": 1.1, "z": -0.1},
        "pelvis": {"x": 0, "y": 0.6, "z": -0.1},
        "hip_left": {"x": -0.15, "y": 0.6, "z": 0},
        "hip_right": {"x": 0.15, "y": 0.6, "z": 0},
        
        # Extremities
        "arm_left": {"x": -0.5, "y": 1.0, "z": 0},
        "arm_right": {"x": 0.5, "y": 1.0, "z": 0},
        "leg_left": {"x": -0.15, "y": 0.3, "z": 0},
        "leg_right": {"x": 0.15, "y": 0.3, "z": 0},
        "hand_left": {"x": -0.7, "y": 0.8, "z": 0},
        "hand_right": {"x": 0.7, "y": 0.8, "z": 0},
        "foot_left": {"x": -0.15, "y": 0, "z": 0},
        "foot_right": {"x": 0.15, "y": 0, "z": 0},
        
        # Systems
        "blood": {"x": 0, "y": 1.0, "z": 0},
        "immune_system": {"x": 0, "y": 1.0, "z": 0},
        "nervous_system": {"x": 0, "y": 1.3, "z": 0},
        "lymphatic_system": {"x": 0, "y": 1.0, "z": 0},
        "skin": {"x": 0, "y": 1.0, "z": 0.2}
    }
    
    return positions.get(body_part, {"x": 0, "y": 1, "z": 0})

def _get_severity_color(severity: float) -> str:
    """Get color based on severity level"""
    if severity >= 8:
        return "#8B0000"  # Critical - Dark Red
    elif severity >= 6:
        return "#FF4444"  # Severe - Red
    elif severity >= 4:
        return "#FFA500"  # Moderate - Orange
    elif severity >= 2:
        return "#FFFF00"  # Mild - Yellow
    elif severity > 0:
        return "#00FF00"  # Normal - Green
    else:
        return "#808080"  # Unknown - Grey

def _get_severity_level(severity: float) -> str:
    """Convert numeric severity to severity level"""
    if severity >= 8:
        return "critical"
    elif severity >= 6:
        return "severe"
    elif severity >= 4:
        return "moderate"
    elif severity >= 2:
        return "mild"
    elif severity > 0:
        return "normal"
    else:
        return "unknown"

def _get_body_part_category(body_part: str) -> str:
    """Get category for body part grouping"""
    categories = {
        # Head and Neck
        "brain": "neurological",
        "eyes": "sensory",
        "ears": "sensory",
        "nose": "respiratory",
        "throat": "respiratory",
        "neck": "musculoskeletal",
        "face": "external",
        "skull": "musculoskeletal",
        
        # Cardiovascular
        "heart": "cardiovascular",
        "blood": "cardiovascular",
        
        # Respiratory
        "lungs": "respiratory",
        "chest": "respiratory",
        
        # Digestive
        "liver": "digestive",
        "stomach": "digestive",
        "pancreas": "digestive",
        "spleen": "digestive",
        "gallbladder": "digestive",
        "intestines_small": "digestive",
        "intestines_large": "digestive",
        "appendix": "digestive",
        
        # Urinary
        "kidneys": "urinary",
        "bladder": "urinary",
        
        # Reproductive
        "reproductive_system": "reproductive",
        
        # Musculoskeletal
        "spine": "musculoskeletal",
        "ribs": "musculoskeletal",
        "pelvis": "musculoskeletal",
        "hip_left": "musculoskeletal",
        "hip_right": "musculoskeletal",
        "shoulder_left": "musculoskeletal",
        "shoulder_right": "musculoskeletal",
        
        # Extremities
        "arm_left": "extremities",
        "arm_right": "extremities",
        "leg_left": "extremities",
        "leg_right": "extremities",
        "hand_left": "extremities",
        "hand_right": "extremities",
        "foot_left": "extremities",
        "foot_right": "extremities",
        
        # Systems
        "immune_system": "immune",
        "nervous_system": "neurological",
        "lymphatic_system": "immune",
        "skin": "external",
        "thyroid": "endocrine"
    }
    
    return categories.get(body_part, "other")
