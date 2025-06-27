"""
Timeline endpoints for chronological medical events and history.

Features:
- Patient timeline visualization
- Event filtering and date ranges
- Medical history aggregation
- User data isolation
"""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Form

from src.utils.schema import TimelineRequest, TimelineResponse, TimelineEvent
from src.utils.logging import logger, log_user_action
from src.db.mongo_db import get_mongo
from src.db.neo4j_db import get_graph

router = APIRouter(prefix="/timeline", tags=["timeline"])


@router.get("/", response_model=TimelineResponse)
async def get_timeline(
    user_id: str = Query(..., description="User identifier"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    event_types: Optional[str] = Query(None, description="Comma-separated event types"),
    limit: int = Query(50, description="Maximum number of events")
):
    """
    Get chronological timeline of medical events for a user.
    
    Returns events sorted by timestamp in descending order (most recent first).
    """
    try:
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
        mongo_events = await mongo_client.get_timeline_events(user_id, limit)
        
        # Get events from Neo4j (medical events)
        neo4j_events = neo4j_client.get_patient_timeline(user_id, limit)
        
        # Combine and sort events
        all_events = []
        
        # Process MongoDB events
        for event in mongo_events:
            timeline_event = TimelineEvent(
                event_id=event.get("event_id"),
                user_id=user_id,
                event_type=event.get("event_type", "general"),
                title=event.get("title", ""),
                description=event.get("description", ""),
                timestamp=datetime.fromisoformat(event["timestamp"]) if isinstance(event["timestamp"], str) else event["timestamp"],
                severity=event.get("severity", "medium"),
                metadata=event.get("metadata", {})
            )
            all_events.append(timeline_event)
        
        # Process Neo4j events
        for event in neo4j_events:
            timeline_event = TimelineEvent(
                event_id=event.get("event_id"),
                user_id=user_id,
                event_type=event.get("event_type", "medical"),
                title=event.get("title", ""),
                description=event.get("description", ""),
                timestamp=datetime.fromisoformat(event["timestamp"]) if isinstance(event["timestamp"], str) else event["timestamp"],
                severity=event.get("severity", "medium"),
                metadata={
                    "affected_body_parts": event.get("affected_body_parts", []),
                    "source": "knowledge_graph"
                }
            )
            all_events.append(timeline_event)
        
        # Filter by date range
        if start_dt or end_dt:
            filtered_events = []
            for event in all_events:
                event_time = event.timestamp
                if start_dt and event_time < start_dt:
                    continue
                if end_dt and event_time > end_dt:
                    continue
                filtered_events.append(event)
            all_events = filtered_events
        
        # Filter by event types
        if event_type_list:
            all_events = [e for e in all_events if e.event_type in event_type_list]
        
        # Sort by timestamp (most recent first)
        all_events.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Limit results
        all_events = all_events[:limit]
        
        # Determine actual date range
        actual_start = min(e.timestamp for e in all_events) if all_events else datetime.utcnow()
        actual_end = max(e.timestamp for e in all_events) if all_events else datetime.utcnow()
        
        # Log user action
        log_user_action(
            user_id,
            "timeline_view",
            {
                "event_count": len(all_events),
                "date_range": f"{actual_start.isoformat()} to {actual_end.isoformat()}"
            }
        )
        
        return TimelineResponse(
            events=all_events,
            total_count=len(all_events),
            date_range={
                "start": actual_start,
                "end": actual_end
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Timeline retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve timeline")


@router.post("/event")
async def create_timeline_event(
    user_id: str,
    event_type: str,
    title: str,
    description: str,
    timestamp: Optional[str] = None,
    severity: str = "medium",
    metadata: Optional[dict] = None
):
    """
    Create a new timeline event for a user.
    
    Args:
        user_id: User identifier
        event_type: Type of event (medical, lifestyle, etc.)
        title: Event title
        description: Event description
        timestamp: Event timestamp (ISO format, defaults to now)
        severity: Event severity (low, medium, high, critical)
        metadata: Additional event metadata
    """
    try:
        # Parse timestamp
        event_time = datetime.utcnow()
        if timestamp:
            try:
                event_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid timestamp format")
        
        # Create event data
        event_data = {
            "event_type": event_type,
            "title": title,
            "description": description,
            "timestamp": event_time,
            "severity": severity,
            "metadata": metadata or {}
        }
        
        # Store in MongoDB
        mongo_client = await get_mongo()
        event_id = await mongo_client.store_timeline_event(user_id, event_data)
        
        # Store in Neo4j knowledge graph if medical event
        if event_type in ["medical", "condition", "symptom", "treatment"]:
            neo4j_client = get_graph()
            neo4j_client.create_medical_event(user_id, event_data)
        
        # Log user action
        log_user_action(
            user_id,
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


@router.get("/summary")
async def get_timeline_summary(
    user_id: str = Query(..., description="User identifier"),
    days: int = Query(30, description="Number of days to summarize")
):
    """
    Get a summary of timeline events for the specified period.
    
    Args:
        user_id: User identifier
        days: Number of days to look back
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get events from MongoDB
        mongo_client = await get_mongo()
        events = await mongo_client.get_timeline_events(user_id, limit=1000)
        
        # Filter events within date range
        period_events = []
        for event in events:
            event_time = datetime.fromisoformat(event["timestamp"]) if isinstance(event["timestamp"], str) else event["timestamp"]
            if start_date <= event_time <= end_date:
                period_events.append(event)
        
        # Create summary statistics
        summary = {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "total_events": len(period_events),
            "event_types": {},
            "severity_distribution": {},
            "daily_activity": {},
            "trends": {}
        }
        
        # Analyze event types
        for event in period_events:
            event_type = event.get("event_type", "unknown")
            summary["event_types"][event_type] = summary["event_types"].get(event_type, 0) + 1
            
            severity = event.get("severity", "medium")
            summary["severity_distribution"][severity] = summary["severity_distribution"].get(severity, 0) + 1
            
            # Daily activity - get date from each event
            event_time = datetime.fromisoformat(event["timestamp"]) if isinstance(event["timestamp"], str) else event["timestamp"]
            event_date = event_time.date().isoformat()
            summary["daily_activity"][event_date] = summary["daily_activity"].get(event_date, 0) + 1
        
        # Calculate trends
        if len(period_events) > 1:
            recent_half = period_events[:len(period_events)//2]
            older_half = period_events[len(period_events)//2:]
            
            summary["trends"]["activity_trend"] = "increasing" if len(recent_half) > len(older_half) else "decreasing"
        else:
            summary["trends"]["activity_trend"] = "stable"
        
        # Log user action
        log_user_action(
            user_id,
            "timeline_summary_view",
            {
                "days": days,
                "total_events": len(period_events)
            }
        )
        
        return summary
        
    except Exception as e:
        logger.error(f"Timeline summary failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate timeline summary")


@router.delete("/event/{event_id}")
async def delete_timeline_event(
    event_id: str,
    user_id: str = Query(..., description="User identifier for access control")
):
    """
    Delete a timeline event.
    
    Args:
        event_id: Event identifier
        user_id: User identifier for access control
    """
    try:
        # Get MongoDB client
        mongo_client = await get_mongo()
        
        # Verify event exists and belongs to user
        event = await mongo_client.get_timeline_event(user_id, event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Timeline event not found")
        
        # Delete from MongoDB
        deleted = await mongo_client.delete_timeline_event(user_id, event_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Timeline event not found")
        
        # Remove from Neo4j if it was a medical event
        if event.get("event_type") in ["medical", "condition", "symptom", "treatment"]:
            try:
                neo4j_client = get_graph()
                neo4j_client.delete_medical_event(user_id, event_id)
            except Exception as e:
                logger.warning(f"Failed to delete from Neo4j: {e}")
                # Continue even if Neo4j deletion fails
        
        log_user_action(
            user_id,
            "timeline_event_deleted",
            {"event_id": event_id, "event_type": event.get("event_type")}
        )
        
        return {
            "message": "Timeline event deleted successfully",
            "event_id": event_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete timeline event: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete timeline event")


@router.put("/event/{event_id}")
async def update_timeline_event(
    event_id: str,
    user_id: str = Query(..., description="User identifier"),
    title: Optional[str] = Form(None, description="Event title"),
    description: Optional[str] = Form(None, description="Event description"),
    event_type: Optional[str] = Form(None, description="Type of event"),
    severity: Optional[str] = Form(None, description="Event severity"),
    timestamp: Optional[str] = Form(None, description="Event timestamp (ISO format)"),
    metadata: Optional[str] = Form(None, description="Additional metadata (JSON string)")
):
    """
    Update an existing timeline event.
    
    Args:
        event_id: Event identifier
        user_id: User identifier
        title: Updated event title
        description: Updated event description
        event_type: Updated event type
        severity: Updated event severity
        timestamp: Updated timestamp (ISO format)
        metadata: Updated metadata (JSON string)
    """
    try:
        # Get MongoDB client
        mongo_client = await get_mongo()
        
        # Verify event exists and belongs to user
        existing_event = await mongo_client.get_timeline_event(user_id, event_id)
        if not existing_event:
            raise HTTPException(status_code=404, detail="Timeline event not found")
        
        # Build update data
        update_data = {}
        if title is not None:
            update_data["title"] = title
        if description is not None:
            update_data["description"] = description
        if event_type is not None:
            update_data["event_type"] = event_type
        if severity is not None:
            update_data["severity"] = severity
        if timestamp is not None:
            try:
                event_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                update_data["timestamp"] = event_time
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid timestamp format")
        if metadata is not None:
            try:
                import json
                update_data["metadata"] = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid metadata JSON")
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")
        
        # Update in MongoDB
        updated = await mongo_client.update_timeline_event(user_id, event_id, update_data)
        if not updated:
            raise HTTPException(status_code=404, detail="Timeline event not found")
        
        # Update in Neo4j if it's a medical event
        if existing_event.get("event_type") in ["medical", "condition", "symptom", "treatment"]:
            try:
                neo4j_client = get_graph()
                neo4j_client.update_medical_event(user_id, event_id, update_data)
            except Exception as e:
                logger.warning(f"Failed to update in Neo4j: {e}")
                # Continue even if Neo4j update fails
        
        # Log user action
        log_user_action(
            user_id,
            "timeline_event_updated",
            {
                "event_id": event_id,
                "updated_fields": list(update_data.keys())
            }
        )
        
        return {
            "message": "Timeline event updated successfully",
            "event_id": event_id,
            "updated_fields": list(update_data.keys())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update timeline event: {e}")
        raise HTTPException(status_code=500, detail="Failed to update timeline event")


@router.get("/search")
async def search_timeline_events(
    user_id: str = Query(..., description="User identifier"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    search_term: Optional[str] = Query(None, description="Search in title/description"),
    limit: int = Query(50, description="Maximum number of results")
):
    """
    Search and filter timeline events.
    
    Args:
        user_id: User identifier
        event_type: Filter by event type
        severity: Filter by severity level
        start_date: Start date filter (ISO format)
        end_date: End date filter (ISO format)
        search_term: Search term for title/description
        limit: Maximum number of results
    """
    try:
        # Get MongoDB client
        mongo_client = await get_mongo()
        
        # Get all events first
        all_events = await mongo_client.get_timeline_events(user_id, limit=1000)
        
        # Apply filters
        filtered_events = []
        
        for event in all_events:
            # Event type filter
            if event_type and event.get("event_type") != event_type:
                continue
            
            # Severity filter
            if severity and event.get("severity") != severity:
                continue
            
            # Date range filter
            event_time = datetime.fromisoformat(event["timestamp"]) if isinstance(event["timestamp"], str) else event["timestamp"]
            
            if start_date:
                try:
                    start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                    if event_time < start_dt:
                        continue
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid start_date format")
            
            if end_date:
                try:
                    end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                    if event_time > end_dt:
                        continue
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid end_date format")
            
            # Search term filter
            if search_term:
                search_lower = search_term.lower()
                title = event.get("title", "").lower()
                description = event.get("description", "").lower()
                if search_lower not in title and search_lower not in description:
                    continue
            
            filtered_events.append(event)
        
        # Apply limit
        result_events = filtered_events[:limit]
        
        # Log user action
        log_user_action(
            user_id,
            "timeline_search",
            {
                "filters": {
                    "event_type": event_type,
                    "severity": severity,
                    "start_date": start_date,
                    "end_date": end_date,
                    "search_term": search_term is not None
                },
                "result_count": len(result_events)
            }
        )
        
        return {
            "events": result_events,
            "total_found": len(filtered_events),
            "returned": len(result_events),
            "filters_applied": {
                "event_type": event_type,
                "severity": severity,
                "start_date": start_date,
                "end_date": end_date,
                "search_term": bool(search_term)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Timeline search failed: {e}")
        raise HTTPException(status_code=500, detail="Timeline search failed")
