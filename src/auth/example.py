"""
Example of how to update API endpoints to use JWT authentication.

This shows the migration from query parameter user_id to JWT-based authentication.
"""

from fastapi import APIRouter, Request, Depends
from typing import List, Dict, Any

from src.auth.dependencies import AuthenticatedUserId, AuthenticatedUser
from src.auth.middleware import get_user_id_from_request
from src.auth.models import User
from src.utils.logging import logger, log_user_action

router = APIRouter(prefix="/example", tags=["authentication-example"])


# OLD WAY: Using query parameter (insecure)
@router.get("/old-way")
async def old_endpoint(user_id: str):
    """
    OLD: Using user_id as query parameter.
    This is insecure because user_id can be spoofed.
    """
    # Anyone can pass any user_id - not secure!
    return {"message": f"Hello user {user_id}", "method": "query_parameter"}


# NEW WAY 1: Using middleware (recommended)
@router.get("/new-way-middleware")
async def new_endpoint_middleware(request: Request):
    """
    NEW: Using JWT middleware to extract user_id.
    The middleware automatically verifies the JWT token and extracts user_id.
    """
    user_id = get_user_id_from_request(request)
    
    log_user_action(user_id, "api_access", {"endpoint": "/example/new-way-middleware"})
    
    return {
        "message": f"Hello authenticated user {user_id}",
        "method": "jwt_middleware",
        "secure": True
    }


# NEW WAY 2: Using dependency injection (also good)
@router.get("/new-way-dependency")
async def new_endpoint_dependency(user_id: AuthenticatedUserId):
    """
    NEW: Using dependency injection to get user_id.
    FastAPI automatically calls the dependency to extract user_id from JWT.
    """
    log_user_action(user_id, "api_access", {"endpoint": "/example/new-way-dependency"})
    
    return {
        "message": f"Hello authenticated user {user_id}",
        "method": "dependency_injection",
        "secure": True
    }


# NEW WAY 3: Getting full user object
@router.get("/new-way-full-user")
async def new_endpoint_full_user(user: AuthenticatedUser):
    """
    NEW: Getting full user object from JWT token.
    Provides access to user_id, email, username, etc.
    """
    log_user_action(user.user_id, "api_access", {
        "endpoint": "/example/new-way-full-user",
        "email": user.email
    })
    
    return {
        "message": f"Hello {user.username or user.email}",
        "user_id": user.user_id,
        "email": user.email,
        "method": "full_user_object",
        "secure": True
    }


# MIGRATION EXAMPLE: Supporting both old and new ways during transition
@router.get("/migration-example")
async def migration_endpoint(
    request: Request,
    user_id: str = None  # Optional query parameter for backward compatibility
):
    """
    MIGRATION: Supporting both JWT and query parameter during transition.
    Prioritizes JWT authentication but falls back to query parameter.
    """
    
    # Try to get user_id from JWT first
    try:
        jwt_user_id = get_user_id_from_request(request)
        auth_method = "jwt_token"
        secure = True
    except:
        # Fall back to query parameter
        if user_id:
            jwt_user_id = user_id
            auth_method = "query_parameter"
            secure = False
            logger.warning(f"Using insecure query parameter authentication for user {user_id}")
        else:
            return {"error": "Authentication required"}
    
    return {
        "user_id": jwt_user_id,
        "auth_method": auth_method,
        "secure": secure,
        "message": "This endpoint supports both authentication methods during migration"
    }
