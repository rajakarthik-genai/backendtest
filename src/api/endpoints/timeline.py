"""
Return chronological events (lab tests, injuries, etc.).
"""
from fastapi import APIRouter, Query

from src.db import mongo_db

router = APIRouter(prefix="/timeline", tags=["timeline"])


@router.get("/")
async def timeline(user_id: str = Query(...)):
    events = (
        mongo_db.events_col.find({"user_id": user_id}).sort("date", 1)
    )
    return [
        {
            "date": ev["date"],
            "type": ev["event_type"],
            "description": ev.get("description", ""),
        }
        for ev in events
    ]
