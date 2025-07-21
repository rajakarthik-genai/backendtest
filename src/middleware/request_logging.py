"""
Request logging middleware for FastAPI to track all API calls.
"""

import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable

from src.utils.logging import log_request, logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests and responses.
    
    Features:
    - Logs request method, path, query parameters
    - Logs response status code and duration
    - HIPAA-compliant (sanitizes PII data)
    - Configurable log levels based on response status
    """
    
    def __init__(self, app, log_requests: bool = True):
        super().__init__(app)
        self.log_requests = log_requests
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Process request and log details."""
        if not self.log_requests:
            return await call_next(request)
        
        # Record start time
        start_time = time.time()
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log request details
            log_request(request, response, duration)
            
            return response
            
        except Exception as e:
            # Log failed requests
            duration = time.time() - start_time
            logger.error(
                "Request failed: %s %s | Duration: %.2fms | Error: %s",
                request.method,
                request.url.path,
                duration * 1000,
                str(e)
            )
            raise
