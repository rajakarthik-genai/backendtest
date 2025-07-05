"""
JWT token validation utilities for the MediTwin backend.

This module handles JWT token verification and user extraction from tokens
issued by the external login service. It does NOT handle user registration,
login, or password management - those are handled by the separate login service.
"""

import jwt
from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException, Request, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.config.settings import settings
from src.utils.logging import logger
from .models import User, TokenData


class JWTBearer(HTTPBearer):
    """
    JWT Bearer token authentication for FastAPI.
    
    Extracts and verifies JWT tokens from Authorization headers.
    """
    
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
    
    async def __call__(self, request: Request) -> Optional[str]:
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        
        if credentials:
            if not credentials.scheme == "Bearer":
                if self.auto_error:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Invalid authentication scheme"
                    )
                return None
            
            token = credentials.credentials
            if not verify_token(token):
                if self.auto_error:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Invalid or expired token"
                    )
                return None
            
            return token
        
        if self.auto_error:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Authorization header required"
            )
        return None


def verify_token(token: str) -> bool:
    """
    Verify JWT token signature and expiration.
    
    Args:
        token: JWT token string
        
    Returns:
        True if token is valid, False otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        # Check expiration
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            return False
        
        # Check required fields (user_id for new format, sub for standard)
        user_id = payload.get("user_id") or payload.get("sub")
        if not user_id:
            return False
        
        return True
        
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return False
    except Exception as e:
        logger.error(f"JWT verification error: {e}")
        return False


def decode_token(token: str) -> Optional[TokenData]:
    """
    Decode JWT token and extract user data.
    
    Args:
        token: JWT token string
        
    Returns:
        TokenData object or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        # Support both user_id (legacy) and sub (standard) formats
        user_id = payload.get("user_id") or payload.get("sub")
        
        return TokenData(
            sub=user_id,
            email=payload.get("email"),
            username=payload.get("username"),
            exp=datetime.fromtimestamp(payload.get("exp", 0), tz=timezone.utc) if payload.get("exp") else None,
            iat=datetime.fromtimestamp(payload.get("iat", 0), tz=timezone.utc) if payload.get("iat") else None,
            token_type=payload.get("type", "access")
        )
        
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None
    except Exception as e:
        logger.error(f"JWT decode error: {e}")
        return None


async def get_current_user(token: str = Depends(JWTBearer())) -> User:
    """
    Extract current user from JWT token.
    
    Args:
        token: JWT token string (from JWTBearer dependency)
        
    Returns:
        User object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token required"
        )
    
    token_data = decode_token(token)
    if not token_data or not token_data.sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    # Create user object from token data
    user = User(
        user_id=token_data.sub,
        email=token_data.email,
        username=token_data.username,
        is_active=True,  # Assume active if token is valid
        roles=[]  # Could be extracted from token if needed
    )
    
    logger.debug(f"Authenticated user: {token_data.sub[:8]}...")
    return user


def extract_user_id_from_token(token: str) -> Optional[str]:
    """
    Extract user_id from JWT token without full validation.
    
    Args:
        token: JWT token string
        
    Returns:
        User ID string or None if not found
    """
    try:
        # Decode without verification for user_id extraction
        payload = jwt.decode(token, options={"verify_signature": False})
        # Support both user_id (legacy) and sub (standard) formats
        user_id = payload.get("user_id") or payload.get("sub")
        logger.debug(f"Extracted user_id from token: {user_id[:8] if user_id else 'None'}...")
        return user_id
    except Exception as e:
        logger.error(f"Failed to extract user_id from token: {e}")
        return None
