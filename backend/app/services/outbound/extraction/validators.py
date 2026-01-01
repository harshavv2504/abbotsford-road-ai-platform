"""
Extraction Validators

What it does:
- Validates extracted data (email, phone, consistency checks)
- Detects refusals and human connection requests
- Checks for ambiguous inputs
"""

import re
from app.utils.logger import logger


class ExtractionValidators:
    """Validation utilities for extracted data"""
    
    @staticmethod
    def is_actual_email(text: str) -> bool:
        """Check if text is actual email address, not just preference"""
        if not text:
            return False
        
        # Reject preference words
        preference_words = ["email", "e-mail", "mail", "yes", "sure", "okay", "ok", "yep", "yeah"]
        if text.lower().strip() in preference_words:
            return False
        
        # Must contain @ symbol
        if "@" not in text:
            return False
        
        # Basic email pattern check
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return bool(re.match(email_pattern, text))
    
    @staticmethod
    def is_actual_phone(text: str) -> bool:
        """Check if text is actual phone number, not just preference"""
        if not text:
            return False
        
        # Reject preference words
        preference_words = ["phone", "call", "number", "mobile", "cell", "yes", "sure", "okay", "ok"]
        if text.lower().strip() in preference_words:
            return False
        
        # Must contain digits
        if not any(char.isdigit() for char in text):
            return False
        
        # Should have at least 7 digits for a valid phone
        digit_count = sum(1 for char in text if char.isdigit())
        return digit_count >= 7
    
    @staticmethod
    def detect_refusal(user_message: str) -> bool:
        """BUG-004 FIX: Detect if user is refusing to provide information"""
        refusal_patterns = [
            r"\bno\b", r"\bnope\b", r"\bnah\b",
            r"\bdon'?t want\b", r"\bwon'?t share\b", 
            r"\brefuse\b", r"\bnot comfortable\b",
            r"\bdon'?t have\b", r"\bi said no\b", 
            r"\balready said\b", r"\bstop asking\b",
            r"\bprivacy\b", r"\bpersonal\b",
            r"\bmay ?be no\b", r"\bmaybe not\b"
        ]
        message_lower = user_message.lower()
        is_refusal = any(re.search(pattern, message_lower) for pattern in refusal_patterns)
        
        if is_refusal:
            logger.info(f"⚠️ BUG-004 FIX: Refusal detected in message: '{user_message}'")
        
        return is_refusal
    
    @staticmethod
    def detect_human_connection_request(user_message: str) -> bool:
        """BUG-012 FIX: Detect if user wants to connect with a real person"""
        connection_patterns = [
            r"connect.*real person", r"connect.*person",
            r"talk.*human", r"talk.*person", r"talk.*someone",
            r"speak.*human", r"speak.*person", r"speak.*someone",
            r"real person", r"human agent", r"actual person",
            r"connect me", r"transfer.*human", r"escalate",
            r"talk.*real", r"speak.*real",
            r"can i.*person", r"want.*person"
        ]
        message_lower = user_message.lower()
        is_connection_request = any(re.search(pattern, message_lower) for pattern in connection_patterns)
        
        if is_connection_request:
            logger.info(f"🤝 BUG-012 FIX: Human connection request detected: '{user_message}'")
        
        return is_connection_request
    
    @staticmethod
    def validate_extraction_consistency(user_message: str, extracted_field: str, extracted_value: str) -> bool:
        """BUG-008 FIX: Validate that extracted value matches user's actual message"""
        if not extracted_value or not user_message:
            return True
        
        message_lower = user_message.lower()
        value_lower = extracted_value.lower().replace("_", " ")
        
        # For coffee_style, check if user's words are in the extracted value
        if extracted_field == "coffee_style":
            # Get key words from user message
            user_words = set(message_lower.split())
            value_words = set(value_lower.split())
            
            # Check for overlap - if no overlap, something is wrong
            if not user_words.intersection(value_words):
                logger.warning(f"⚠️ BUG-008 FIX: Extraction mismatch - User said '{user_message}' but extracted '{extracted_value}'")
                return False
        
        return True
    
    @staticmethod
    def is_ambiguous_number(user_message: str, expected_field: str) -> bool:
        """BUG-005 FIX: Detect if user provided ambiguous number that needs clarification"""
        stripped = user_message.strip()
        
        # Check if message is just a number (or number with decimal)
        if stripped.replace('.', '').replace(',', '').isdigit():
            # Just a number without context
            logger.info(f"⚠️ BUG-005 FIX: Ambiguous number detected: '{user_message}' for field '{expected_field}'")
            return True
        
        return False


# Singleton instance
extraction_validators = ExtractionValidators()
