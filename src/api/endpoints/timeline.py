"""
Timeline endpoints for medical event timelines.
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

router = APIRouter(prefix="/timeline", tags=["timeline"])

class TimelineResponse(BaseModel):
    """Response model for timeline data."""
    user_id: str
    events: List[Dict[str, Any]]
    total_events: int
    timeline_period: str

@router.get("/", response_model=TimelineResponse)
async def get_timeline(
    current_user: CurrentUser,
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
        # Get user_id from JWT token
        user_id = current_user.user_id
        
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
            mongo_events = await mongo_client.get_timeline_events(user_id, limit)
        except Exception as e:
            logger.warning(f"Failed to get MongoDB events: {e}")
            mongo_events = []
        
        # Get events from Neo4j (medical events)
        try:
            neo4j_events = neo4j_client.get_patient_timeline(user_id, limit)
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
                "user_id": user_id,
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
                "user_id": user_id,
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
            user_id,
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
            user_id=user_id,
            events=filtered_events,
            total_events=len(filtered_events),
            timeline_period=timeline_period
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Timeline retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve timeline")


@router.post("/event")
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
        # Get user_id from JWT token
        user_id = current_user.user_id
        
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
            event_id = await mongo_client.store_timeline_event(user_id, event_data)
        except Exception as e:
            logger.error(f"Failed to store in MongoDB: {e}")
            # Generate a fallback event ID
            event_id = f"evt_{int(event_time.timestamp())}"
        
        # Store in Neo4j knowledge graph if medical event
        if event_type in ["medical", "condition", "symptom", "treatment"]:
            try:
                neo4j_client = get_graph()
                neo4j_client.create_medical_event(user_id, event_data)
            except Exception as e:
                logger.warning(f"Failed to store in Neo4j: {e}")
                # Continue even if Neo4j fails
        
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
    current_user: CurrentUser,
    days: int = Query(30, description="Number of days to summarize")
):
    """
    Get a summary of timeline events for the specified period.
    
    Args:
        current_user: Authenticated user
        days: Number of days to look back
    """
    try:
        # Get user_id from JWT token
        user_id = current_user.user_id
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get events from MongoDB
        try:
            mongo_client = await get_mongo()
            events = await mongo_client.get_timeline_events(user_id, limit=1000)
        except Exception as e:
            logger.warning(f"Failed to get MongoDB events: {e}")
            events = []
        
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


@router.get("/search")
async def search_timeline_events(
    current_user: CurrentUser,
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
        current_user: Authenticated user
        event_type: Filter by event type
        severity: Filter by severity level
        start_date: Start date filter (ISO format)
        end_date: End date filter (ISO format)
        search_term: Search term for title/description
        limit: Maximum number of results
    """
    try:
        # Get user_id from JWT token
        user_id = current_user.user_id
        
        # Get all events first
        try:
            mongo_client = await get_mongo()
            all_events = await mongo_client.get_timeline_events(user_id, limit=1000)
        except Exception as e:
            logger.warning(f"Failed to get MongoDB events: {e}")
            all_events = []
        
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
