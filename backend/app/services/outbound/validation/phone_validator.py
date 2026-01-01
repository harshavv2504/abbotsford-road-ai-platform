"""
Phone Validator

What it does:
- Validates and formats phone numbers
- Smart country detection from message and phone format
- Provides country clarification prompts
"""

from typing import Dict, Optional
import random
from app.utils.validators import (
    validate_phone,
    extract_country_from_text,
    detect_country_from_phone,
    get_smart_validation_feedback
)
from app.utils.logger import logger


class PhoneValidator:
    """Phone number validation with smart country detection"""
    
    @staticmethod
    def validate_and_format_phone(
        phone: str, 
        country: Optional[str] = None,
        user_message: Optional[str] = None
    ) -> Dict:
        """
        Validate and format phone number with smart country detection
        
        Args:
            phone: Phone number to validate
            country: Country code (optional, will be detected if not provided)
            user_message: Original user message for country detection
        
        Returns:
            Dict with success, formatted_phone, country, and error message
        """
        # Smart country detection
        detected_country = None
        
        # Try to detect from message first
        if user_message:
            detected_country = extract_country_from_text(user_message)
            if detected_country:
                logger.info(f"Detected country from message: {detected_country} (message: {user_message})")
        
        # Try to detect from phone number itself
        if not detected_country:
            detected_country = detect_country_from_phone(phone)
            if detected_country:
                logger.info(f"Detected country from phone format: {detected_country}")
        
        # Priority: detected country > provided country > default US
        country_to_use = detected_country or country or "US"
        
        logger.info(f"Phone validation: phone={phone}, provided_country={country}, detected={detected_country}, using={country_to_use}")
        
        # Validate phone number
        is_valid, formatted, final_country = validate_phone(phone, country_to_use)
        
        if not is_valid:
            logger.info(f"Invalid phone number: {phone} for country {country_to_use}")
            error_message = get_smart_validation_feedback("phone", phone)
            
            return {
                "success": False,
                "error": error_message,
                "formatted_phone": None,
                "country": None
            }
        
        logger.info(f"Validated phone: {formatted} (country: {final_country})")
        return {
            "success": True,
            "formatted_phone": formatted,
            "country": final_country,
            "error": None
        }
    
    @staticmethod
    def needs_country_clarification(phone: str, user_message: str) -> bool:
        """
        Check if phone number needs country clarification
        
        Args:
            phone: Phone number
            user_message: User's message
        
        Returns:
            True if country clarification needed
        """
        country_from_phone = detect_country_from_phone(phone)
        country_from_message = extract_country_from_text(user_message)
        
        # If no country detected and phone looks local (no +), need clarification
        if not country_from_phone and not country_from_message and not phone.startswith("+"):
            return True
        
        return False
    
    @staticmethod
    def get_country_prompt() -> str:
        """Get a friendly prompt asking for country"""
        prompts = [
            "Got it! What country is this number from?",
            "Perfect! Which country is that number in?",
            "Thanks! What country should I use for this number?",
            "Awesome! What country is this for?",
        ]
        return random.choice(prompts)


# Singleton instance
phone_validator = PhoneValidator()
