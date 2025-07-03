"""
Authentication middleware for automatic JWT token processing.
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable

from src.auth.jwt_auth import extract_user_id_from_token, verify_token
from src.utils.logging import logger


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """
    JWT Authentication middleware that automatically extracts user_id from tokens.
    
    This middleware:
    1. Checks for Authorization header with Bearer token
    2. Verifies the JWT token
    3. Extracts user_id and adds it to request state
    4. Allows endpoints to access user_id without manual token parsing
    """
    
    # Endpoints that don't require authentication
    EXEMPT_PATHS = {
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json"
    }
    
    def __init__(self, app, require_auth: bool = True):
        super().__init__(app)
        self.require_auth = require_auth
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Skip authentication for exempt paths
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)
        
        # Skip authentication for OPTIONS requests (CORS)
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Extract Authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            if self.require_auth:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Authorization header required"}
                )
            else:
                # Continue without authentication
                return await call_next(request)
        
        # Parse Bearer token
        try:
            scheme, token = auth_header.split(" ", 1)
            if scheme.lower() != "bearer":
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid authentication scheme"}
                )
        except ValueError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid Authorization header format"}
            )
        
        # Verify token
        if not verify_token(token):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or expired token"}
            )
        
        # Extract user_id
        user_id = extract_user_id_from_token(token)
        if not user_id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid token: user_id not found"}
            )
        
        # Add user information to request state
        request.state.user_id = user_id
        request.state.token = token
        
        # Log authenticated request
        logger.debug(f"Authenticated request for user {user_id[:8]}... to {request.url.path}")
        
        return await call_next(request)


def get_user_id_from_request(request: Request) -> str:
    """
    Extract user_id from authenticated request.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User ID string
        
    Raises:
        HTTPException: If user not authenticated
    """
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )
    return user_id
