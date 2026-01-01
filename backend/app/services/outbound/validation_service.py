"""
Validation Service (outbound)

DEPRECATED: This file is now a backward-compatible wrapper.
The actual implementation has been modularized into the validation/ directory:
- validation/phone_validator.py - Phone validation
- validation/email_validator.py - Email validation
- validation/field_validator.py - Field validation

What it does:
- Validates and normalizes fields like phone, email, and domain-specific values
- Provides user-facing clarification/error prompts

If you change it:
- You change data quality and user prompts for corrections
"""

from typing import Dict, Optional
from app.services.outbound.validation import phone_validator, email_validator, field_validator


class ValidationService:
    """Centralized validation service for all field types"""
    
    def __init__(self):
        self.phone_validator = phone_validator
        self.email_validator = email_validator
        self.field_validator = field_validator
    
    @staticmethod
    def validate_and_format_phone(
        phone: str, 
        country: Optional[str] = None,
        user_message: Optional[str] = None
    ) -> Dict:
        return phone_validator.validate_and_format_phone(phone, country, user_message)
    
    @staticmethod
    def validate_and_format_email(email: str) -> Dict:
        return email_validator.validate_and_format_email(email)
    
    @staticmethod
    def validate_name(name: str) -> Dict:
        return field_validator.validate_name(name)
    
    @staticmethod
    def is_vague_pain_point(pain_point: str) -> bool:
        return field_validator.is_vague_pain_point(pain_point)
    
    @staticmethod
    def get_clarification_prompt(field_name: str, vague_value: str) -> str:
        return field_validator.get_clarification_prompt(field_name, vague_value)
    
    @staticmethod
    def needs_country_clarification(phone: str, user_message: str) -> bool:
        return phone_validator.needs_country_clarification(phone, user_message)
    
    @staticmethod
    def get_country_prompt() -> str:
        return phone_validator.get_country_prompt()


# Singleton instance
validation_service = ValidationService()
