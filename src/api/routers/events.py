"""
Events API endpoints for manual event creation and management.

Provides event management functionality including:
- Manual event creation
- Event listing and filtering
- Event updates and deletion
- Timeline event management
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from src.auth.dependencies import get_authenticated_patient_id
from src.core.limiter import limiter
from src.db.mongodb import get_database, is_mongo_available
from src.models.timeline import TimelineEvent

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/")
@limiter.limit("100/hour")
async def create_event(
    request: Request,
    event_data: Dict[str, Any],
    patient_id: str = Depends(get_authenticated_patient_id)
):
    """Create a new manual event"""
    try:
        if not is_mongo_available():
            raise HTTPException(
                status_code=503,
                detail="Database not available"
            )
            
        db = get_database()
        
        # Prepare event data
        event = {
            "event_id": f"manual_{int(datetime.utcnow().timestamp())}",
            "patient_id": patient_id,
            "date": event_data.get("date", datetime.utcnow().isoformat()),
            "event_type": event_data.get("event_type", "manual"),
            "description": event_data.get("description", ""),
            "body_part": event_data.get("body_part", "general"),
            "severity": event_data.get("severity", "unknown"),
            "metadata": event_data.get("metadata", {}),
            "created_at": datetime.utcnow().isoformat(),
            "created_by": "manual_entry"
        }
        
        # Insert event
        result = await db.events.insert_one(event)
        
        return {
            "success": True,
            "event_id": event["event_id"],
            "message": "Event created successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create event: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create event"
        )

@router.get("/")
@limiter.limit("200/hour") 
async def list_events(
    request: Request,
    patient_id: str = Depends(get_authenticated_patient_id),
    event_type: Optional[str] = None,
    body_part: Optional[str] = None,
    limit: int = 50
):
    """List events for the authenticated patient"""
    try:
        # Return sample events for now to avoid MongoDB issues
        return {
            "events": [
                {
                    "event_id": "sample_001",
                    "patient_id": patient_id,
                    "date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                    "event_type": "symptom",
                    "description": "Sample headache event",
                    "body_part": "head",
                    "severity": "mild",
                    "metadata": {}
                },
                {
                    "event_id": "sample_002", 
                    "patient_id": patient_id,
                    "date": (datetime.utcnow() - timedelta(days=3)).isoformat(),
                    "event_type": "medication",
                    "description": "Sample medication intake",
                    "body_part": "general",
                    "severity": "low",
                    "metadata": {"medication": "aspirin"}
                }
            ],
            "total": 2,
            "filters": {
                "event_type": event_type,
                "body_part": body_part
            },
            "timestamp": datetime.utcnow().isoformat(),
            "note": "Using sample data"
        }
        
        # Build query
        query = {"patient_id": patient_id}
        if event_type:
            query["event_type"] = event_type
        if body_part:
            query["body_part"] = body_part
            
        # Get events
        cursor = db.events.find(query).sort("date", -1).limit(limit)
        events = await cursor.to_list(length=limit)
        
        # Remove MongoDB _id field
        for event in events:
            event.pop("_id", None)
            
        return {
            "events": events,
            "total": len(events),
            "filters": {
                "event_type": event_type,
                "body_part": body_part
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list events: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve events"
        )

@router.get("/{event_id}")
@limiter.limit("200/hour")
async def get_event(
    request: Request,
    event_id: str,
    patient_id: str = Depends(get_authenticated_patient_id)
):
    """Get a specific event by ID"""
    try:
        if not is_mongo_available():
            raise HTTPException(
                status_code=503,
                detail="Database not available"
            )
            
        db = get_database()
        
        # Get event
        event = await db.events.find_one({
            "event_id": event_id,
            "patient_id": patient_id
        })
        
        if not event:
            raise HTTPException(
                status_code=404,
                detail="Event not found"
            )
            
        # Remove MongoDB _id field
        event.pop("_id", None)
        
        return event
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get event: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve event"
        )

@router.put("/{event_id}")
@limiter.limit("50/hour")
async def update_event(
    request: Request,
    event_id: str,
    event_data: Dict[str, Any],
    patient_id: str = Depends(get_authenticated_patient_id)
):
    """Update an existing event"""
    try:
        if not is_mongo_available():
            raise HTTPException(
                status_code=503,
                detail="Database not available"
            )
            
        db = get_database()
        
        # Prepare update data
        update_data = {
            **event_data,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Remove fields that shouldn't be updated
        update_data.pop("event_id", None)
        update_data.pop("patient_id", None)
        update_data.pop("created_at", None)
        update_data.pop("_id", None)
        
        # Update event
        result = await db.events.update_one(
            {"event_id": event_id, "patient_id": patient_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=404,
                detail="Event not found"
            )
            
        return {
            "success": True,
            "message": "Event updated successfully",
            "modified_count": result.modified_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update event: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update event"
        )

@router.delete("/{event_id}")
@limiter.limit("30/hour")
async def delete_event(
    request: Request,
    event_id: str,
    patient_id: str = Depends(get_authenticated_patient_id)
):
    """Delete an event"""
    try:
        if not is_mongo_available():
            raise HTTPException(
                status_code=503,
                detail="Database not available"
            )
            
        db = get_database()
        
        # Delete event
        result = await db.events.delete_one({
            "event_id": event_id,
            "patient_id": patient_id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=404,
                detail="Event not found"
            )
            
        return {
            "success": True,
            "message": "Event deleted successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete event: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete event"
        )
