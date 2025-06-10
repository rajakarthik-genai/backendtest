"""
/timeline – chronological list of patient events from MongoDB.
"""

from datetime import datetime
from fastapi import APIRouter, Query
from bson import ObjectId
from src.db.mongo_db import MongoDBClient
from src.config.settings import settings

mongo = MongoDBClient(settings.mongo_uri, settings.mongo_db_name)
router = APIRouter(prefix="/timeline", tags=["timeline"])


@router.get("/")
async def timeline(user_id: str = Query(...), start: str | None = Query(None), end: str | None = Query(None)):
    """
    Return ordered timeline events between start and end ISO dates (optional).
    """
    start_dt = datetime.fromisoformat(start) if start else None
    end_dt = datetime.fromisoformat(end) if end else None
    records = mongo.query_timeline(user_id, start_dt, end_dt)
    # Convert ObjectId to string for safe JSON
    for r in records:
        r["_id"] = str(r.get("_id", ""))
        r["timestamp"] = r["timestamp"].isoformat() if r.get("timestamp") else ""
    return records
