"""
User initialization middleware for MediTwin.
Automatically initializes Neo4j graph with patient node + 30 body parts
when a user first interacts with the system.
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from src.utils.logging import logger
from src.db.neo4j_db import get_graph
from src.auth.dependencies import get_authenticated_user_id
import asyncio


class UserInitializationMiddleware(BaseHTTPMiddleware):
    """
    Middleware that automatically initializes user graphs when needed.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.initialized_users = set()  # In-memory cache to avoid repeated checks
    
    async def dispatch(self, request: Request, call_next):
        # Only process authenticated requests
        try:
            # Skip initialization for certain paths
            skip_paths = [
                "/docs", "/redoc", "/openapi.json", "/favicon.ico",
                "/auth/", "/health", "/metrics"
            ]
            
            if any(request.url.path.startswith(path) for path in skip_paths):
                return await call_next(request)
            
            # Get user ID from request
            user_id = None
            
            # Try to get user_id from request state (set by auth middleware)
            if hasattr(request.state, 'user_id'):
                user_id = request.state.user_id
            else:
                # Try to extract from Authorization header
                auth_header = request.headers.get("Authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header.split(" ", 1)[1]
                    from src.auth.jwt_auth import extract_user_id_from_token
                    user_id = extract_user_id_from_token(token)
            
            # Initialize user if needed
            if user_id and user_id not in self.initialized_users:
                try:
                    neo4j_client = get_graph()
                    if not neo4j_client.is_user_initialized(user_id):
                        logger.info(f"Initializing user graph for user {user_id[:8]}...")
                        success = neo4j_client.initialize_user_graph(user_id)
                        if success:
                            logger.info(f"User graph initialized successfully for {user_id[:8]}...")
                        else:
                            logger.warning(f"Failed to initialize user graph for {user_id[:8]}...")
                    
                    # Cache the initialization to avoid repeated checks
                    self.initialized_users.add(user_id)
                    
                except Exception as e:
                    logger.error(f"Error during user initialization: {e}")
                    # Don't fail the request, just log the error
            
        except Exception as e:
            logger.error(f"Error in user initialization middleware: {e}")
            # Don't fail the request, continue processing
        
        # Continue with the request
        return await call_next(request)
