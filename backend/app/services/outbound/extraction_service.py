"""
Extraction Service (outbound)

DEPRECATED: This file is now a backward-compatible wrapper.
The actual implementation has been modularized into the extraction/ directory:
- extraction/validators.py - Validation helpers
- extraction/llm_extractor.py - LLM-based extraction
- extraction/fallback_extractor.py - Regex/heuristic fallbacks
- extraction/function_defs.py - Function definitions

What it does:
- Provides LLM function-calling and regex/heuristic fallbacks to extract structured fields from user text.

If you change it:
- You modify how raw text is parsed into fields before validation. Keep contracts stable for
  `core/extraction_pipeline.py`.
"""

from typing import Dict, List, Optional
from app.services.outbound.extraction import (
    extraction_validators,
    llm_extractor,
    fallback_extractor
)


class ExtractionService:
    """Service for extracting customer data from messages"""
    
    def __init__(self):
        self.validators = extraction_validators
        self.llm_extractor = llm_extractor
        self.fallback_extractor = fallback_extractor
        # Keep old attribute names for backward compatibility
        self.llm_service = llm_extractor.llm_service
        self.extraction_function_def = llm_extractor.extraction_function_def
    
    # Delegate validation methods
    def _is_actual_email(self, text: str) -> bool:
        return self.validators.is_actual_email(text)
    
    def _is_actual_phone(self, text: str) -> bool:
        return self.validators.is_actual_phone(text)
    
    def detect_refusal(self, user_message: str) -> bool:
        return self.validators.detect_refusal(user_message)
    
    def detect_human_connection_request(self, user_message: str) -> bool:
        return self.validators.detect_human_connection_request(user_message)
    
    def validate_extraction_consistency(self, user_message: str, extracted_field: str, extracted_value: str) -> bool:
        return self.validators.validate_extraction_consistency(user_message, extracted_field, extracted_value)
    
    def is_ambiguous_number(self, user_message: str, expected_field: str) -> bool:
        return self.validators.is_ambiguous_number(user_message, expected_field)
    
    # Delegate extraction methods
    async def extract_fields_with_llm(
        self, 
        user_message: str, 
        customer_type: str,
        conversation_history: Optional[List[Dict]] = None,
        state = None
    ) -> Dict:
        return await self.llm_extractor.extract_fields_with_llm(
            user_message, customer_type, conversation_history, state
        )
    
    def extract_fields_fallback(
        self,
        user_message: str,
        last_bot_message: str,
        customer_type: str,
        missing_fields: List[str]
    ) -> Dict:
        return self.fallback_extractor.extract_fields_fallback(
            user_message, last_bot_message, customer_type, missing_fields
        )


# Singleton instance
extraction_service = ExtractionService()
