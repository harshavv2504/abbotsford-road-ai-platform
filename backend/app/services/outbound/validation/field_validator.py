"""
Field Validator

What it does:
- Validates name fields
- Checks for vague pain points
- Provides clarification prompts
"""

from typing import Dict
import random
from app.utils.logger import logger


class FieldValidator:
    """General field validation"""
    
    @staticmethod
    def validate_name(name: str) -> Dict:
        """
        Validate name field
        
        Args:
            name: Name to validate
        
        Returns:
            Dict with success, cleaned_name, and error message
        """
        # Skip if it's just a pronoun or too short
        if name.lower() in ["i'm", "i am", "my", "me", "i"]:
            logger.info(f"Skipping invalid name: {name}")
            return {
                "success": False,
                "error": "Could you share your full name?",
                "cleaned_name": None
            }
        
        # Clean up name prefixes
        name_lower = name.lower()
        prefixes_to_remove = [
            "my name is ", "my name's ", "i'm ", "i am ", 
            "call me ", "it's ", "this is ", "name is "
        ]
        
        cleaned = name
        for prefix in prefixes_to_remove:
            if name_lower.startswith(prefix):
                cleaned = name[len(prefix):].strip()
                break
        
        # Final validation - name should be at least 2 chars
        if len(cleaned) < 2 or cleaned.lower() in ["i'm", "i am", "my", "me", "i"]:
            logger.info(f"Skipping invalid name after cleanup: {cleaned}")
            return {
                "success": False,
                "error": "Could you share your full name?",
                "cleaned_name": None
            }
        
        logger.info(f"Validated name: {cleaned}")
        return {
            "success": True,
            "cleaned_name": cleaned,
            "error": None
        }
    
    @staticmethod
    def is_vague_pain_point(pain_point: str) -> bool:
        """
        Check if pain point is too vague and needs clarification
        
        Args:
            pain_point: Pain point text to check
        
        Returns:
            True if vague, False if specific enough
        """
        pain_point_lower = pain_point.lower().strip()
        
        # Valid "no issues" responses - NOT vague
        no_issues_responses = [
            "no_supplier_issues", "satisfied_with_supplier", "no_problems", 
            "no_issues", "satisfied_with_current", "supplier_is_fine"
        ]
        
        if pain_point_lower in no_issues_responses:
            return False
        
        # Vague phrases that don't actually describe the problem
        # NOTE: "looking for new supplier" is NOT vague - it's a valid opening statement
        # We'll ask about specifics later in the flow naturally
        vague_phrases = [
            "few problems", "some problems", "some issues", "few issues",
            "problems", "issues", "not happy", "not satisfied", "not good",
            "bad", "terrible", "awful", "not great", "could be better"
        ]
        
        if pain_point_lower in vague_phrases:
            return True
        
        # Check if it's very short (less than 3 words) and contains vague words
        word_count = len(pain_point.split())
        if word_count < 3:
            vague_words = ["problem", "issue", "bad", "not", "some", "few"]
            if any(word in pain_point_lower for word in vague_words):
                return True
        
        # Check if it starts with vague phrases
        vague_starters = [
            "i have few", "i have some", "there are few", "there are some",
            "got few", "got some"
        ]
        if any(pain_point_lower.startswith(starter) for starter in vague_starters):
            return True
        
        return False
    
    @staticmethod
    def get_clarification_prompt(field_name: str, vague_value: str) -> str:
        """
        Get a friendly clarification prompt for vague responses
        
        Args:
            field_name: Name of the field that needs clarification
            vague_value: The vague value provided
        
        Returns:
            Friendly clarification prompt
        """
        if field_name == "current_pain_points":
            prompts = [
                "I hear you! Can you tell me specifically what's not working? Like delivery issues, quality problems, or something else?",
                "Got it! What specifically is the issue—late deliveries, inconsistent quality, poor support?",
                "I understand! What exactly is frustrating you—is it the coffee quality, service, pricing?",
                "Makes sense! Can you be more specific? Like what's the main thing that's driving you crazy?",
                "I get it! What's the biggest issue—delivery, quality, support, or something else?"
            ]
            return random.choice(prompts)
        
        return f"Could you tell me a bit more about that? I want to make sure I understand correctly."


# Singleton instance
field_validator = FieldValidator()
