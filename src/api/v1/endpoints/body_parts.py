"""
Body Parts endpoints for severity tracking and timeline analysis.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Path, Depends
from pydantic import BaseModel, Field

from src.utils.logging import logger
from src.auth.dependencies import CurrentUser
from src.db.neo4j_db import get_graph
from src.db.mongo_db import get_mongo
from src.config.body_parts import get_default_body_parts, get_severity_levels

router = APIRouter(tags=["body_parts"])


class BodyPartSeverity(BaseModel):
    """Model for body part severity."""
    name: str = Field(description="Body part name")
    severity: str = Field(description="Severity level (NA, normal, mild, moderate, severe, critical)")
    event_count: int = Field(description="Number of events for this body part")
    last_updated: str = Field(description="Last update timestamp")


class BodyPartsResponse(BaseModel):
    """Response model for body parts severity."""
    patient_id: str = Field(description="Patient identifier")
    body_parts: List[BodyPartSeverity] = Field(description="List of body parts with severity")
    total_parts: int = Field(description="Total number of body parts")
    last_updated: str = Field(description="Last update timestamp")


class BodyPartTimelineEvent(BaseModel):
    """Model for body part timeline event."""
    event_id: str = Field(description="Event identifier")
    timestamp: str = Field(description="Event timestamp")
    title: str = Field(description="Event title")
    description: str = Field(description="Event description")
    severity: str = Field(description="Event severity")
    source: str = Field(description="Event source (document, manual, etc.)")


class BodyPartTimelineResponse(BaseModel):
    """Response model for body part timeline."""
    body_part: str = Field(description="Body part name")
    patient_id: str = Field(description="Patient identifier")
    events: List[BodyPartTimelineEvent] = Field(description="Timeline events")
    total_events: int = Field(description="Total number of events")
    severity_summary: Dict[str, int] = Field(description="Severity distribution")


@router.get("/severity", response_model=BodyPartsResponse)
async def get_body_parts_severity(current_user: CurrentUser):
    """
    Get severity status for all 30+ body parts for the patient.
    
    Returns severity levels based on information extracted from uploaded documents.
    If no information is available for a body part, returns "NA".
    """
    try:
        patient_id = current_user.patient_id
        neo4j_client = get_graph()
        
        # Ensure user is initialized
        neo4j_client.ensure_user_initialized(patient_id)
        
        # Get severities for all body parts
        severities = neo4j_client.get_body_part_severities(patient_id)
        
        # Get all default body parts
        default_body_parts = get_default_body_parts()
        
        # Format response for all body parts
        body_parts_data = []
        for body_part in default_body_parts:
            severity_info = severities.get(body_part, {
                "severity": "NA",
                "event_count": 0,
                "last_updated": datetime.utcnow().isoformat()
            })
            
            body_parts_data.append(BodyPartSeverity(
                name=body_part,
                severity=severity_info.get("severity", "NA"),
                event_count=severity_info.get("event_count", 0),
                last_updated=severity_info.get("last_updated", datetime.utcnow().isoformat())
            ))
        
        return BodyPartsResponse(
            patient_id=patient_id,
            body_parts=body_parts_data,
            total_parts=len(body_parts_data),
            last_updated=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to get body parts severity: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve body parts severity: {str(e)}")


@router.get("/timeline/{body_part}", response_model=BodyPartTimelineResponse)
async def get_body_part_timeline(
    body_part: str = Path(..., description="Body part name"),
    current_user: CurrentUser = Depends(),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """
    Get timeline of events for a specific body part.
    
    Returns all collected data and events related to the specified body part.
    """
    try:
        patient_id = current_user.patient_id
        neo4j_client = get_graph()
        
        # Validate body part
        default_body_parts = get_default_body_parts()
        if body_part not in default_body_parts:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid body part: {body_part}. Must be one of the predefined body parts."
            )
        
        # Parse date range
        start_dt = None
        end_dt = None
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")
        
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")
        
        # Get timeline events for the body part
        events = neo4j_client.get_body_part_timeline(
            patient_id, 
            body_part, 
            start_date=start_dt, 
            end_date=end_dt
        )
        
        # Format events
        timeline_events = []
        severity_counts = {"NA": 0, "normal": 0, "mild": 0, "moderate": 0, "severe": 0, "critical": 0}
        
        for event in events:
            severity = event.get("severity", "NA")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            timeline_events.append(BodyPartTimelineEvent(
                event_id=event.get("event_id", ""),
                timestamp=event.get("timestamp", ""),
                title=event.get("title", ""),
                description=event.get("description", ""),
                severity=severity,
                source=event.get("source", "unknown")
            ))
        
        return BodyPartTimelineResponse(
            body_part=body_part,
            patient_id=patient_id,
            events=timeline_events,
            total_events=len(timeline_events),
            severity_summary=severity_counts
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get body part timeline: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve body part timeline: {str(e)}")


@router.get("/timeline/{body_part}/range", response_model=BodyPartTimelineResponse)
async def get_body_part_timeline_range(
    body_part: str = Path(..., description="Body part name"),
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    current_user: CurrentUser = Depends()
):
    """
    Get timeline of events for a specific body part within a date range.
    
    Returns relevant information for the specified body part from start_date to end_date.
    """
    try:
        patient_id = current_user.patient_id
        neo4j_client = get_graph()
        
        # Validate body part
        default_body_parts = get_default_body_parts()
        if body_part not in default_body_parts:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid body part: {body_part}. Must be one of the predefined body parts."
            )
        
        # Parse dates
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # Validate date range
        if start_dt > end_dt:
            raise HTTPException(status_code=400, detail="Start date must be before end date")
        
        # Get timeline events for the body part within date range
        events = neo4j_client.get_body_part_timeline(
            patient_id, 
            body_part, 
            start_date=start_dt, 
            end_date=end_dt
        )
        
        # Format events
        timeline_events = []
        severity_counts = {"NA": 0, "normal": 0, "mild": 0, "moderate": 0, "severe": 0, "critical": 0}
        
        for event in events:
            severity = event.get("severity", "NA")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            timeline_events.append(BodyPartTimelineEvent(
                event_id=event.get("event_id", ""),
                timestamp=event.get("timestamp", ""),
                title=event.get("title", ""),
                description=event.get("description", ""),
                severity=severity,
                source=event.get("source", "unknown")
            ))
        
        return BodyPartTimelineResponse(
            body_part=body_part,
            patient_id=patient_id,
            events=timeline_events,
            total_events=len(timeline_events),
            severity_summary=severity_counts
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get body part timeline range: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve body part timeline range: {str(e)}")


@router.get("/list")
async def get_available_body_parts():
    """
    Get list of all available body parts.
    """
    try:
        body_parts = get_default_body_parts()
        severity_levels = get_severity_levels()
        
        return {
            "body_parts": body_parts,
            "total_count": len(body_parts),
            "severity_levels": severity_levels,
            "description": "Available body parts for severity tracking and timeline analysis"
        }
        
    except Exception as e:
        logger.error(f"Failed to get body parts list: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve body parts list")


@router.get("/health")
async def get_body_parts_health():
    """Health check for body parts service."""
    return {
        "status": "healthy",
        "service": "body_parts",
        "version": "1.0.0",
        "features": [
            "Body parts severity tracking",
            "Timeline analysis",
            "Date range filtering",
            "Severity level classification",
            "Event source tracking"
        ]
    } 