"""
Validation Module

Modularized validation with:
- Phone validation (phone_validator.py)
- Email validation (email_validator.py)
- Field validation (field_validator.py)
"""

from app.services.outbound.validation.phone_validator import PhoneValidator, phone_validator
from app.services.outbound.validation.email_validator import EmailValidator, email_validator
from app.services.outbound.validation.field_validator import FieldValidator, field_validator

__all__ = [
    'PhoneValidator',
    'EmailValidator',
    'FieldValidator',
    'phone_validator',
    'email_validator',
    'field_validator',
]
