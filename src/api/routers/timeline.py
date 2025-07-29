"""
Timeline API endpoints for medical event history and chronological analysis.

Provides comprehensive timeline functionality including:
- Body part specific event histories
- Chronological medical data retrieval
- Timeline visualization data
- Patient journey tracking across body systems
- Event filtering by date ranges and types

Integration: MongoDB for document storage, Neo4j for knowledge graph relationships
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List, Dict, Any, Optional
from datetime import date
from src.core.exceptions import ValidationError
from src.auth.dependencies import get_authenticated_patient_id
from src.core.database import get_database_clients
from src.core.limiter import limiter
import logging

from src.api.dependencies import get_current_user, require_patient_access
from src.auth.dependencies import get_authenticated_patient_id, AuthenticatedPatientId
from src.models.timeline import TimelineEvent, TimelineRequest
from src.core.config import settings
from src.core.database import get_database_clients
from src.core.limiter import limiter

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/events", response_model=List[TimelineEvent])
@limiter.limit("1000/hour")
async def get_body_part_timeline(
    request: Request,
    timeline_request: TimelineRequest,
    current_user: dict = Depends(get_current_user),
    db_clients: dict = Depends(get_database_clients),
    _: str = Depends(require_patient_access)
):
    """
    Retrieve comprehensive chronological timeline for a specific body part.
    
    Returns complete medical history including:
    - Diagnoses and medical conditions
    - Treatments and interventions
    - Test results and measurements
    - Symptoms and clinical observations
    - Procedures and surgeries
    - Medication history
    
    Args:
        timeline_request: Request body with patient_id, body_part, and optional filters
        
    Returns:
        List[TimelineEvent]: Chronologically sorted medical events
        
    Features:
    - Date range filtering (start_date, end_date)
    - Body part validation against configured parts
    - Neo4j graph traversal for complete relationship mapping
    - JSON serialization for complex medical data
    """
    try:
        if timeline_request.body_part not in settings.BODY_PARTS:
            raise HTTPException(status_code=400, detail="Invalid body part")
        
        neo4j = db_clients["neo4j"]
        
        # Build query conditions
        where_conditions = [
            "p.patient_id = $patient_id",
            "bp.name = $body_part"
        ]
        
        query_params = {
            "patient_id": timeline_request.patient_id,
            "body_part": timeline_request.body_part
        }
        
        # Add date filters
        if timeline_request.start_date:
            where_conditions.append("date(ev.date) >= date($start_date)")
            query_params["start_date"] = timeline_request.start_date.isoformat()
        
        if timeline_request.end_date:
            where_conditions.append("date(ev.date) <= date($end_date)")
            query_params["end_date"] = timeline_request.end_date.isoformat()
        
        # Add event type filter
        if timeline_request.event_types:
            where_conditions.append("ev.event_type IN $event_types")
            query_params["event_types"] = timeline_request.event_types
        
        where_clause = " AND ".join(where_conditions)
        
        # Query timeline events
        timeline_query = f"""
            MATCH (p:Patient)-[:HAS_BODY_PART]->(bp:BodyPart)<-[:AFFECTS]-(ev:Event)
            OPTIONAL MATCH (ev)-[:FROM_DOCUMENT]->(d:Document)
            WHERE {where_clause}
            
            RETURN ev.event_id as event_id,
                   ev.date as date,
                   ev.event_type as event_type,
                   ev.description as description,
                   ev.severity as severity,
                   d.document_id as source_document_id,
                   ev.metadata as metadata
            ORDER BY ev.date DESC
            LIMIT 100
        """
        
        timeline_result = await neo4j.execute_query(timeline_query, query_params)
        
        # Convert to timeline events
        timeline_events = []
        for record in timeline_result:
            # Parse date
            event_date = record["date"]
            if isinstance(event_date, str):
                try:
                    event_date = datetime.fromisoformat(event_date)
                except:
                    event_date = datetime.now()
            
            timeline_event = TimelineEvent(
                event_id=record["event_id"] or f"evt_{len(timeline_events)}",
                date=event_date,
                body_part=timeline_request.body_part,
                event_type=record["event_type"] or "unknown",
                description=record["description"] or "No description",
                severity=record["severity"],
                source_document_id=record["source_document_id"] or "unknown",
                metadata=record["metadata"] or {}
            )
            timeline_events.append(timeline_event)
        
        return timeline_events
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get timeline: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/patient")
@limiter.limit("1000/hour")
async def get_patient_timeline(
    request: Request,
    patient_id: AuthenticatedPatientId,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    event_types: Optional[List[str]] = None,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db_clients: dict = Depends(get_database_clients),
    _: str = Depends(require_patient_access)
):
    """
    Get complete timeline for a patient across all body parts
    """
    try:
        neo4j = db_clients["neo4j"]
        
        # Build query conditions
        where_conditions = ["p.patient_id = $patient_id"]
        query_params = {"patient_id": patient_id}
        
        # Add date filters
        if start_date:
            where_conditions.append("date(ev.date) >= date($start_date)")
            query_params["start_date"] = start_date.isoformat()
        
        if end_date:
            where_conditions.append("date(ev.date) <= date($end_date)")
            query_params["end_date"] = end_date.isoformat()
        
        # Add event type filter
        if event_types:
            where_conditions.append("ev.event_type IN $event_types")
            query_params["event_types"] = event_types
        
        where_clause = " AND ".join(where_conditions)
        
        # Query all timeline events
        timeline_query = f"""
            MATCH (p:Patient)-[:HAS_EVENT]->(ev:Event)
            OPTIONAL MATCH (ev)-[:AFFECTS]->(bp:BodyPart)
            OPTIONAL MATCH (ev)-[:FROM_DOCUMENT]->(d:Document)
            WHERE {where_clause}
            
            RETURN ev.event_id as event_id,
                   ev.date as date,
                   bp.name as body_part,
                   ev.event_type as event_type,
                   ev.description as description,
                   ev.severity as severity,
                   d.document_id as source_document_id,
                   ev.metadata as metadata
            ORDER BY ev.date DESC
            LIMIT $limit
        """
        
        query_params["limit"] = limit
        timeline_result = await neo4j.execute_query(timeline_query, query_params)
        
        # Convert to timeline events
        timeline_events = []
        for record in timeline_result:
            # Parse date
            event_date = record["date"]
            if isinstance(event_date, str):
                try:
                    event_date = datetime.fromisoformat(event_date)
                except:
                    event_date = datetime.now()
            
            timeline_event = TimelineEvent(
                event_id=record["event_id"] or f"evt_{len(timeline_events)}",
                date=event_date,
                body_part=record["body_part"] or "unknown",
                event_type=record["event_type"] or "unknown",
                description=record["description"] or "No description",
                severity=record["severity"],
                source_document_id=record["source_document_id"] or "unknown",
                metadata=record["metadata"] or {}
            )
            timeline_events.append(timeline_event)
        
        return {
            "patient_id": patient_id,
            "timeline_events": timeline_events,
            "total_events": len(timeline_events),
            "date_range": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get patient timeline: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary")
@limiter.limit("1000/hour")
async def get_timeline_summary(
    request: Request,
    patient_id: str = Depends(get_authenticated_patient_id),
    db_clients: dict = Depends(get_database_clients)
):
    """
    Get timeline summary statistics
    """
    try:
        neo4j = db_clients["neo4j"]
        
        # Get timeline statistics
        stats_query = """
            MATCH (p:Patient {patient_id: $patient_id})-[:HAS_EVENT]->(ev:Event)
            OPTIONAL MATCH (ev)-[:AFFECTS]->(bp:BodyPart)
            
            WITH ev, bp
            RETURN 
                count(DISTINCT ev) as total_events,
                count(DISTINCT bp) as affected_body_parts,
                collect(DISTINCT ev.event_type) as event_types,
                min(ev.date) as earliest_event,
                max(ev.date) as latest_event,
                avg(ev.severity) as average_severity
        """
        
        stats_result = await neo4j.execute_query(stats_query, {"patient_id": patient_id})
        
        if not stats_result:
            return {
                "patient_id": patient_id,
                "total_events": 0,
                "affected_body_parts": 0,
                "event_types": [],
                "date_range": None,
                "average_severity": 0
            }
        
        record = stats_result[0]
        
        # Get event type breakdown
        breakdown_query = """
            MATCH (p:Patient {patient_id: $patient_id})-[:HAS_EVENT]->(ev:Event)
            RETURN ev.event_type as event_type, count(*) as count
            ORDER BY count DESC
        """
        
        breakdown_result = await neo4j.execute_query(breakdown_query, {"patient_id": patient_id})
        
        event_breakdown = {
            record["event_type"]: record["count"]
            for record in breakdown_result
        }
        
        return {
            "patient_id": patient_id,
            "total_events": record["total_events"] or 0,
            "affected_body_parts": record["affected_body_parts"] or 0,
            "event_types": record["event_types"] or [],
            "event_breakdown": event_breakdown,
            "date_range": {
                "earliest": record["earliest_event"],
                "latest": record["latest_event"]
            },
            "average_severity": record["average_severity"] or 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get timeline summary: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
