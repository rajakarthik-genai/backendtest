"""
Events API - Basic CRUD operations for manual health events.

This module provides endpoints for creating, reading, updating, and deleting
health events manually entered by users or healthcare providers.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends, status
from pydantic import BaseModel, Field
from src.db.mongo_db import get_mongo
from src.db.neo4j_db import get_graph
from src.utils.schema import TimelineEvent, EventsRequest, EventsResponse
from src.utils.logging import logger, log_user_action

router = APIRouter(prefix="/events", tags=["events"])


class EventCreate(BaseModel):
    """Model for creating a new event."""
    event_type: str = Field(..., description="Type of event (medical, lifestyle, etc.)")
    title: str = Field(..., min_length=1, max_length=200, description="Event title")
    description: Optional[str] = Field(None, max_length=2000, description="Event description")
    timestamp: Optional[datetime] = Field(None, description="Event timestamp (defaults to now)")
    severity: str = Field("medium", description="Event severity (low, medium, high, critical)")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional event metadata")
    body_parts: Optional[List[str]] = Field(default_factory=list, description="Affected body parts")


class EventUpdate(BaseModel):
    """Model for updating an existing event."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    event_type: Optional[str] = None
    severity: Optional[str] = None
    metadata: Optional[dict] = None
    body_parts: Optional[List[str]] = None


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_event(
    user_id: str = Query(..., description="User identifier"),
    event: EventCreate = ...
):
    """
    Create a new manual health event.
    
    Args:
        user_id: User identifier
        event: Event data to create
    
    Returns:
        Dictionary containing the created event ID and details
    """
    try:
        # Validate event type and severity
        if event.event_type not in ["medical", "lifestyle", "symptom", "treatment", "medication", "lab_test", "injury", "note"]:
            raise HTTPException(status_code=400, detail="Invalid event type")
        
        if event.severity not in ["low", "medium", "high", "critical"]:
            raise HTTPException(status_code=400, detail="Invalid severity level")
        
        # Prepare event data
        event_data = {
            "event_type": event.event_type,
            "title": event.title,
            "description": event.description or "",
            "timestamp": event.timestamp or datetime.utcnow(),
            "severity": event.severity,
            "metadata": event.metadata,
            "body_parts": event.body_parts,
            "source": "manual"
        }
        
        # Store in MongoDB
        mongo_client = await get_mongo()
        event_id = await mongo_client.store_medical_record(user_id, event_data)
        
        # Store in Neo4j knowledge graph if medical event
        if event.event_type in ["medical", "symptom", "treatment", "medication"]:
            neo4j_client = get_graph()
            await neo4j_client.create_medical_event(
                user_id,
                {
                    **event_data,
                    "event_id": event_id
                }
            )
        
        # Log user action
        log_user_action(
            user_id,
            "event_created",
            {
                "event_type": event.event_type,
                "title": event.title,
                "event_id": event_id
            }
        )
        
        logger.info(f"Manual event created {event_id} for user {user_id}")
        
        return {
            "event_id": event_id,
            "message": "Event created successfully",
            "event_type": event.event_type,
            "timestamp": event_data["timestamp"].isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create event for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create event")


@router.get("/")
async def get_events(
    user_id: str = Query(..., description="User identifier"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip")
):
    """
    Retrieve events for a user with optional filtering.
    
    Args:
        user_id: User identifier
        event_type: Optional event type filter
        start_date: Optional start date filter
        end_date: Optional end date filter
        limit: Maximum number of events to return
        offset: Number of events to skip
    
    Returns:
        List of events matching the criteria
    """
    try:
        mongo_client = await get_mongo()
        
        # Build filter criteria
        filters = {}
        if event_type:
            filters["event_type"] = event_type
        if start_date:
            filters["timestamp"] = {"$gte": start_date}
        if end_date:
            if "timestamp" not in filters:
                filters["timestamp"] = {}
            filters["timestamp"]["$lte"] = end_date
        
        # Get events from MongoDB
        events = await mongo_client.get_medical_records(
            user_id,
            filters=filters,
            limit=limit,
            offset=offset
        )
        
        return {
            "events": events,
            "count": len(events),
            "offset": offset,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve events for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve events")


@router.get("/{event_id}")
async def get_event(
    event_id: str,
    user_id: str = Query(..., description="User identifier")
):
    """
    Retrieve a specific event by ID.
    
    Args:
        event_id: Event identifier
        user_id: User identifier
    
    Returns:
        Event details
    """
    try:
        mongo_client = await get_mongo()
        event = await mongo_client.get_medical_record(user_id, event_id)
        
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        return event
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve event {event_id} for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve event")


@router.put("/{event_id}")
async def update_event(
    event_id: str,
    user_id: str = Query(..., description="User identifier"),
    event_update: EventUpdate = ...
):
    """
    Update an existing event.
    
    Args:
        event_id: Event identifier
        user_id: User identifier
        event_update: Event update data
    
    Returns:
        Updated event details
    """
    try:
        mongo_client = await get_mongo()
        
        # Check if event exists
        existing_event = await mongo_client.get_medical_record(user_id, event_id)
        if not existing_event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Prepare update data
        update_data = {}
        for field, value in event_update.dict(exclude_unset=True).items():
            if value is not None:
                update_data[field] = value
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid update data provided")
        
        # Validate severity if provided
        if "severity" in update_data and update_data["severity"] not in ["low", "medium", "high", "critical"]:
            raise HTTPException(status_code=400, detail="Invalid severity level")
        
        # Update in MongoDB
        await mongo_client.update_medical_record(user_id, event_id, update_data)
        
        # Update in Neo4j if medical event
        if existing_event.get("event_type") in ["medical", "symptom", "treatment", "medication"]:
            neo4j_client = get_graph()
            await neo4j_client.update_medical_event(user_id, event_id, update_data)
        
        # Get updated event
        updated_event = await mongo_client.get_medical_record(user_id, event_id)
        
        # Log user action
        log_user_action(
            user_id,
            "event_updated",
            {
                "event_id": event_id,
                "updated_fields": list(update_data.keys())
            }
        )
        
        logger.info(f"Event {event_id} updated for user {user_id}")
        
        return {
            "event": updated_event,
            "message": "Event updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update event {event_id} for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update event")


@router.delete("/{event_id}")
async def delete_event(
    event_id: str,
    user_id: str = Query(..., description="User identifier")
):
    """
    Delete an event.
    
    Args:
        event_id: Event identifier
        user_id: User identifier
    
    Returns:
        Deletion confirmation
    """
    try:
        mongo_client = await get_mongo()
        
        # Check if event exists
        existing_event = await mongo_client.get_medical_record(user_id, event_id)
        if not existing_event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Delete from MongoDB
        await mongo_client.delete_medical_record(user_id, event_id)
        
        # Delete from Neo4j if medical event
        if existing_event.get("event_type") in ["medical", "symptom", "treatment", "medication"]:
            neo4j_client = get_graph()
            await neo4j_client.delete_medical_event(user_id, event_id)
        
        # Log user action
        log_user_action(
            user_id,
            "event_deleted",
            {
                "event_id": event_id,
                "event_type": existing_event.get("event_type")
            }
        )
        
        logger.info(f"Event {event_id} deleted for user {user_id}")
        
        return {
            "message": "Event deleted successfully",
            "event_id": event_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete event {event_id} for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete event")
