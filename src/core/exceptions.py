"""
Custom exceptions for Medical Digital Twin API
"""

from fastapi import HTTPException
from typing import Optional, Dict, Any


class MedicalTwinException(HTTPException):
    """Base exception for Medical Twin API"""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code


class DocumentProcessingError(MedicalTwinException):
    """Document processing related errors"""
    
    def __init__(self, detail: str, headers: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=422,
            detail=detail,
            error_code="DOCUMENT_PROCESSING_ERROR",
            headers=headers
        )


class ExtractionError(MedicalTwinException):
    """Information extraction errors"""
    
    def __init__(self, detail: str, headers: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=500,
            detail=detail,
            error_code="EXTRACTION_ERROR",
            headers=headers
        )


class DatabaseConnectionError(MedicalTwinException):
    """Database connection errors"""
    
    def __init__(self, detail: str, headers: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=503,
            detail=detail,
            error_code="DATABASE_CONNECTION_ERROR",
            headers=headers
        )


class AuthenticationError(MedicalTwinException):
    """Authentication related errors"""
    
    def __init__(self, detail: str = "Authentication failed", headers: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=401,
            detail=detail,
            error_code="AUTHENTICATION_ERROR",
            headers=headers
        )


class AuthorizationError(MedicalTwinException):
    """Authorization related errors"""
    
    def __init__(self, detail: str = "Access denied", headers: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=403,
            detail=detail,
            error_code="AUTHORIZATION_ERROR",
            headers=headers
        )


class ValidationError(MedicalTwinException):
    """Data validation errors"""
    
    def __init__(self, detail: str, headers: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=400,
            detail=detail,
            error_code="VALIDATION_ERROR",
            headers=headers
        )


class ExternalServiceError(MedicalTwinException):
    """External service integration errors"""
    
    def __init__(self, detail: str, service_name: str, headers: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=502,
            detail=f"{service_name}: {detail}",
            error_code="EXTERNAL_SERVICE_ERROR",
            headers=headers
        )


class RateLimitError(MedicalTwinException):
    """Rate limiting errors"""
    
    def __init__(self, detail: str = "Rate limit exceeded", headers: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=429,
            detail=detail,
            error_code="RATE_LIMIT_ERROR",
            headers=headers
        )


class FileProcessingError(MedicalTwinException):
    """File processing errors"""
    
    def __init__(self, detail: str, headers: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=422,
            detail=detail,
            error_code="FILE_PROCESSING_ERROR",
            headers=headers
        )


class AIServiceError(MedicalTwinException):
    """AI service related errors"""
    
    def __init__(self, detail: str, headers: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=503,
            detail=detail,
            error_code="AI_SERVICE_ERROR",
            headers=headers
        )
