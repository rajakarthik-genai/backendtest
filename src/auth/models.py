"""
Authentication models for JWT token validation.

This module contains only the models needed to validate JWT tokens 
issued by the external login service.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


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
