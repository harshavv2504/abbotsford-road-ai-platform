"""
New Cafe Qualifier

What it does:
- Validates qualification for new café customers
- Checks all required fields
- Validates phone and email
"""

from typing import Dict
from app.utils.validators import validate_phone, validate_email
from app.utils.logger import logger


class NewCafeQualifier:
    """Qualification logic for new café customers"""
    
    @staticmethod
    def qualify_new_cafe_customer(
        timeline: str,
        coffee_style: str,
        equipment: str,
        volume: str,
        name: str,
        phone: str,
        email: str,
        phone_needs_review: bool = False
    ) -> Dict:
        """
        Qualify a new café customer by validating all required information
        
        Args:
            timeline: When they're opening the café
            coffee_style: Coffee preference
            equipment: Equipment situation
            volume: Expected daily coffee volume
            name: Contact name
            phone: Contact phone (REQUIRED)
            email: Contact email (OPTIONAL)
        
        Returns:
            Dict with success status, missing fields, or error message
        """
        missing_fields = []
        collected_fields = []
        validation_errors = {}
        
        # Check each field
        if not timeline or not timeline.strip():
            missing_fields.append("timeline")
        else:
            collected_fields.append("timeline")
        
        if not coffee_style or not coffee_style.strip():
            missing_fields.append("coffee_style")
        else:
            collected_fields.append("coffee_style")
        
        if not equipment or not equipment.strip():
            missing_fields.append("equipment")
        else:
            collected_fields.append("equipment")
        
        if not volume or not volume.strip():
            missing_fields.append("volume")
        else:
            collected_fields.append("volume")
        
        if not name or not name.strip():
            missing_fields.append("name")
        elif len(name.strip()) < 2:
            validation_errors["name"] = "Name must be at least 2 characters long"
        else:
            collected_fields.append("name")
        
        # Validate phone - REQUIRED
        formatted_phone = None
        if not phone or not phone.strip():
            missing_fields.append("phone")
        elif phone == "user_declined":
            # User explicitly declined to provide phone - this is acceptable if email is provided
            formatted_phone = "user_declined"
            collected_fields.append("phone")
        else:
            if phone.startswith("+") or phone_needs_review:
                formatted_phone = phone
                collected_fields.append("phone")
            else:
                is_valid_phone, formatted_phone, country = validate_phone(phone.strip())
                if not is_valid_phone:
                    validation_errors["phone"] = "Invalid phone number format"
                else:
                    collected_fields.append("phone")
        
        # Validate email - OPTIONAL
        normalized_email = None
        if email and email.strip() and email != "user_declined":
            is_valid_email, normalized_email, email_error = validate_email(email.strip())
            if not is_valid_email:
                validation_errors["email"] = f"Invalid email: {email_error}"
            else:
                collected_fields.append("email")
        elif email == "user_declined":
            # User explicitly declined to provide email - this is acceptable
            normalized_email = "user_declined"
            collected_fields.append("email")
        
        # If there are missing fields or validation errors, return them
        if missing_fields or validation_errors:
            return {
                "success": False,
                "missing_fields": missing_fields,
                "collected_fields": collected_fields,
                "validation_errors": validation_errors
            }
        
        # All validation passed
        return {
            "success": True,
            "message": "New café customer qualified successfully",
            "missing_fields": [],
            "collected_fields": collected_fields,
            "data": {
                "timeline": timeline.strip(),
                "coffee_style": coffee_style.strip(),
                "equipment": equipment.strip(),
                "volume": volume.strip(),
                "name": name.strip(),
                "phone": formatted_phone,
                "email": normalized_email,
                "phone_needs_review": phone_needs_review
            }
        }


# Singleton instance
new_cafe_qualifier = NewCafeQualifier()
