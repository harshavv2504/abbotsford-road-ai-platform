from typing import Dict

"""
Bot Functions (outbound)

What it does:
- Declares function-callable tools exposed to the LLM during response generation (tool definitions and
  handlers), used by `response_builder`.

If you change it:
- You change which tools the LLM can call and their schemas. Keep inputs/outputs consistent and validate
  rigorously to avoid malformed tool calls.
"""
from app.services.outbound.bot_business_logic import outbound_bot_business_logic


class OutboundBotFunctions:
    """Bot-specific functions for outbound chatbot"""
    
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
        Qualify a new café customer
        
        Returns:
            Dict with success status or error message
        """
        result = outbound_bot_business_logic.qualify_new_cafe_customer(
            timeline=timeline,
            coffee_style=coffee_style,
            equipment=equipment,
            volume=volume,
            name=name,
            phone=phone,
            email=email,
            phone_needs_review=phone_needs_review
        )
        
        return result
    
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
        
        Returns:
            Dict with success status or error message
        """
        result = outbound_bot_business_logic.qualify_existing_cafe_customer(
            current_pain_points=current_pain_points,
            cafe_count=cafe_count,
            support_needs=support_needs,
            current_coffee_style=current_coffee_style,
            coffee_preference=coffee_preference,
            name=name,
            phone=phone,
            email=email,
            phone_needs_review=phone_needs_review
        )
        
        return result


# Function definitions for OpenAI function calling
# No OpenAI functions - we handle everything with state tracking
OUTBOUND_FUNCTION_DEFINITIONS = []


# Singleton instance
outbound_bot_functions = OutboundBotFunctions()
