"""
Question Generator

Generates natural questions for field collection with variations.
"""

import random
from typing import Optional

"""
Question Generator (outbound)

What it does:
- Provides the next best question for a given field and customer type, and clarifying prompts when user
  responses are vague or ambiguous.

If you change it:
- You shape the conversation’s micro-prompts during qualification. Keep messages short and aligned with
  persona; changes here affect the bot’s questioning style.
"""
from app.services.outbound.state_manager import ConversationState


class QuestionGenerator:
    """Generates natural questions for collecting customer information"""
    
    def __init__(self):
        # Define question variations for each field
        self.question_variations = {
            "timeline": [
                "When are you thinking of opening your café?",
                "When are you planning to open?",
                "Do you have an opening date in mind?",
                "How soon are you planning to launch?",
                "When do you aim to get started?"
            ],
            "coffee_style": [
                "What flavor profile are you looking for—bold and strong, or something lighter?",
                "Are you thinking bold and punchy, or more smooth and balanced?",
                "What is your preferred coffee style? Dark and intense or lighter and nuanced?",
                "Do you prefer a bold roast or something lighter?",
                "What kind of coffee profile interests you—strong and bold or smooth and classic?"
            ],
            "equipment": [
                "Do you have any café equipment already, or are you starting completely from scratch?",
                "What is your equipment situation—do you have some gear, or need everything?",
                "Do you have any equipment lined up, or are you starting fresh?",
                "Do you have machines and equipment sorted, or are you building from zero?",
                "Regarding equipment, do you have anything already, or are you starting from the ground up?"
            ],
            "volume": [
                "How many cups are you planning to sell daily—around 50, 100, 200, or more?",
                "What is your target daily volume? Thinking 50 cups, 100, 200+?",
                "How many cups per day are you aiming for—50, 100, 200, or higher?",
                "What kind of daily sales are you targeting—50 cups, 100, 200+?",
                "How many cups daily are you hoping to sell—around 50, 100, 200, or more?"
            ],
            "name": [
                "May I ask your name?",
                "Who am I speaking with?",
                "What should I call you?",
                "Great! What is your name?",
                "Excellent! Who am I chatting with?"
            ],
            "phone": [
                "What is the best number to reach you?",
                "What is a good phone number for you?",
                "What is the best number to call you at?",
                "How can we reach you by phone?",
                "What number works best for you?"
            ],
            "email": [
                "What is your email address?",
                "What is a good email for you?",
                "What is the best email to reach you at?",
                "Where should we send info—what is your email?",
                "What email works for you?"
            ],
            "current_pain_points": [
                "is your current supplier working well for you, or are you facing any issues?",
                "are you happy with your current coffee supplier, or having some problems?",
                "how's your current supplier—all good, or are there issues you're dealing with?",
                "is everything smooth with your current supplier, or are you running into problems?",
                "are you satisfied with your current supplier, or is something not working out?"
            ],
            "cafe_count": [
                "how many locations are you running?",
                "how many cafés do you have?",
                "are you running one spot or multiple locations?",
                "how many places are you operating?",
                "is this one café or do you have a few going?"
            ],
            "support_needs": [
                "do you need any other services—training, equipment help, or consulting?",
                "interested in additional services—staff training, machine service, marketing?",
                "looking for extra support—barista training, technical help, business guidance?",
                "want any other services—equipment maintenance, staff development, menu design?",
                "do you need additional support beyond coffee—like training programs, technical service, or operations help?"
            ],
            "current_coffee_style": [
                "what coffee style do you currently serve—bold, classic, or specialty?",
                "what's your current coffee offering—dark roast, medium, or specialty blends?",
                "what style of coffee are you serving now—bold and strong, balanced, or specialty?",
                "what kind of coffee do you offer right now—bold, classic blends, or specialty?",
                "what's your current coffee style—dark and bold, medium classic, or specialty single-origin?"
            ],
            "coffee_preference": [
                "interested in exploring other coffee styles, or happy with what you have?",
                "want to try different coffee styles, or stick with your current approach?",
                "thinking about adding new coffee styles, or staying with what works?",
                "looking to try other styles, or keeping what you serve now?",
                "interested in different coffee options, or sticking with your current style?"
            ],
            "phone": [
                "what's the best number to reach you?",
                "what's your phone number?",
                "how can we reach you by phone?"
            ],
            "email": [
                "what's your email?",
                "what's your email address?",
                "where should we send you info?"
            ]
        }
        
        # Clarification prompts for unclear responses
        self.clarifications = {
            "timeline": {
                "contextual": "when you say '{snippet}', thinking next few months, this year, or further out?",
                "fallback": "roughly when are you planning to open—next few months, this year, or later?"
            },
            "volume": {
                "contextual": "when you say '{snippet}', are we talking 50 cups daily, 100-200, or higher volume?",
                "fallback": "roughly how many cups of coffee daily—50, 100, 200, or more?",
                "business_context": "thinking small neighborhood café (50-100), busy office spot (200-300), or high-traffic location (400+)?"
            },
            "cafe_count": {
                "contextual": "when you say '{snippet}', is it one location, a few spots, or multiple?",
                "fallback": "how many locations—one café, a few, or multiple spots?"
            },
            "current_pain_points": {
                "contextual": "when you say '{snippet}', what specifically is the issue—delivery, quality, service, or pricing?",
                "fallback": "what specifically is frustrating you—late deliveries, quality issues, poor service, or something else?"
            },
            "support_needs": {
                "contextual": "when you say '{snippet}', are you thinking training, equipment help, or business support?",
                "fallback": "what kind of additional support—staff training, equipment service, or business guidance?"
            }
        }
    
    def get_field_question(self, field: str, customer_type: str, state: Optional[ConversationState] = None) -> str:
        """Get natural question for a field - with multiple variations"""
        variations = self.question_variations.get(field, ["can you tell me more about your café?"])
        return random.choice(variations)
    
    def get_clarification(self, field: str, user_message: str, state: ConversationState) -> Optional[str]:
        """Get clarification question for unclear field responses"""
        
        if field not in self.clarifications:
            # Field-specific fallbacks for better UX
            field_fallbacks = {
                "equipment": "do you have any café equipment already, or starting from scratch?",
                "coffee_style": "what kind of vibe are you going for—bold and strong, or something lighter?",
                "name": "what's your name?",
                "phone": "what's the best number to reach you?",
                "email": "what's your email?",
            }
            return field_fallbacks.get(field, "could you tell me a bit more about that?")
        
        # Get a snippet of what they actually said for context
        original_snippet = user_message[:30] + "..." if len(user_message) > 30 else user_message
        
        clarification_options = self.clarifications[field]
        
        # Special handling for volume - use business context for very uncertain responses
        if field == "volume" and any(uncertain in user_message.lower() for uncertain in ["no idea", "don't know", "not sure", "haven't thought", "figuring out"]):
            return clarification_options["business_context"]
        
        # Use contextual question if the original message isn't too long or generic
        if len(user_message) <= 50 and not any(generic in user_message.lower() for generic in ["not sure", "don't know", "unclear", "maybe"]):
            return clarification_options["contextual"].format(snippet=original_snippet)
        else:
            return clarification_options["fallback"]


# Singleton instance
question_generator = QuestionGenerator()
