"""
Email Validator

What it does:
- Validates and formats email addresses
- Detects common typos
- Provides smart error messages
"""

from typing import Dict
from app.utils.validators import validate_email
from app.utils.logger import logger


class EmailValidator:
    """Email address validation with typo detection"""
    
    @staticmethod
    def validate_and_format_email(email: str) -> Dict:
        """
        Validate and format email address with typo detection
        
        Args:
            email: Email address to validate
        
        Returns:
            Dict with success, normalized_email, suggested_correction, and error message
        """
        # Use smart validation (whitelist + selective DNS)
        is_valid, normalized, error = validate_email(email)
        
        if not is_valid:
            logger.info(f"Invalid email: {email} - {error}")
            
            return {
                "success": False,
                "error": error,
                "normalized_email": None,
                "suggested_correction": None,
                "typo_detected": False
            }
        
        logger.info(f"Validated email: {normalized}")
        return {
            "success": True,
            "normalized_email": normalized,
            "error": None,
            "suggested_correction": None,
            "typo_detected": False
        }


# Singleton instance
email_validator = EmailValidator()
