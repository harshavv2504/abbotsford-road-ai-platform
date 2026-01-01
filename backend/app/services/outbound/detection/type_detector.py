"""
Customer Type Detector

What it does:
- Detects if customer is opening a new café or owns existing café
- Uses LLM function calling with confidence levels
- Extracts contact information if provided
"""

from typing import Dict, List, Optional
import json
from app.services.llm_service import llm_service
from app.utils.logger import logger


class TypeDetector:
    """Detects customer type (new vs existing café)"""
    
    def __init__(self):
        self.llm_service = llm_service
        
        # Define intent detection function for OpenAI function calling
        self.intent_detection_function_def = [
            {
                "type": "function",
                "function": {
                    "name": "detect_customer_intent",
                    "description": "Determine if the user is planning to open a NEW café or already OWNS/OPERATES an existing café, AND detect early action intents (order/talk requests).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "customer_type": {
                                "type": "string",
                                "enum": ["new_cafe", "existing_cafe", "unclear"],
                                "description": "Customer type: 'new_cafe' (planning to open/start a new café), 'existing_cafe' (already owns/operates café(s)), or 'unclear' (not enough information)"
                            },
                            "confidence": {
                                "type": "string",
                                "enum": ["high", "medium", "low"],
                                "description": "Confidence level in the detection"
                            },
                            "reasoning": {
                                "type": "string",
                                "description": "Brief explanation of why this customer type was detected"
                            },
                            "wants_to_place_order": {
                                "type": "boolean",
                                "description": "True if user wants to place an order or request samples (e.g., 'I want to order', 'Can I get samples?', 'I'd like to buy'). False otherwise."
                            },
                            "wants_to_talk_to_person": {
                                "type": "boolean",
                                "description": "True if user wants to speak with a real person (e.g., 'Can I talk to someone?', 'Connect me with your team', 'I want to speak to a person'). False otherwise."
                            }
                        },
                        "required": ["customer_type", "confidence", "reasoning", "wants_to_place_order", "wants_to_talk_to_person"]
                    }
                }
            }
        ]
    
    async def detect_with_llm(
        self, 
        user_message: str, 
        conversation_history: List[Dict]
    ) -> Optional[Dict]:
        """Use LLM function calling to detect customer type (new vs existing café)"""
        
        # Build context from recent conversation
        context_messages = []
        for msg in conversation_history[-3:]:  # Last 3 messages for context
            if 'user' in msg:
                context_messages.append(f"User: {msg['user']}")
            elif 'bot' in msg:
                context_messages.append(f"Bot: {msg['bot']}")
        
        context_messages.append(f"User: {user_message}")
        conversation_context = "\n".join(context_messages)
        
        detection_prompt = f"""Analyze this conversation to determine if the user is:
1. Planning to OPEN A NEW CAFÉ (new_cafe)
2. Already OWNS/OPERATES an existing café (existing_cafe)
3. Unclear - not enough information

Conversation:
{conversation_context}

STRICT DETECTION RULES:

NEW CAFÉ (new_cafe) - ONLY if they explicitly state plans to OPEN/START:

HIGH CONFIDENCE - Explicit action intent:
- "I want to open a café", "I'm opening a café", "I'm planning to open"
- "going to open", "will open", "opening in [timeframe]"
- "starting a café", "launching a café", "I'm starting a new café business"

MEDIUM CONFIDENCE - Implied interest but not committed:
- "thinking of opening", "considering opening", "looking to open"
- "interested in opening", "might open", "exploring opening"

LOW CONFIDENCE - Vague or exploratory:
- "interested in cafés", "learning about café business"
- "tell me about opening a café" (just asking, not stating intent)

EXISTING CAFÉ (existing_cafe) - ONLY if they clearly OWN/OPERATE:

HIGH CONFIDENCE - Clear ownership/operation:
- "I own a café", "I run a café", "my café", "our café"
- "we operate X cafés", "we run X locations"
- "I'm a café owner", "we're café owners"
- "current supplier" (implies they have a café with a supplier)

MEDIUM CONFIDENCE - Implied ownership:
- "been in the café business", "operating for X years" (without explicit ownership)
- "looking for a new supplier" (implies ownership but not explicit)

LOW CONFIDENCE - Vague or exploratory:
- "interested in café supplies", "learning about suppliers"

UNCLEAR - Use this for:
- General questions: "tell me about coffee", "what do you offer", "what blends do you have"
- Pure information seeking: "how does delivery work", "what are your prices"
- Vague interest: "thinking about it", "considering", "might want to" (WITHOUT explicit mention of opening/owning)
- Ambiguous statements that don't clearly indicate new or existing

CONFIDENCE LEVELS - BE CONSERVATIVE:
- HIGH: ONLY explicit, unambiguous statements with clear action intent or ownership
  * Must include words like "I want", "I'm opening", "I own", "I run", "my café"
  * Clear commitment or current ownership
  
- MEDIUM: Implied interest or ownership but not explicitly committed
  * Words like "thinking of", "considering", "interested in", "looking to"
  * Indirect ownership signals
  
- LOW: Exploratory, vague, or just asking questions
  * General questions without stating intent
  * Information gathering phase

BE CONSERVATIVE - When in doubt, use MEDIUM or LOW.
Only use HIGH when the user has EXPLICITLY stated their intent to open a café or clearly owns one.
Prefer UNCLEAR over forcing a classification.

Detect the customer type with confidence level."""

        try:
            response = await self.llm_service.generate_response(
                messages=[{"role": "user", "content": detection_prompt}],
                tools=self.intent_detection_function_def,
                tool_choice={"type": "function", "function": {"name": "detect_customer_intent"}},
                temperature=0.0,
                max_tokens=200
            )
            
            if response.get("type") == "function_call":
                function_args = json.loads(response["function_args"])
                logger.info(f"LLM detected: {function_args['customer_type']} (confidence: {function_args['confidence']}, reason: {function_args['reasoning']})")
                return function_args
            else:
                logger.warning("LLM did not call intent detection function")
                return None
                
        except Exception as e:
            logger.error(f"LLM intent detection failed: {e}")
            return None


# Singleton instance
type_detector = TypeDetector()
