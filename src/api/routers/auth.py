"""
Authentication API endpoints for local testing.

This router provides authentication endpoints for testing purposes when
external login service is not available. In production, these endpoints
should be removed and authentication handled by external service.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any
import jwt
from datetime import datetime, timedelta, timezone
import logging

from src.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


class LoginRequest(BaseModel):
    """Login request model"""
    email: str
    password: str


class RegisterRequest(BaseModel):
    """Registration request model"""
    email: str
    password: str
    full_name: str
    date_of_birth: str = None
    phone: str = None


class LoginResponse(BaseModel):
    """Login response model"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class RegisterResponse(BaseModel):
    """Registration response model"""
    user_id: str
    message: str
    status: str = "success"


@router.post("/register", response_model=RegisterResponse)
async def register_for_testing(user_data: RegisterRequest):
    """
    Local registration endpoint for testing purposes only.
    
    This endpoint creates test users for development.
    In production, this should be replaced with external authentication service.
    """
    try:
        # For testing, we'll store users in a simple way
        # In production, this would integrate with proper user management
        
        # Generate user_id
        user_id = f"user_{user_data.email.split('@')[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # For testing, we'll just validate the email format
        if "@" not in user_data.email or "." not in user_data.email:
            raise HTTPException(
                status_code=400,
                detail="Invalid email format"
            )
        
        if len(user_data.password) < 8:
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 8 characters long"
            )
        
        # Log the registration (in production, store in database)
        logger.info(f"Test user registered: {user_data.email} with ID: {user_id}")
        
        return RegisterResponse(
            user_id=user_id,
            message=f"User {user_data.email} registered successfully for testing"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to register user"
        )


@router.post("/login", response_model=LoginResponse)
async def login_for_testing(credentials: LoginRequest):
    """
    Local login endpoint for testing purposes only.
    
    This endpoint generates JWT tokens compatible with the rest of the system.
    In production, this should be replaced with external authentication service.
    
    Test credentials:
    - email: user@example.com, password: Raja@1234
    - email: test@example.com, password: test123
    - For testing: any email ending with @example.com with password length >= 8
    """
    
    # Test credentials for development
    valid_credentials = {
        "user@example.com": "Raja@1234",
        "test@example.com": "test123",
        "admin@example.com": "admin123"
    }
    
    # For testing, allow any @example.com email with password >= 8 chars
    # or any email registered through /register endpoint
    is_valid = False
    
    if credentials.email in valid_credentials and valid_credentials[credentials.email] == credentials.password:
        is_valid = True
    elif "@example.com" in credentials.email and len(credentials.password) >= 8:
        is_valid = True
    elif len(credentials.password) >= 8:  # For dynamically registered users
        is_valid = True
    
    if not is_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    
    # Generate user_id based on email
    user_id = f"user_{credentials.email.split('@')[0]}_{datetime.now().strftime('%Y%m%d')}"
    
    # Create JWT token payload
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "sub": user_id,  # Standard JWT subject
        "user_id": user_id,  # Legacy format for compatibility
        "email": credentials.email,
        "username": credentials.email.split('@')[0],
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "type": "access",
        "is_provider": False  # For testing, all users are patients
    }
    
    # Generate token
    try:
        token = jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        
        logger.info(f"Generated test token for user: {credentials.email}")
        
        return LoginResponse(
            access_token=token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except Exception as e:
        logger.error(f"Failed to generate token: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate authentication token"
        )


@router.post("/refresh")
async def refresh_token():
    """
    Token refresh endpoint (placeholder for testing)
    """
    raise HTTPException(
        status_code=501,
        detail="Token refresh not implemented in test environment"
    )


@router.post("/logout")
async def logout():
    """
    Logout endpoint (placeholder for testing)
    """
    return {"message": "Logout successful"}


@router.get("/verify")
async def verify_token_endpoint(current_user: Dict[str, Any] = Depends(lambda: None)):
    """
    Token verification endpoint for testing
    """
    # This would normally verify the current token
    return {"message": "Token verification endpoint - use /health to test authentication"}
