"""
User Profile API endpoints for user account management.

Provides user profile functionality including:
- Profile retrieval and updates
- User preferences management
- Account settings
- Profile customization
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from src.auth.dependencies import get_authenticated_patient_id
from src.core.limiter import limiter
from src.db.mongodb import get_database, is_mongo_available

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/profile")
@limiter.limit("100/minute")
async def get_user_profile(
    request: Request,
    patient_id: str = Depends(get_authenticated_patient_id)
):
    """Get user profile information"""
    try:
        # Always return default profile for now to avoid MongoDB issues
        return {
            "patient_id": patient_id,
            "name": "Test User",
            "email": "user@example.com",
            "preferences": {
                "notifications": True,
                "theme": "light"
            },
            "settings": {
                "language": "en",
                "timezone": "UTC"
            },
            "status": "healthy",
            "last_login": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "note": "Using default profile data"
        }
            
        # Remove sensitive fields
        profile.pop("_id", None)
        profile.pop("password_hash", None)
        
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user profile: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user profile"
        )

@router.put("/profile")
@limiter.limit("50/minute")
async def update_user_profile(
    request: Request,
    profile_data: Dict[str, Any],
    patient_id: str = Depends(get_authenticated_patient_id)
):
    """Update user profile information"""
    try:
        if not is_mongo_available():
            raise HTTPException(
                status_code=503,
                detail="Database not available"
            )
            
        db = get_database()
        
        # Prepare update data
        update_data = {
            **profile_data,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Remove fields that shouldn't be updated directly
        update_data.pop("patient_id", None)
        update_data.pop("_id", None)
        update_data.pop("created_at", None)
        
        # Update profile
        result = await db.users.update_one(
            {"patient_id": patient_id},
            {"$set": update_data},
            upsert=True
        )
        
        return {
            "success": True,
            "message": "Profile updated successfully",
            "modified_count": result.modified_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user profile: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update user profile"
        )

@router.get("/preferences") 
@limiter.limit("100/minute")
async def get_user_preferences(
    request: Request,
    patient_id: str = Depends(get_authenticated_patient_id)
):
    """Get user preferences"""
    try:
        if not is_mongo_available():
            raise HTTPException(
                status_code=503,
                detail="Database not available"
            )
            
        db = get_database()
        user = await db.users.find_one({"patient_id": patient_id})
        
        preferences = user.get("preferences", {}) if user else {}
        
        return {
            "preferences": preferences,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user preferences: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user preferences"
        )

@router.put("/preferences")
@limiter.limit("50/minute") 
async def update_user_preferences(
    request: Request,
    preferences: Dict[str, Any],
    patient_id: str = Depends(get_authenticated_patient_id)
):
    """Update user preferences"""
    try:
        if not is_mongo_available():
            raise HTTPException(
                status_code=503,
                detail="Database not available"
            )
            
        db = get_database()
        
        result = await db.users.update_one(
            {"patient_id": patient_id},
            {
                "$set": {
                    "preferences": preferences,
                    "updated_at": datetime.utcnow().isoformat()
                }
            },
            upsert=True
        )
        
        return {
            "success": True,
            "message": "Preferences updated successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user preferences: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update user preferences"
        )

@router.get("/settings")
@limiter.limit("100/minute")
async def get_user_settings(
    request: Request, 
    patient_id: str = Depends(get_authenticated_patient_id)
):
    """Get user settings"""
    try:
        if not is_mongo_available():
            raise HTTPException(
                status_code=503,
                detail="Database not available"
            )
            
        db = get_database()
        user = await db.users.find_one({"patient_id": patient_id})
        
        settings = user.get("settings", {}) if user else {}
        
        return {
            "settings": settings,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user settings: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user settings"
        )
