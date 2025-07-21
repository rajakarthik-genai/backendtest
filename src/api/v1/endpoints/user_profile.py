"""
User Profile and Analytics endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from src.auth.dependencies import CurrentUser
from src.utils.logging import logger
from src.db.mongo_db import get_mongo

router = APIRouter(tags=["user-profile"])

class UserProfileRequest(BaseModel):
    preferences: Optional[Dict[str, Any]] = Field({}, description="User preferences")
    settings: Optional[Dict[str, Any]] = Field({}, description="User settings")

@router.get("/user/profile")
async def get_user_profile(current_user: CurrentUser):
    """Get user profile information from MongoDB."""
    mongo_client = await get_mongo()
    profile_records = await mongo_client.get_medical_records(
        user_id=current_user.patient_id,
        record_type="profile",
        limit=1
    )
    profile = profile_records[0]["data"] if profile_records else {}
    return {
        "user_id": current_user.patient_id,
        "email": getattr(current_user, "email", None),
        **profile
    }

@router.put("/user/profile")
async def update_user_profile(
    request: UserProfileRequest,
    current_user: CurrentUser
):
    """Update user profile and persist to MongoDB."""
    mongo_client = await get_mongo()
    update_data = {
        "preferences": request.preferences,
        "settings": request.settings
    }
    await mongo_client.store_medical_record(
        user_id=current_user.patient_id,
        record_data=update_data,
        record_type="profile"
    )
    return {
        "message": "Profile updated successfully",
        "user_id": current_user.patient_id,
        "updated_fields": list(request.preferences.keys()) + list(request.settings.keys())
    }

@router.get("/user/preferences")
async def get_user_preferences(current_user: CurrentUser):
    """Get user preferences"""
    return {
        "notifications": True,
        "data_sharing": False,
        "language": "en",
        "theme": "light",
        "units": "metric",
        "patient_id": current_user.patient_id
    }

@router.get("/user/settings")
async def get_user_settings(current_user: CurrentUser):
    """Get user settings"""
    return {
        "privacy_level": "standard",
        "data_retention": "1_year",
        "export_format": "json",
        "backup_enabled": True,
        "patient_id": current_user.patient_id
    }
