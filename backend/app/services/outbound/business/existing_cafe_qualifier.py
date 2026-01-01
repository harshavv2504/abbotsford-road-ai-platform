"""
Existing Cafe Qualifier

What it does:
- Validates qualification for existing café customers
- Checks all required fields
- Validates phone and email
"""

from typing import Dict
from app.utils.validators import validate_phone, validate_email
from app.utils.logger import logger


class ExistingCafeQualifier:
    """Qualification logic for existing café customers"""
    
    @staticmethod
    def qualify_existing_cafe_customer(
        current_pain_points: str,
        cafe_count: str,
        support_needs: str,
        current_coffee_style: str,
        coffee_preference: str,
        name: str,
        phone: str,
        email: str,
        phone_needs_review: bool = False
    ) -> Dict:
        """
        Qualify an existing café customer looking for a new supplier
        
        Args:
            current_pain_points: Issues with current supplier
            cafe_count: Number of cafés they operate
            support_needs: What support they need
            current_coffee_style: Current coffee style they serve
            coffee_preference: Interest in exploring other coffee styles
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
        if not current_pain_points or not current_pain_points.strip():
            missing_fields.append("current_pain_points")
        else:
            collected_fields.append("current_pain_points")
        
        if not cafe_count or not cafe_count.strip():
            missing_fields.append("cafe_count")
        else:
            collected_fields.append("cafe_count")
        
        if not support_needs or not support_needs.strip():
            missing_fields.append("support_needs")
        else:
            collected_fields.append("support_needs")
        
        if not current_coffee_style or not current_coffee_style.strip():
            missing_fields.append("current_coffee_style")
        else:
            collected_fields.append("current_coffee_style")
        
        if not coffee_preference or not coffee_preference.strip():
            missing_fields.append("coffee_preference")
        else:
            collected_fields.append("coffee_preference")
        
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
            "message": "Existing café customer qualified successfully",
            "missing_fields": [],
            "collected_fields": collected_fields,
            "data": {
                "current_pain_points": current_pain_points.strip(),
                "cafe_count": cafe_count.strip(),
                "support_needs": support_needs.strip(),
                "current_coffee_style": current_coffee_style.strip(),
                "coffee_preference": coffee_preference.strip(),
                "name": name.strip(),
                "phone": formatted_phone,
                "email": normalized_email,
                "phone_needs_review": phone_needs_review
            }
        }


# Singleton instance
existing_cafe_qualifier = ExistingCafeQualifier()
