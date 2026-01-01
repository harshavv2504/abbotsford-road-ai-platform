"""
Fallback Extractor

What it does:
- Provides regex/heuristic-based extraction when LLM fails
- Context-aware extraction based on bot's last question
- Keyword-based field detection
"""

from typing import Dict, List
from app.utils.validators import extract_phone_from_text, extract_email_from_text
from app.utils.logger import logger


class FallbackExtractor:
    """Fallback extraction using regex and heuristics"""
    
    def extract_fields_fallback(
        self,
        user_message: str,
        last_bot_message: str,
        customer_type: str,
        missing_fields: List[str]
    ) -> Dict:
        """
        Fallback extraction based on what bot just asked for
        
        Args:
            user_message: User's message
            last_bot_message: Bot's last message
            customer_type: "new_cafe" or "existing_cafe"
            missing_fields: List of fields still needed
        
        Returns:
            Dict with extracted field (if any)
        """
        if not last_bot_message or not missing_fields:
            return {}
        
        bot_lower = last_bot_message.lower()
        next_field = missing_fields[0]
        
        # Map of keywords to fields
        field_keywords = {
            "timeline": ["when", "timeline", "planning to open", "planning"],
            "coffee_style": ["coffee style", "style", "bold", "classic", "specialty", "coffee"],
            "equipment": ["equipment", "machine", "gear", "have"],
            "volume": ["volume", "cups", "daily", "serve", "many"],
            "current_pain_points": ["pain", "issue", "problem", "frustrat", "experiencing"],
            "cafe_count": ["how many", "locations", "cafés", "café"],
            "support_needs": ["support", "help", "need"],
            "current_coffee_style": ["current", "currently", "serve now", "offering now"],
            "coffee_preference": ["exploring", "try different", "other styles", "interested in"],
            "name": ["name", "call you", "who"],
            "phone": ["phone", "number"],
            "email": ["email"]
        }
        
        # Check if bot asked for the next missing field
        if next_field in field_keywords:
            keywords = field_keywords[next_field]
            if any(keyword in bot_lower for keyword in keywords):
                value = user_message.strip()
                logger.info(f"Fallback extracted {next_field}: {value}")
                return {next_field: value}
        
        return {}


# Singleton instance
fallback_extractor = FallbackExtractor()
