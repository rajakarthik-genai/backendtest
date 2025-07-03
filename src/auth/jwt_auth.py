"""
JWT authentication utilities for the MediTwin backend.

Handles JWT token verification, user extraction, and refresh token management.
"""

import jwt
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Set
from fastapi import HTTPException, Request, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext

from src.config.settings import settings
from src.utils.logging import logger
from .models import User, TokenData, TokenResponse

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory store for active refresh tokens (use Redis/DB in production)
active_refresh_tokens: Set[str] = set()


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


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def verify_token(token: str, token_type: str = "access") -> bool:
    """
    Verify JWT token signature and expiration.
    
    Args:
        token: JWT token string
        token_type: Type of token ('access' or 'refresh')
        
    Returns:
        True if token is valid, False otherwise
    """
    try:
        # Use different secret for refresh tokens if available
        secret_key = settings.jwt_secret_key
        if token_type == "refresh" and hasattr(settings, 'jwt_refresh_secret_key'):
            secret_key = settings.jwt_refresh_secret_key
        
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        # Check token type if specified in payload
        if payload.get("type") and payload.get("type") != token_type:
            logger.warning(f"Token type mismatch: expected {token_type}, got {payload.get('type')}")
            return False
        
        # Check expiration
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            return False
        
        # Check required fields (user_id for new format, sub for standard)
        user_id = payload.get("user_id") or payload.get("sub")
        if not user_id:
            return False
        
        # For refresh tokens, check if it's in active store
        if token_type == "refresh" and token not in active_refresh_tokens:
            logger.warning("Refresh token not in active store")
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


def extract_user_id_from_token(token: str, token_type: str = "access") -> Optional[str]:
    """
    Extract user_id from JWT token without full validation.
    
    Args:
        token: JWT token string
        token_type: Type of token ('access' or 'refresh')
        
    Returns:
        User ID string or None if not found
    """
    try:
        # Decode without verification for user_id extraction
        payload = jwt.decode(token, options={"verify_signature": False})
        # Support both user_id (legacy) and sub (standard) formats
        user_id = payload.get("user_id") or payload.get("sub")
        logger.debug(f"Extracted user_id from {token_type} token: {user_id[:8] if user_id else 'None'}...")
        return user_id
    except Exception as e:
        logger.error(f"Failed to extract user_id from token: {e}")
        return None


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token with user data.
    
    Args:
        data: Token payload data (should include 'sub' with user_id)
        expires_delta: Custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    })
    
    token = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    logger.debug(f"Created access token for user: {data.get('sub', 'unknown')[:8]}...")
    return token


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT refresh token.
    
    Args:
        data: Token payload data (should include 'sub' with user_id)
        expires_delta: Custom expiration time
        
    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh"
    })
    
    # Use refresh secret if available, otherwise use main secret
    secret_key = getattr(settings, 'jwt_refresh_secret_key', settings.jwt_secret_key)
    token = jwt.encode(to_encode, secret_key, algorithm=settings.jwt_algorithm)
    
    # Store refresh token (in production, use Redis or database)
    active_refresh_tokens.add(token)
    logger.debug(f"Created refresh token for user: {data.get('sub', 'unknown')[:8]}...")
    return token


def verify_refresh_token(token: str) -> Optional[str]:
    """
    Verify refresh token and return user_id.
    
    Args:
        token: Refresh token string
        
    Returns:
        User ID if valid, None otherwise
    """
    if not verify_token(token, "refresh"):
        return None
    
    return extract_user_id_from_token(token, "refresh")


def create_token_response(user_id: str, email: str = None, username: str = None) -> TokenResponse:
    """
    Create a complete token response with access and refresh tokens.
    
    Args:
        user_id: User ID to include in token
        email: User email (optional)
        username: Username (optional)
    
    Returns:
        TokenResponse with both tokens
    """
    # Create token payload
    token_data = {
        "sub": user_id,
        "email": email,
        "username": username
    }
    
    # Create both tokens
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": user_id})  # Refresh token only needs user_id
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,  # Convert to seconds
        refresh_expires_in=settings.refresh_token_expire_days * 24 * 60 * 60,  # Convert to seconds
        user_id=user_id
    )


def invalidate_refresh_token(token: str) -> bool:
    """
    Invalidate a refresh token by removing it from active store.
    
    Args:
        token: Refresh token to invalidate
    
    Returns:
        True if token was found and removed, False otherwise
    """
    try:
        active_refresh_tokens.discard(token)
        logger.info("Refresh token invalidated")
        return True
    except Exception as e:
        logger.error(f"Error invalidating refresh token: {e}")
        return False


def refresh_access_token(refresh_token: str) -> Optional[str]:
    """
    Create a new access token using a valid refresh token.
    
    Args:
        refresh_token: Valid refresh token
    
    Returns:
        New access token string if successful, None otherwise
    """
    user_id = verify_refresh_token(refresh_token)
    if not user_id:
        return None
    
    # Create new access token
    new_access_token = create_access_token({"sub": user_id})
    logger.info(f"Access token refreshed for user: {user_id[:8]}...")
    return new_access_token
