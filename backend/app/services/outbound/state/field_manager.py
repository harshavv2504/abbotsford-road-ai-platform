"""
Field Manager Mixin

What it does:
- Manages field tracking (required, preferred, missing, collected)
- Handles field completion logic
- Provides field access methods
"""

from typing import List, Optional
from app.utils.logger import logger


class FieldManagerMixin:
    """Mixin for field management methods"""
    
    def get_required_fields(self, customer_type: str) -> List[str]:
        """Get required fields to display in UI/context (excludes OR contacts)"""
        if customer_type in ["new_cafe", "existing_cafe"]:
            return ["name"]
        return []
    
    def get_preferred_fields(self, customer_type: str) -> List[str]:
        """Get list of PREFERRED fields (nice to have, but not required)"""
        if customer_type == "new_cafe":
            return ["timeline", "coffee_style", "equipment", "volume"]
        elif customer_type == "existing_cafe":
            return ["current_pain_points", "cafe_count", "support_needs", "current_coffee_style", "coffee_preference"]
        return []
    
    def get_all_fields(self, customer_type: str) -> List[str]:
        """Get list of all fields (required + preferred)"""
        required = self.get_required_fields(customer_type)
        preferred = self.get_preferred_fields(customer_type)
        return required + preferred
    
    def get_collected_fields(self, customer_type: str) -> List[str]:
        """Get list of fields that have been collected"""
        required = self.get_required_fields(customer_type)
        return [f for f in required if getattr(self, f, None)]
    
    def get_missing_fields(self, customer_type: str) -> List[str]:
        """Get list of fields still needed (name first, then preferred, then contact info last)"""
        required = self.get_required_fields(customer_type)
        preferred = self.get_preferred_fields(customer_type)
        
        # Separate name from contact fields
        name_missing = [] if self.name else ["name"]
        phone_missing = [] if self.phone else ["phone"]
        email_missing = [] if self.email else ["email"]
        
        # If user has skipped 2+ preferred fields, skip all remaining preferred fields
        MAX_PREFERRED_SKIPS = 2
        if self.skipped_preferred_count >= MAX_PREFERRED_SKIPS:
            logger.info(f"⏭️  User skipped {self.skipped_preferred_count} preferred fields - skipping all remaining preferred fields")
            # Auto-mark all remaining preferred fields as "to_be_discussed"
            for field in preferred:
                if not getattr(self, field, None):
                    self.set_field(field, "to_be_discussed_with_team")
            # Return: name first, then contact info
            return name_missing + phone_missing + email_missing
        
        # Otherwise, return: name first, then preferred, then contact info (phone/email) last
        missing_preferred = [f for f in preferred if not getattr(self, f, None)]
        
        # NEW ORDER: name → preferred fields → phone/email (build rapport before asking contact)
        return name_missing + missing_preferred + phone_missing + email_missing
    
    def is_complete(self, customer_type: str) -> bool:
        """Check if MINIMUM required fields are collected (name + phone OR email)"""
        has_name = bool(self.name)
        has_phone = bool(self.phone)
        has_email = bool(self.email)
        has_contact = has_phone or has_email
        
        return has_name and has_contact
    
    def has_all_preferred_fields(self, customer_type: str) -> bool:
        """Check if all preferred fields are collected"""
        all_fields = self.get_all_fields(customer_type)
        missing = [f for f in all_fields if not getattr(self, f, None)]
        return len(missing) == 0
    
    def set_field(self, field_name: str, value: str) -> None:
        """Set a field value with validation"""
        if hasattr(self, field_name):
            setattr(self, field_name, value)
        else:
            raise ValueError(f"Invalid field name: {field_name}")
    
    def get_field(self, field_name: str) -> Optional[str]:
        """Get a field value"""
        return getattr(self, field_name, None)
    
    def is_skippable_field(self, field: str) -> bool:
        """Check if a field is skippable (preferred fields are skippable)"""
        return field in self.get_preferred_fields(self.customer_type or "")
    
    def is_preferred_field(self, field: str) -> bool:
        """Check if a field is a preferred field"""
        return field in self.get_preferred_fields(self.customer_type or "")
    
    def format_for_display(self, field_name: str, field_value: str) -> str:
        """Format field value for display (replace underscores with spaces, capitalize)"""
        if not field_value:
            return ""
        
        # Replace underscores with spaces
        formatted = field_value.replace("_", " ")
        
        # Capitalize first letter of each word for better readability
        formatted = formatted.title()
        
        return formatted
