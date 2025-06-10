"""
/events – basic CRUD for manual health events.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from src.db.mongo_db import MongoDBClient
from src.config.settings import settings
from src.utils.logging import logger

mongo = MongoDBClient(settings.mongo_uri, settings.mongo_db_name)
router = APIRouter(prefix="/events", tags=["events"])


class EventIn(BaseModel):
    patient_id: str = Field(..., description="User ID")
    event_type: str = Field(..., description="lab_test | injury | medication | note")
    description: str | None = None
    timestamp: datetime | None = None


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_event(evt: EventIn):
    evt_id = mongo.collection.insert_one(
        {
            "patient_id": evt.patient_id,
            "event_type": evt.event_type,
            "description": evt.description or "",
            "timestamp": evt.timestamp or datetime.utcnow(),
            "source": "manual",
        }
    ).inserted_id
    logger.info("Manual event created %s for patient %s", evt_id, evt.patient_id)
    return {"event_id": str(evt_id)}
