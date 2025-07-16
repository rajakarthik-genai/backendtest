"""
/anatomy – body-part–centric queries via Neo4j.
Enhanced with severity tracking and 30-body-part initialization.
"""

from fastapi import APIRouter, Path, HTTPException, Query
from typing import Dict, List, Any
from src.db.neo4j_db import get_graph
from src.auth.dependencies import CurrentUser
from src.auth.models import User
from src.utils.logging import logger
from src.config.body_parts import get_default_body_parts, get_severity_levels, validate_body_part

router = APIRouter(tags=["anatomy"])


@router.get("/body-parts")
async def get_body_parts_severities(current_user: CurrentUser):
    """
    Get severity status for all 30 body parts for 3D visualization.
    
    Returns:
        JSON with body parts and their severity levels (NA, normal, mild, moderate, severe, critical)
    """
    try:
        patient_id = current_user.patient_id
        neo4j_client = get_graph()
        
        # Ensure user is initialized
        neo4j_client.ensure_user_initialized(patient_id)
        
        # Get severities for all body parts
        severities = neo4j_client.get_body_part_severities(user_id)
        
        # Format response for frontend
        body_parts_data = []
        for body_part, severity in severities.items():
            body_parts_data.append({
                "name": body_part,
                "severity": severity
            })
        
        return {
            "patient_id": patient_id,
            "body_parts": body_parts_data,
            "total_parts": len(body_parts_data)
        }
        
    except Exception as e:
        logger.error(f"Failed to get body parts severities: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve body parts data")


@router.get("/body-part/{body_part}")
async def get_body_part_details(
    current_user: CurrentUser,
    body_part: str = Path(..., description="Specific body part name (e.g., 'Heart', 'Left Knee')")
):
    """
    Get detailed information for a specific body part.
    
    Args:
        body_part: Name of the body part to retrieve data for
        
    Returns:
        Detailed information including severity, event history, and statistics
    """
    try:
        patient_id = current_user.patient_id
        
        # Validate body part
        if not validate_body_part(body_part):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid body part: {body_part}. Must be one of the predefined body parts."
            )
        
        neo4j_client = get_graph()
        
        # Ensure user is initialized
        neo4j_client.ensure_user_initialized(patient_id)
        
        # Get current severity
        severities = neo4j_client.get_body_part_severities(user_id)
        current_severity = severities.get(body_part, "NA")
        
        # Get event history for this body part
        event_history = neo4j_client.get_body_part_history(user_id, body_part)
        
        # Get related conditions
        related_conditions = []
        if event_history:
            # Get the most recent event title for related condition search
            recent_event = event_history[0] if event_history else None
            if recent_event:
                related_conditions = neo4j_client.get_related_conditions(
                    patient_id, recent_event.get("title", "")
                )
        
        # Calculate statistics
        total_events = len(event_history)
        severity_counts = {}
        for event in event_history:
            sev = event.get("severity", "unknown")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
        
        return {
            "patient_id": patient_id,
            "body_part": body_part,
            "current_severity": current_severity,
            "statistics": {
                "total_events": total_events,
                "severity_distribution": severity_counts,
                "last_updated": event_history[0].get("timestamp") if event_history else None
            },
            "recent_events": event_history[:10],  # Last 10 events
            "related_conditions": related_conditions[:5]  # Top 5 related conditions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get body part details for {body_part}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve body part details")


@router.post("/body-part/{body_part}/severity")
async def update_body_part_severity(
    current_user: CurrentUser,
    body_part: str = Path(..., description="Body part name"),
    severity: str = Query(..., description="New severity level")
):
    """
    Manually update the severity of a specific body part.
    
    Args:
        body_part: Name of the body part
        severity: New severity level (NA, normal, mild, moderate, severe, critical)
    """
    try:
        patient_id = current_user.patient_id
        
        # Validate body part
        if not validate_body_part(body_part):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid body part: {body_part}"
            )
        
        # Validate severity
        valid_severities = list(get_severity_levels().keys())
        if severity not in valid_severities:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid severity: {severity}. Must be one of: {', '.join(valid_severities)}"
            )
        
        neo4j_client = get_graph()
        
        # Ensure user is initialized
        neo4j_client.ensure_user_initialized(patient_id)
        
        # Update severity
        success = neo4j_client.update_body_part_severity(patient_id, body_part, severity)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to update body part severity"
            )
        
        return {
            "message": "Body part severity updated successfully",
            "body_part": body_part,
            "new_severity": severity,
            "patient_id": patient_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update body part severity: {e}")
        raise HTTPException(status_code=500, detail="Failed to update severity")


@router.post("/auto-update-severities")
async def auto_update_severities(current_user: CurrentUser):
    """
    Automatically update all body part severities based on recent events.
    This endpoint can be called periodically or after document uploads.
    """
    try:
        patient_id = current_user.patient_id
        neo4j_client = get_graph()
        
        # Ensure user is initialized
        neo4j_client.ensure_user_initialized(patient_id)
        
        # Auto-update severities
        success = neo4j_client.auto_update_body_part_severities(patient_id)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to auto-update severities"
            )
        
        # Get updated severities
        severities = neo4j_client.get_body_part_severities(user_id)
        
        return {
            "message": "Body part severities updated successfully",
            "patient_id": patient_id,
            "updated_severities": severities
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to auto-update severities: {e}")
        raise HTTPException(status_code=500, detail="Failed to auto-update severities")


@router.get("/")
async def anatomy_overview(current_user: CurrentUser):
    """
    Get overview of all body parts with issues (legacy endpoint, updated).
    """
    try:
        patient_id = current_user.patient_id
        neo4j_client = get_graph()
        
        # Ensure user is initialized
        neo4j_client.ensure_user_initialized(patient_id)
        
        # Get all body parts with their issues
        hashed_user_id = neo4j_client._hash_user_id(patient_id)
        
        with neo4j_client.driver.session() as session:
            query = """
            MATCH (p:Patient {patient_id: $patient_id})-[:HAS_EVENT]->(e:Event)-[:AFFECTS]->(b:BodyPart)
            RETURN b.name AS body_part, 
                   collect({
                       title: e.title,
                       severity: e.severity,
                       timestamp: e.timestamp,
                       event_type: e.event_type
                   }) AS issues
            ORDER BY b.name
            """
            
            result = session.run(query, {"patient_id": hashed_user_id})
            
            issues_data = []
            for record in result:
                issues_data.append({
                    "body_part": record["body_part"],
                    "issues": record["issues"]
                })
            
            return {
                "patient_id": patient_id,
                "body_parts_with_issues": issues_data
            }
        
    except Exception as e:
        logger.error(f"Failed to get anatomy overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve anatomy overview")


@router.get("/{body_part}/timeline")
async def part_timeline(
    current_user: CurrentUser,
    body_part: str = Path(..., description="e.g. 'Right Shoulder' or 'Heart'")
):
    """
    Get timeline of events for a specific body part (legacy endpoint, updated).
    """
    try:
        patient_id = current_user.patient_id
        
        # Validate body part
        if not validate_body_part(body_part):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid body part: {body_part}"
            )
        
        neo4j_client = get_graph()
        
        # Ensure user is initialized
        neo4j_client.ensure_user_initialized(patient_id)
        
        # Get timeline events
        events = neo4j_client.get_body_part_history(user_id, body_part)
        
        return {
            "patient_id": patient_id,
            "body_part": body_part,
            "timeline": events
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get part timeline: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve timeline")


@router.get("/config/body-parts")
async def get_configured_body_parts():
    """
    Get the list of all configured body parts.
    Useful for frontend validation and configuration.
    """
    try:
        body_parts = get_default_body_parts()
        severity_levels = get_severity_levels()
        
        return {
            "body_parts": body_parts,
            "severity_levels": severity_levels,
            "total_parts": len(body_parts)
        }
        
    except Exception as e:
        logger.error(f"Failed to get configured body parts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve configuration")
