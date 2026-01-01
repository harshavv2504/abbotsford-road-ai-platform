"""
Bot Business Logic (outbound)

DEPRECATED: This file is now a backward-compatible wrapper.
The actual implementation has been modularized into the business/ directory:
- business/new_cafe_qualifier.py - New cafe qualification
- business/existing_cafe_qualifier.py - Existing cafe qualification

What it does:
- Validates end-of-qualification field sets and returns qualification outcomes/errors
- Pure business rules, separate from conversation flow

If you change it:
- You adjust qualification requirements and error reporting
"""

from typing import Dict
from app.services.outbound.business import new_cafe_qualifier, existing_cafe_qualifier


class OutboundBotBusinessLogic:
    """Business rules and logic for outbound chatbot"""
    
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
        return new_cafe_qualifier.qualify_new_cafe_customer(
            timeline, coffee_style, equipment, volume, name, phone, email, phone_needs_review
        )
    
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
        return existing_cafe_qualifier.qualify_existing_cafe_customer(
            current_pain_points, cafe_count, support_needs, current_coffee_style,
            coffee_preference, name, phone, email, phone_needs_review
        )


# Singleton instance
outbound_bot_business_logic = OutboundBotBusinessLogic()
