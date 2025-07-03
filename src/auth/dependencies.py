"""
FastAPI dependencies for authentication and user access.
"""

from fastapi import Depends, Request, HTTPException, status
from typing import Annotated

from .middleware import get_user_id_from_request
from .jwt_auth import get_current_user, JWTBearer
from .models import User


# JWT Bearer dependency
jwt_bearer = JWTBearer()


def get_authenticated_user_id(request: Request) -> str:
    """
    Dependency to get user_id from authenticated request.
    
    Use this instead of user_id query parameters.
    """
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        # If authentication is disabled and no user_id is set,
        # extract from JWT token manually if provided
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
            from .jwt_auth import extract_user_id_from_token
            user_id = extract_user_id_from_token(token)
            if user_id:
                return user_id
        
        # Fall back to a default user for testing/development
        # In production, this should raise an exception
        from src.config.settings import settings
        if not getattr(settings, 'jwt_require_auth', True):
            return "test_user_123"  # Default user for development
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )
    return user_id


async def get_authenticated_user(token: str = Depends(jwt_bearer)) -> User:
    """
    Dependency to get full user object from JWT token.
    """
    return await get_current_user(token)


async def get_current_user_dependency(token: str = Depends(jwt_bearer)) -> User:
    """
    Async dependency to get current user from JWT token.
    This is the recommended dependency for protected endpoints.
    """
    return await get_current_user(token)


# Type annotations for easier use
AuthenticatedUserId = Annotated[str, Depends(get_authenticated_user_id)]
AuthenticatedUser = Annotated[User, Depends(get_authenticated_user)]
CurrentUser = Annotated[User, Depends(get_current_user_dependency)]
