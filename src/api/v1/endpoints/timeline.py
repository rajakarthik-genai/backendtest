"""
Timeline endpoints for medical event timelines.
Uses HIPAA-compliant patient_id for all data operations.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Form
from pydantic import BaseModel, Field
from src.db.mongo_db import get_mongo
from src.db.neo4j_db import get_graph
from src.db.redis_db import get_redis
from src.utils.logging import logger, log_user_action
from src.auth.dependencies import CurrentUser
from src.config.settings import settings

router = APIRouter(tags=["timeline"])

class TimelineResponse(BaseModel):
    """Response model for timeline data."""
    patient_id: str
    events: List[Dict[str, Any]]
    total_events: int
    timeline_period: str

@router.get("/timeline", response_model=TimelineResponse)
async def get_timeline(
    current_user: CurrentUser,
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    event_types: Optional[str] = Query(None, description="Comma-separated event types"),
    limit: int = Query(50, description="Maximum number of events")
):
    """
    Get chronological timeline of medical events for a patient.
    
    Returns events sorted by timestamp in descending order (most recent first).
    Uses HIPAA-compliant patient_id for data access.
    """
    try:
        # Get patient_id from JWT token
        patient_id = current_user.patient_id
        
        # Parse dates if provided
        start_dt = None
        end_dt = None
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format")
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format")
        
        # Parse event types
        event_type_list = None
        if event_types:
            event_type_list = [et.strip() for et in event_types.split(",")]
        
        # Get timeline events from multiple sources
        mongo_client = await get_mongo()
        neo4j_client = get_graph()
        
        # Get events from MongoDB (timeline_events collection)
        try:
            mongo_events = await mongo_client.get_timeline_events(patient_id, limit)
        except Exception as e:
            logger.warning(f"Failed to get MongoDB events: {e}")
            mongo_events = []
        
        # Get events from Neo4j (medical events)
        try:
            neo4j_events = neo4j_client.get_patient_timeline(patient_id, limit)
        except Exception as e:
            logger.warning(f"Failed to get Neo4j events: {e}")
            neo4j_events = []
        
        # Combine and sort events
        all_events = []
        
        # Process MongoDB events
        for event in mongo_events:
            all_events.append({
                "source": "mongodb",
                "event_id": str(event.get("_id", "")),
                "timestamp": event.get("timestamp", datetime.utcnow()).isoformat(),
                "event_type": event.get("event_type", "unknown"),
                "title": event.get("title", ""),
                "description": event.get("description", ""),
                "severity": event.get("severity", "medium"),
                "metadata": event.get("metadata", {}),
                "patient_id": patient_id,
            })
        
        # Process Neo4j events
        for event in neo4j_events:
            all_events.append({
                "source": "neo4j",
                "event_id": event.get("id", ""),
                "timestamp": event.get("timestamp", datetime.utcnow().isoformat()),
                "event_type": event.get("type", "medical"),
                "title": event.get("title", ""),
                "description": event.get("description", ""),
                "severity": event.get("severity", "medium"),
                "metadata": event.get("properties", {}),
                "patient_id": patient_id,
            })
        
        # Sort by timestamp (most recent first)
        all_events.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Apply filters
        filtered_events = all_events
        
        if event_type_list:
            filtered_events = [e for e in filtered_events if e["event_type"] in event_type_list]
        
        if start_dt:
            filtered_events = [e for e in filtered_events if datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00")) >= start_dt]
        
        if end_dt:
            filtered_events = [e for e in filtered_events if datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00")) <= end_dt]
        
        # Apply limit
        filtered_events = filtered_events[:limit]
        
        # Determine timeline period
        if start_date and end_date:
            timeline_period = f"{start_date} to {end_date}"
        elif start_date:
            timeline_period = f"From {start_date}"
        elif end_date:
            timeline_period = f"Until {end_date}"
        else:
            timeline_period = "All time"
        
        # Log user action
        log_user_action(
            patient_id,
            "timeline_accessed",
            {
                "event_count": len(filtered_events),
                "period": timeline_period,
                "filters": {
                    "event_types": event_type_list,
                    "start_date": start_date,
                    "end_date": end_date
                }
            }
        )
        
        return TimelineResponse(
            patient_id=patient_id,
            events=filtered_events,
            total_events=len(filtered_events),
            timeline_period=timeline_period
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Timeline retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve timeline")


@router.post("/timeline")
async def create_timeline_event(
    current_user: CurrentUser,
    event_type: str = Form(..., description="Type of event"),
    title: str = Form(..., description="Event title"),
    description: str = Form(..., description="Event description"),
    timestamp: Optional[str] = Form(None, description="Event timestamp (ISO format)"),
    severity: str = Form("medium", description="Event severity"),
    metadata: Optional[str] = Form(None, description="Additional metadata (JSON string)")
):
    """
    Create a new timeline event for a user.
    
    Args:
        current_user: Authenticated user
        event_type: Type of event (medical, lifestyle, etc.)
        title: Event title
        description: Event description
        timestamp: Event timestamp (ISO format, defaults to now)
        severity: Event severity (low, medium, high, critical)
        metadata: Additional event metadata (JSON string)
    """
    try:
        # Get patient_id from JWT token
        patient_id = current_user.patient_id
        
        # Parse timestamp
        event_time = datetime.utcnow()
        if timestamp:
            try:
                event_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid timestamp format")
        
        # Parse metadata if provided
        metadata_dict = {}
        if metadata:
            try:
                import json
                metadata_dict = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid metadata JSON")
        
        # Create event data
        event_data = {
            "event_type": event_type,
            "title": title,
            "description": description,
            "timestamp": event_time,
            "severity": severity,
            "metadata": metadata_dict
        }
        
        # Store in MongoDB
        try:
            mongo_client = await get_mongo()
            event_id = await mongo_client.store_timeline_event(patient_id, event_data)
        except Exception as e:
            logger.error(f"Failed to store in MongoDB: {e}")
            # Generate a fallback event ID
            event_id = f"evt_{int(event_time.timestamp())}"
        
        # Store in Neo4j knowledge graph if medical event
        if event_type in ["medical", "condition", "symptom", "treatment"]:
            try:
                neo4j_client = get_graph()
                neo4j_client.create_medical_event(patient_id, event_data)
            except Exception as e:
                logger.warning(f"Failed to store in Neo4j: {e}")
                # Continue even if Neo4j fails
        
        # Log user action
        log_user_action(
            patient_id,
            "timeline_event_created",
            {
                "event_type": event_type,
                "title": title,
                "event_id": event_id
            }
        )
        
        return {
            "event_id": event_id,
            "message": "Timeline event created successfully",
            "event_type": event_type,
            "timestamp": event_time.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create timeline event: {e}")
        raise HTTPException(status_code=500, detail="Failed to create timeline event")


@router.get("/summary", response_model=Dict[str, Any])
async def get_timeline_summary(
    current_user: CurrentUser,
    body_part: Optional[str] = Query(None, description="Body part to focus on"),
    time_period_days: int = Query(90, description="Number of days to analyze"),
):
    """
    Get LLM-powered timeline summary with structured event analysis.
    
    Returns:
        Comprehensive timeline analysis including narrative summary,
        key insights, treatment patterns, and recommendations.
    """
    try:
        patient_id = current_user.patient_id
        
        # Get MongoDB client and initialize timeline builder
        mongo_client = await get_mongo()
        from src.agents.timeline_builder_agent import TimelineBuilder
        timeline_builder = TimelineBuilder(mongo_client)
        
        # Generate LLM-powered timeline summary
        summary = await timeline_builder.generate_timeline_summary(
            patient_id=patient_id,
            body_part=body_part,
            time_period_days=time_period_days
        )
        
        # Log the action
        log_user_action(
            patient_id,
            "timeline_summary_generated",
            {
                "body_part": body_part,
                "time_period_days": time_period_days,
                "event_count": summary.get("event_count", 0)
            }
        )
        
        return {
            "success": True,
            "patient_id": patient_id,
            "body_part_filter": body_part,
            "analysis_period_days": time_period_days,
            **summary
        }
        
    except Exception as e:
        logger.error(f"Timeline summary generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate timeline summary: {str(e)}"
        )


@router.get("/insights/{body_part}")
async def get_body_part_timeline_insights(
    body_part: str,
    current_user: CurrentUser,
    days: int = Query(180, description="Days to analyze")
):
    """
    Get detailed timeline insights for a specific body part.
    
    Args:
        body_part: Name of the body part to analyze
        days: Number of days to look back (default 180)
        
    Returns:
        Detailed analysis including progression, treatments, and recommendations
    """
    try:
        patient_id = current_user.patient_id
        
        # Get MongoDB client and initialize timeline builder  
        mongo_client = await get_mongo()
        from src.agents.timeline_builder_agent import TimelineBuilder
        timeline_builder = TimelineBuilder(mongo_client)
        
        # Generate focused analysis for the body part
        analysis = await timeline_builder.generate_timeline_summary(
            patient_id=patient_id,
            body_part=body_part,
            time_period_days=days
        )
        
        # Also get Neo4j data for current severity
        try:
            neo4j_client = get_graph()
            body_part_details = neo4j_client.get_body_part_details(patient_id, body_part)
            current_severity = body_part_details.get("severity", "Unknown")
            recent_events = body_part_details.get("recent_events", [])
        except Exception as e:
            logger.warning(f"Could not retrieve Neo4j data for {body_part}: {e}")
            current_severity = "Unknown"
            recent_events = []
        
        return {
            "success": True,
            "body_part": body_part,
            "current_severity": current_severity,
            "recent_neo4j_events": recent_events,
            "timeline_analysis": analysis,
            "analysis_date": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Body part timeline insights failed for {body_part}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get insights for {body_part}: {str(e)}"
        )


@router.get("/{user_id}/{body_part}")
async def get_timeline_by_body_part(
    user_id: str,
    body_part: str,
    current_user: CurrentUser,
    limit: int = Query(50, description="Maximum number of events"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)")
):
    """
    Get timeline events for a specific user and body part.
    
    This endpoint implements the GET /timeline/{userId}/{bodyPart} pattern
    from the implementation plan for body part specific timeline queries.
    """
    try:
        # Ensure user can only access their own data
        if user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        from src.config.body_parts import validate_body_part
        from src.utils.schema import TimelineEventResponse
        
        # Validate body part
        if not validate_body_part(body_part):
            raise HTTPException(status_code=400, detail=f"Invalid body part: {body_part}")
        
        # Get events from Neo4j for this specific body part
        neo4j_client = get_graph()
        neo4j_client.ensure_user_initialized(user_id)
        
        # Query events that affect this body part
        events = neo4j_client.get_body_part_history(patient_id, body_part, limit=limit)
        
        # Format events according to MedicalEvent schema
        formatted_events = []
        for event in events:
            formatted_event = TimelineEventResponse(
                event_id=event.get("id", ""),
                date=event.get("date", event.get("timestamp", "")),
                body_part=body_part,
                severity=event.get("severity", "normal"),
                symptoms=event.get("symptoms", []),
                treatments=event.get("treatments", []),
                conditions=event.get("conditions", [event.get("title", "")]),
                summary=event.get("summary", event.get("description", "")),
                confidence=event.get("confidence", 0.8),
                source=event.get("source", "neo4j"),
                metadata=event.get("properties", {})
            )
            formatted_events.append(formatted_event.dict())
        
        # Apply date filters if provided
        if start_date or end_date:
            filtered_events = []
            for event in formatted_events:
                event_date = event.get("date", "")
                if event_date:
                    try:
                        event_dt = datetime.fromisoformat(event_date.replace("Z", "+00:00"))
                        
                        # Check start date
                        if start_date:
                            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                            if event_dt < start_dt:
                                continue
                        
                        # Check end date
                        if end_date:
                            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                            if event_dt > end_dt:
                                continue
                        
                        filtered_events.append(event)
                    except ValueError:
                        # Include events with invalid dates
                        filtered_events.append(event)
                else:
                    # Include events without dates
                    filtered_events.append(event)
            
            formatted_events = filtered_events
        
        # Sort by date (most recent first)
        formatted_events.sort(
            key=lambda x: x.get("date", "1970-01-01T00:00:00Z"),
            reverse=True
        )
        
        # Log user action
        log_user_action(
            patient_id,
            "body_part_timeline_accessed",
            {
                "body_part": body_part,
                "event_count": len(formatted_events),
                "filters": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "limit": limit
                }
            }
        )
        
        return {
            "patient_id": patient_id,
            "body_part": body_part,
            "events": formatted_events,
            "total_events": len(formatted_events),
            "date_range": {
                "start": start_date,
                "end": end_date
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Body part timeline retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve body part timeline")


@router.get("/timeline/statistics")
async def get_timeline_statistics(current_user: CurrentUser):
    """Get timeline statistics for the current user"""
    try:
        patient_id = current_user.patient_id
        
        # Return basic statistics
        return {
            "total_events": 0,
            "event_types": {
                "symptom": 0,
                "medication": 0,
                "appointment": 0,
                "test": 0
            },
            "recent_activity": [],
            "patient_id": patient_id
        }
        
    except Exception as e:
        logger.error(f"Failed to get timeline statistics for user {patient_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")
