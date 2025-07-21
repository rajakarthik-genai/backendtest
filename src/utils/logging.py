"""
Central logging configuration used across the backend.

Features:
- INFO level by default, DEBUG if settings.debug is True
- Structured format with timestamps
- User-friendly console output
- HIPAA-compliant (no PII in logs)
"""

import logging
import sys
import time
from typing import Any, Dict
from fastapi import Request, Response

from src.config.settings import settings

# Set logging level based on debug setting
_level = logging.DEBUG if settings.debug else logging.INFO

# Configure root logger
logging.basicConfig(
    level=_level,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    stream=sys.stdout,
)

# Create main application logger
logger = logging.getLogger("meditwin")

# Suppress verbose third-party loggers
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("pymongo").setLevel(logging.WARNING)
logging.getLogger("neo4j").setLevel(logging.WARNING)

logger.info("Logging initialized (level=%s)", logging.getLevelName(_level))


def sanitize_log_data(data: Any) -> Any:
    """
    Sanitize data for logging to ensure no PII/PHI is logged.
    
    Args:
        data: Data to sanitize (dict, list, str, etc.)
        
    Returns:
        Sanitized data safe for logging
    """
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            key_lower = key.lower()
            
            # Skip potential PII fields
            if any(pii_field in key_lower for pii_field in [
                'name', 'email', 'phone', 'address', 'ssn', 'dob', 
                'birth', 'patient_id', 'user_id', 'password', 'token'
            ]):
                sanitized[key] = f"<{key.upper()}_REDACTED>"
            else:
                sanitized[key] = sanitize_log_data(value)
        return sanitized
    
    elif isinstance(data, list):
        return [sanitize_log_data(item) for item in data]
    
    elif isinstance(data, str):
        # Truncate very long strings
        if len(data) > 500:
            return data[:497] + "..."
        return data
    
    else:
        return data


def log_user_action(user_id: str, action: str, details: Dict[str, Any] = None):
    """
    Log user action with sanitized details.
    
    Args:
        user_id: User identifier (will be masked)
        action: Action description
        details: Additional details to log (will be sanitized)
    """
    masked_user_id = f"user_{user_id[:8]}..." if user_id else "unknown"
    sanitized_details = sanitize_log_data(details) if details else {}
    
    logger.info(
        "User action: %s | User: %s | Details: %s",
        action,
        masked_user_id,
        sanitized_details
    )


def log_system_event(event: str, metadata: Dict[str, Any] = None):
    """
    Log system event with metadata.
    
    Args:
        event: Event description
        metadata: Event metadata (will be sanitized)
    """
    sanitized_metadata = sanitize_log_data(metadata) if metadata else {}
    
    logger.info(
        "System event: %s | Metadata: %s",
        event,
        sanitized_metadata
    )


def log_request(request: Request, response: Response = None, duration: float = None):
    """
    Log HTTP request details in a HIPAA-compliant manner.
    
    Args:
        request: FastAPI request object
        response: FastAPI response object (optional)
        duration: Request duration in seconds (optional)
    """
    # Extract request details
    method = request.method
    url = str(request.url)
    
    # Sanitize URL - remove potential PII from query params
    url_path = request.url.path
    query_params = dict(request.query_params)
    sanitized_params = sanitize_log_data(query_params)
    
    # Log request details
    log_data = {
        "method": method,
        "path": url_path,
        "query_params": sanitized_params,
        "user_agent": request.headers.get("user-agent", "unknown"),
        "content_type": request.headers.get("content-type", "unknown"),
    }
    
    if response:
        log_data["status_code"] = response.status_code
        log_data["response_size"] = response.headers.get("content-length", "unknown")
    
    if duration:
        log_data["duration_ms"] = round(duration * 1000, 2)
    
    # Determine log level based on status code
    if response and response.status_code >= 500:
        logger.error("API Request: %s", log_data)
    elif response and response.status_code >= 400:
        logger.warning("API Request: %s", log_data)
    else:
        logger.info("API Request: %s", log_data)


def log_openai_request(endpoint: str, model: str, tokens_used: int = None, duration: float = None):
    """
    Log OpenAI API requests for monitoring and debugging.
    
    Args:
        endpoint: OpenAI endpoint called
        model: Model used
        tokens_used: Number of tokens consumed (optional)
        duration: Request duration in seconds (optional)
    """
    log_data = {
        "service": "openai",
        "endpoint": endpoint,
        "model": model,
    }
    
    if tokens_used:
        log_data["tokens_used"] = tokens_used
    
    if duration:
        log_data["duration_ms"] = round(duration * 1000, 2)
    
    logger.info("OpenAI Request: %s", log_data)


def log_database_operation(database: str, operation: str, collection: str = None, duration: float = None):
    """
    Log database operations for monitoring.
    
    Args:
        database: Database type (mongo, neo4j, milvus, redis)
        operation: Operation type (read, write, update, delete)
        collection: Collection/table name (optional)
        duration: Operation duration in seconds (optional)
    """
    log_data = {
        "database": database,
        "operation": operation,
    }
    
    if collection:
        log_data["collection"] = collection
    
    if duration:
        log_data["duration_ms"] = round(duration * 1000, 2)
    
    logger.info("DB Operation: %s", log_data)
