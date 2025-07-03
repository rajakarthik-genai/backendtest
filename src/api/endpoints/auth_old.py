"""
Authentication endpoints for JWT tokens and user management.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional
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


class UserResponse(BaseModel):
    """User information response model."""
    user_id: str
    email: str
    username: str
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    roles: list[str] = []


# Token generation utilities
def create_access_token(user_id: str, email: str, username: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)  # 15 minutes default
    
    payload = {
        "user_id": user_id,
        "email": email,
        "username": username,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    }
    
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token


def create_refresh_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT refresh token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)  # 7 days default
    
    payload = {
        "user_id": user_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh"
    }
    
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token


def verify_refresh_token(token: str) -> Optional[str]:
    """Verify refresh token and return user_id."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        # Check if it's a refresh token
        if payload.get("type") != "refresh":
            return None
        
        # Check expiration
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            return None
        
        return payload.get("user_id")
        
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid refresh token: {e}")
        return None


# TODO: Replace with actual database operations
# This is a placeholder - you'll need to implement actual user storage
class UserDB:
    """Placeholder for user database operations."""
    
    @staticmethod
    def create_user(email: str, username: str, password: str, full_name: Optional[str] = None) -> str:
        """Create new user and return user_id."""
        # TODO: Implement actual user creation in your database
        # This should hash the password and store user data
        import uuid
        user_id = str(uuid.uuid4())
        logger.info(f"Created user {email} with ID {user_id}")
        return user_id
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[dict]:
        """Get user by email."""
        # TODO: Implement actual user lookup
        # Return None if user not found
        return None
    
    @staticmethod
    def verify_password(email: str, password: str) -> Optional[dict]:
        """Verify user password and return user data."""
        # TODO: Implement actual password verification
        # Return user data if password is correct, None otherwise
        return None
    
    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[dict]:
        """Get user by user_id."""
        # TODO: Implement actual user lookup by ID
        return None


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserSignupRequest):
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
        
        # Generate tokens
        access_token = create_access_token(
            user_id=user_id,
            email=user_data.email,
            username=user_data.username,
            expires_delta=timedelta(minutes=15)
        )
        
        refresh_token = create_refresh_token(
            user_id=user_id,
            expires_delta=timedelta(days=7)
        )
        
        logger.info(f"User {user_data.email} signed up successfully")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=15 * 60,  # 15 minutes in seconds
            user_id=user_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during signup"
        )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLoginRequest):
    """
    Authenticate user and return access and refresh tokens.
    """
    try:
        # Verify credentials
        user_data = UserDB.verify_password(credentials.email, credentials.password)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Generate tokens
        access_token = create_access_token(
            user_id=user_data["user_id"],
            email=user_data["email"],
            username=user_data["username"],
            expires_delta=timedelta(minutes=15)
        )
        
        refresh_token = create_refresh_token(
            user_id=user_data["user_id"],
            expires_delta=timedelta(days=7)
        )
        
        logger.info(f"User {credentials.email} logged in successfully")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=15 * 60,  # 15 minutes in seconds
            user_id=user_data["user_id"]
        )
        
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
        # Verify refresh token
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
        
        # Generate new tokens
        access_token = create_access_token(
            user_id=user_data["user_id"],
            email=user_data["email"],
            username=user_data["username"],
            expires_delta=timedelta(minutes=15)
        )
        
        new_refresh_token = create_refresh_token(
            user_id=user_data["user_id"],
            expires_delta=timedelta(days=7)
        )
        
        logger.info(f"Tokens refreshed for user {user_id}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=15 * 60,  # 15 minutes in seconds
            user_id=user_data["user_id"]
        )
        
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


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout user (client should discard tokens).
    
    Note: Since JWT tokens are stateless, actual logout happens on the client side
    by discarding the tokens. For enhanced security, you could implement a token
    blacklist in Redis or database.
    """
    logger.info(f"User {current_user.user_id} logged out")
    return {"message": "Successfully logged out"}


@router.post("/verify")
async def verify_token_endpoint(current_user: User = Depends(get_current_user)):
    """
    Verify if the provided token is valid and return user info.
    """
    return {
        "valid": True,
        "user_id": current_user.user_id,
        "email": current_user.email,
        "username": current_user.username
    }
