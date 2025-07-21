"""
HIPAA-compliant patient ID utilities.

This module provides utilities for generating and managing HIPAA-compliant patient IDs
that are used throughout the MediTwin system for data isolation and privacy protection.
"""

import hashlib
import hmac
import secrets
import string
from typing import Optional

from src.config.settings import settings
from src.utils.logging import logger


class PatientIdManager:
    """
    Manager for HIPAA-compliant patient ID generation and validation.
    
    Ensures patient IDs are:
    - De-identified and cannot be traced back to user IDs
    - Consistent across sessions for the same user
    - Unique for each user
    - HIPAA compliant for medical data storage
    """
    
    def __init__(self):
        self.salt = settings.patient_id_salt
        
    def generate_patient_id_from_user_id(self, user_id: str) -> str:
        """
        Generate a HIPAA-compliant patient ID from a user ID.
        
        Args:
            user_id: Original user identifier from login service
            
        Returns:
            HIPAA-compliant patient ID (deterministic for same user_id)
        """
        if not user_id:
            raise ValueError("user_id cannot be empty")
        
        # Create deterministic patient ID using HMAC-SHA256
        # This ensures same user_id always generates same patient_id
        patient_id_hash = hmac.new(
            key=self.salt.encode('utf-8'),
            msg=user_id.encode('utf-8'),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        # Create a more readable patient ID format: PT_<first16chars>
        patient_id = f"PT_{patient_id_hash[:16].upper()}"
        
        logger.debug(f"Generated patient_id for user (length: {len(user_id)})")
        return patient_id
    
    def validate_patient_id_format(self, patient_id: str) -> bool:
        """
        Validate that a patient ID follows the expected format.
        
        Args:
            patient_id: Patient ID to validate
            
        Returns:
            True if valid format, False otherwise
        """
        if not patient_id:
            return False
            
        # Expected format: PT_<16_hex_chars>
        if not patient_id.startswith("PT_"):
            return False
            
        if len(patient_id) != 19:  # PT_ + 16 chars
            return False
            
        hex_part = patient_id[3:]
        return all(c in string.hexdigits.upper() for c in hex_part)
    
    def is_test_patient_id(self, patient_id: str) -> bool:
        """
        Check if a patient ID is a test/development ID.
        
        Args:
            patient_id: Patient ID to check
            
        Returns:
            True if it's a test patient ID
        """
        test_patterns = [
            "PT_TEST",
            "PT_DEV",
            "PT_DEMO",
            "test_user",
            "demo_user"
        ]
        
        return any(pattern in patient_id.upper() for pattern in test_patterns)
    
    def anonymize_for_logging(self, patient_id: str) -> str:
        """
        Create a safe version of patient ID for logging (HIPAA compliant).
        
        Args:
            patient_id: Full patient ID
            
        Returns:
            Anonymized version safe for logs
        """
        if not patient_id:
            return "EMPTY_PATIENT_ID"
            
        if self.is_test_patient_id(patient_id):
            return patient_id  # Test IDs can be logged as-is
            
        # For real patient IDs, only show prefix and length
        return f"PT_***[{len(patient_id)}]"


# Global instance
patient_id_manager = PatientIdManager()


def get_patient_id_from_user_id(user_id: str) -> str:
    """
    Convenience function to get patient ID from user ID.
    
    Args:
        user_id: User identifier from authentication
        
    Returns:
        HIPAA-compliant patient ID
    """
    return patient_id_manager.generate_patient_id_from_user_id(user_id)


def validate_patient_id(patient_id: str) -> bool:
    """
    Convenience function to validate patient ID format.
    
    Args:
        patient_id: Patient ID to validate
        
    Returns:
        True if valid format
    """
    return patient_id_manager.validate_patient_id_format(patient_id)


def anonymize_patient_id_for_logs(patient_id: str) -> str:
    """
    Convenience function to anonymize patient ID for logging.
    
    Args:
        patient_id: Patient ID to anonymize
        
    Returns:
        Safe version for logs
    """
    return patient_id_manager.anonymize_for_logging(patient_id)


def hash_patient_id_for_storage(patient_id: str, additional_salt: Optional[str] = None) -> str:
    """
    Hash patient ID for database storage with additional isolation.
    
    This creates an additional layer of hashing for database storage,
    ensuring even if the database is compromised, patient IDs remain protected.
    
    Args:
        patient_id: HIPAA-compliant patient ID
        additional_salt: Additional salt for this specific storage system
        
    Returns:
        Hashed patient ID for storage
    """
    if not patient_id:
        raise ValueError("patient_id cannot be empty")
    
    # Use additional salt if provided, otherwise use the main salt
    salt = additional_salt or settings.patient_id_salt
    
    storage_hash = hmac.new(
        key=salt.encode('utf-8'),
        msg=patient_id.encode('utf-8'),
        digestmod=hashlib.sha256
    ).hexdigest()
    
    return storage_hash
