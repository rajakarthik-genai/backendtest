"""
Shared dependencies for API endpoints with JWT authentication and patient_id extraction
"""

import logging
from typing import Dict, Any, Optional
from fastapi import Depends, HTTPException, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime

from src.core.config import settings
from src.core.exceptions import AuthenticationError, AuthorizationError
from src.db.mongodb import get_database
from src.db.neo4j import neo4j_connection
from src.db.redis_client import get_redis_client
from src.auth.jwt_auth import extract_patient_id_from_token, verify_token, extract_user_id_from_token
from src.utils.patient_id import get_patient_id_from_user_id

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()


async def get_current_user(
    request: Request
) -> Dict[str, Any]:
    """
    Extract current user information from JWT token in request headers
    Automatically extracts patient_id from user_id for HIPAA compliance
    """
    try:
        # Extract user_id from request state (set by middleware)
        user_id = getattr(request.state, "user_id", None)
        if not user_id:
            # Fallback: extract from Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise AuthenticationError("Missing or invalid authorization header")
            
            token = auth_header.split(" ", 1)[1]
            user_id = extract_user_id_from_token(token)
            if not user_id:
                raise AuthenticationError("Invalid token: user_id not found")
        
        # Convert user_id to HIPAA-compliant patient_id
        patient_id = get_patient_id_from_user_id(user_id)
        
        # Extract additional token data if available
        auth_header = request.headers.get("Authorization")
        is_provider = False
        email = None
        username = None
        
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
            try:
                payload = jwt.decode(
                    token,
                    settings.JWT_SECRET_KEY,
                    algorithms=[settings.JWT_ALGORITHM]
                )
                is_provider = payload.get("is_provider", False)
                email = payload.get("email")
                username = payload.get("username")
            except:
                pass
        
        return {
            "user_id": user_id,
            "patient_id": patient_id,
            "is_provider": is_provider,
            "email": email,
            "username": username
        }
        
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token expired")
    except jwt.PyJWTError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise AuthenticationError("Authentication failed")


async def get_current_patient(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> str:
    """
    Get current patient ID from JWT token, ensuring HIPAA-compliant patient_id
    """
    return current_user["patient_id"]


async def get_provider_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Ensure current user is a healthcare provider
    """
    if not current_user.get("is_provider"):
        raise AuthorizationError("Provider access required")
    
    return current_user


async def get_db_clients() -> Dict[str, Any]:
    """
    Get all database client instances
    """
    try:
        mongodb = get_database()
        redis = await get_redis_client()
        
        return {
            "mongodb": mongodb,
            "neo4j": neo4j_connection,
            "redis": redis
        }
        
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=503, detail="Database connection failed")


async def verify_patient_access(
    patient_id: str,
    current_user: Dict[str, Any]
):
    """
    Verify if current user has access to patient data using patient_id from JWT
    """
    if not current_user.get("is_provider", False):
        # Regular users can only access their own data
        if patient_id != current_user.get("patient_id"):
            raise AuthorizationError("Access denied to this patient data")
    # Providers can access any patient data
    return current_user.get("patient_id") == patient_id


async def get_authenticated_patient_id(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> str:
    """
    Dependency to get authenticated patient ID
    """
    return current_user["patient_id"]


async def require_patient_access(
    patient_id: str = Depends(get_authenticated_patient_id),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Dependency to ensure user has access to specific patient using patient_id from JWT
    """
    await verify_patient_access(patient_id, current_user)
    return patient_id


# Rate limiting dependency
async def check_rate_limit(
    user_id: str,
    endpoint: str,
    redis = Depends(get_redis_client)
) -> bool:
    """
    Check rate limiting for user and endpoint
    """
    try:
        # Create rate limit keys
        minute_key = f"rate_limit:{user_id}:{endpoint}:minute"
        hour_key = f"rate_limit:{user_id}:{endpoint}:hour"
        
        # Get current counts
        minute_count = await redis.get(minute_key) or 0
        hour_count = await redis.get(hour_key) or 0
        
        # Check limits
        if int(minute_count) >= settings.RATE_LIMIT_PER_SECOND * 60:
            raise HTTPException(status_code=429, detail="Rate limit exceeded (per minute)")
        
        if int(hour_count) >= settings.RATE_LIMIT_PER_HOUR:
            raise HTTPException(status_code=429, detail="Rate limit exceeded (per hour)")
        
        # Increment counters
        await redis.set(minute_key, int(minute_count) + 1, ttl=60)
        await redis.set(hour_key, int(hour_count) + 1, ttl=3600)
        
        return True
        
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Rate limiting check failed: {e}")
        return True  # Allow request if rate limiting fails


# Optional authentication for public endpoints
async def get_optional_user(
    authorization: Optional[str] = Header(None)
) -> Optional[Dict[str, Any]]:
    """
    Optional authentication - returns None if no token provided
    """
    if not authorization:
        return None
    
    try:
        # Extract token from Bearer header
        if not authorization.startswith("Bearer "):
            return None
        
        token = authorization.split(" ")[1]
        
        # Decode token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        return {
            "user_id": user_id,
            "patient_id": payload.get("patient_id"),
            "is_provider": payload.get("is_provider", False)
        }
        
    except Exception:
        return None


# Pagination dependency
class PaginationParams:
    def __init__(self, skip: int = 0, limit: int = 50):
        self.skip = max(0, skip)
        self.limit = min(100, max(1, limit))  # Max 100 items per page


def get_pagination_params(skip: int = 0, limit: int = 50) -> PaginationParams:
    """Get pagination parameters with validation"""
    return PaginationParams(skip, limit)
