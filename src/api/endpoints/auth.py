"""
Authentication endpoints for JWT tokens and user management.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr

from src.config.settings import settings
from src.auth.jwt_auth import (
    get_current_user, 
    create_token_response, 
    verify_refresh_token,
    refresh_access_token,
    invalidate_refresh_token,
    hash_password,
    verify_password
)
from src.auth.models import User, UserCreate, UserLogin, TokenResponse, RefreshTokenRequest
from src.utils.logging import logger


router = APIRouter(prefix="/auth", tags=["authentication"])


# Additional Response Models
class UserResponse(BaseModel):
    """User information response model."""
    user_id: str
    email: str
    username: str
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    roles: list[str] = []


class LogoutResponse(BaseModel):
    """Logout response model."""
    message: str
    logged_out_at: datetime


class TokenVerificationResponse(BaseModel):
    """Token verification response model."""
    valid: bool
    user_id: str
    email: Optional[str] = None
    username: Optional[str] = None


# TODO: Replace with actual database operations
# This is a placeholder - you'll need to implement actual user storage
class UserDB:
    """Placeholder for user database operations."""
    
    # In-memory storage for demo purposes (use actual database in production)
    _users: Dict[str, Dict[str, Any]] = {}
    _emails: Dict[str, str] = {}  # email -> user_id mapping
    
    @classmethod
    def create_user(cls, email: str, username: str, password: str, full_name: Optional[str] = None) -> str:
        """Create new user and return user_id."""
        # Check if email already exists
        if email in cls._emails:
            raise ValueError("User with this email already exists")
        
        user_id = str(uuid.uuid4())
        hashed_password = hash_password(password)
        
        user_data = {
            "user_id": user_id,
            "email": email,
            "username": username,
            "password_hash": hashed_password,
            "full_name": full_name,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "roles": []
        }
        
        cls._users[user_id] = user_data
        cls._emails[email] = user_id
        
        logger.info(f"Created user {email} with ID {user_id[:8]}...")
        return user_id
    
    @classmethod
    def get_user_by_email(cls, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        user_id = cls._emails.get(email)
        if user_id:
            return cls._users.get(user_id)
        return None
    
    @classmethod
    def verify_user_password(cls, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Verify user password and return user data."""
        user_data = cls.get_user_by_email(email)
        if user_data and verify_password(password, user_data["password_hash"]):
            return user_data
        return None
    
    @classmethod
    def get_user_by_id(cls, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by user_id."""
        return cls._users.get(user_id)


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate):
    """
    Create new user account and return access and refresh tokens.
    """
    try:
        # Check if user already exists
        existing_user = UserDB.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Create new user
        user_id = UserDB.create_user(
            email=user_data.email,
            username=user_data.username,
            password=user_data.password,
            full_name=user_data.full_name
        )
        
        # Generate tokens using modular JWT system
        token_response = create_token_response(
            user_id=user_id,
            email=user_data.email,
            username=user_data.username
        )
        
        logger.info(f"User {user_data.email} signed up successfully")
        return token_response
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during signup"
        )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """
    Authenticate user and return access and refresh tokens.
    """
    try:
        # Verify credentials
        user_data = UserDB.verify_user_password(credentials.email, credentials.password)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Generate tokens using modular JWT system
        token_response = create_token_response(
            user_id=user_data["user_id"],
            email=user_data["email"],
            username=user_data["username"]
        )
        
        logger.info(f"User {credentials.email} logged in successfully")
        return token_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(refresh_request: RefreshTokenRequest):
    """
    Refresh access token using refresh token.
    """
    try:
        # Verify refresh token and get user_id
        user_id = verify_refresh_token(refresh_request.refresh_token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        # Get user data
        user_data = UserDB.get_user_by_id(user_id)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Invalidate old refresh token and generate new tokens
        invalidate_refresh_token(refresh_request.refresh_token)
        
        token_response = create_token_response(
            user_id=user_data["user_id"],
            email=user_data["email"],
            username=user_data["username"]
        )
        
        logger.info(f"Tokens refreshed for user {user_id[:8]}...")
        return token_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token refresh"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current user information from JWT token.
    """
    try:
        # Get additional user data from database if needed
        user_data = UserDB.get_user_by_id(current_user.user_id)
        
        return UserResponse(
            user_id=current_user.user_id,
            email=current_user.email or "",
            username=current_user.username or "",
            full_name=user_data.get("full_name") if user_data else None,
            is_active=current_user.is_active,
            created_at=user_data.get("created_at", datetime.now(timezone.utc)) if user_data else datetime.now(timezone.utc),
            roles=current_user.roles
        )
        
    except Exception as e:
        logger.error(f"Get user info error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    refresh_request: RefreshTokenRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Logout user by invalidating refresh token.
    
    Note: The client should also discard all tokens locally.
    """
    try:
        # Invalidate the refresh token
        invalidate_refresh_token(refresh_request.refresh_token)
        
        logger.info(f"User {current_user.user_id[:8]}... logged out")
        return LogoutResponse(
            message="Successfully logged out",
            logged_out_at=datetime.now(timezone.utc)
        )
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        # Even if token invalidation fails, consider logout successful
        return LogoutResponse(
            message="Logged out (please discard tokens locally)",
            logged_out_at=datetime.now(timezone.utc)
        )


@router.post("/verify", response_model=TokenVerificationResponse)
async def verify_token_endpoint(current_user: User = Depends(get_current_user)):
    """
    Verify if the provided token is valid and return user info.
    """
    return TokenVerificationResponse(
        valid=True,
        user_id=current_user.user_id,
        email=current_user.email,
        username=current_user.username
    )
