"""
Authentication models for JWT tokens and user data.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr


class TokenData(BaseModel):
    """JWT token payload data."""
    sub: str  # subject - user_id
    email: Optional[str] = None
    username: Optional[str] = None
    exp: Optional[datetime] = None
    iat: Optional[datetime] = None
    token_type: Optional[str] = "access"  # access or refresh


class User(BaseModel):
    """User information extracted from JWT token."""
    user_id: str
    email: Optional[str] = None
    username: Optional[str] = None
    is_active: bool = True
    roles: List[str] = []  # For future role-based access control


class UserCreate(BaseModel):
    """User creation model for signup."""
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """User login credentials."""
    email: EmailStr
    password: str


class UserInDB(BaseModel):
    """User model as stored in database."""
    user_id: str
    username: str
    email: str
    hashed_password: str
    is_active: bool = True
    created_at: datetime
    roles: List[str] = []


class JWTToken(BaseModel):
    """JWT token response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenResponse(BaseModel):
    """Complete token response with access and refresh tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int
    user_id: str


class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""
    refresh_token: str


class UserResponse(BaseModel):
    """User response model (without sensitive data)."""
    user_id: str
    username: str
    email: str
    is_active: bool
    created_at: datetime
    roles: List[str] = []
