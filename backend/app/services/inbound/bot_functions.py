from typing import Dict, Any
from app.services.inbound.bot_business_logic import inbound_bot_business_logic


class InboundBotFunctions:
    """Bot-specific functions for inbound chatbot"""
    
    @staticmethod
    def end_chat(farewell_type: str = "general") -> Dict:
        """
        End the chat conversation with appropriate farewell
        
        Args:
            farewell_type: Type of farewell ("thanks", "general", "help")
        
        Returns:
            Dict with farewell message and end flag
        """
        result = inbound_bot_business_logic.prepare_farewell_message(farewell_type)
        
        return {
            "message": result["message"],
            "should_end": True,
            "farewell_type": result["farewell_type"]
        }
    
    @staticmethod
    def get_function_definitions() -> list:
        """Return function definitions for LLM function calling"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "confirm_ticket_creation",
                    "description": "Ask the customer if they want to create a support ticket for their issue. Use this when you've understood their problem and they need follow-up support.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "issue_summary": {
                                "type": "string",
                                "description": "Brief summary of the customer's issue"
                            },
                            "issue_details": {
                                "type": "string",
                                "description": "Detailed description of the problem including symptoms and impact"
                            }
                        },
                        "required": ["issue_summary", "issue_details"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "mark_ticket_needed",
                    "description": "Mark that a support ticket should be created for this conversation. Use this when customer confirms they want a ticket created.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "customer_confirmed": {
                                "type": "boolean",
                                "description": "Whether customer confirmed they want a ticket"
                            }
                        },
                        "required": ["customer_confirmed"]
                    }
                }
            }
        ]
    
    @staticmethod
    def get_ticket_classification_definition() -> list:
        """Return function definition for ticket response classification"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "classify_ticket_response",
                    "description": "Classify the customer's response when asked if they want a support ticket created.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "response_type": {
                                "type": "string",
                                "enum": ["CONFIRMING", "DECLINING", "UNCLEAR"],
                                "description": "CONFIRMING: agreeing to ticket (yes, sure, go ahead). DECLINING: refusing or postponing (no, not now, later). UNCLEAR: asking unrelated questions or giving unclear response."
                            },
                            "reasoning": {
                                "type": "string",
                                "description": "Brief explanation of why the user declined or if they are switching topics (e.g., 'User wants to buy beans instead', 'User says issue is resolved', 'User wants to try troubleshooting first')."
                            },
                            "new_topic": {
                                "type": "string",
                                "enum": ["sales", "troubleshooting", "general_info", "none"],
                                "description": "If user is switching topics, what is the new topic? 'sales' (buying products), 'troubleshooting' (trying more steps), 'general_info' (asking questions), or 'none'."
                            }
                        },
                        "required": ["response_type", "reasoning"]
                    }
                }
            }
        ]
    
    @staticmethod
    def confirm_ticket_creation(issue_summary: str, issue_details: str) -> Dict[str, Any]:
        """Ask customer if they want to create a ticket"""
        return {
            "action": "ask_confirmation",
            "issue_summary": issue_summary,
            "issue_details": issue_details,
            "message": f"I understand you're experiencing: {issue_summary}. Would you like me to create a support ticket so our team can help resolve this?"
        }
    
    @staticmethod
    def mark_ticket_needed(customer_confirmed: bool) -> Dict[str, Any]:
        """Mark that ticket should be created"""
        if customer_confirmed:
            return {
                "action": "ticket_confirmed",
                "create_ticket": True,
                "message": "Perfect! I'll make sure a support ticket is created for you. You'll receive an email confirmation shortly, and our team will reach out to resolve this as soon as possible."
            }
        else:
            return {
                "action": "ticket_declined",
                "create_ticket": False,
                "message": "No problem! Let me know if you need anything else or if you change your mind."
            }


# Singleton instance
inbound_bot_functions = InboundBotFunctions()
