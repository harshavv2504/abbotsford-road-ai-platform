"""
Flow State Detector

What it does:
- Detects user's state/intent during qualification flow
- Identifies if user wants to exit, refuse contact, ask questions, etc.
"""

from typing import Dict, List, Optional
import json
from app.services.llm_service import llm_service
from app.utils.logger import logger


class FlowDetector:
    """Detects user flow state during qualification"""
    
    def __init__(self):
        self.llm_service = llm_service
    
    async def detect_flow_state(self, user_message: str, conversation_history: List[Dict], current_field: Optional[str] = None) -> Dict:
        """
        Detect user's state/intent during qualification flow
        
        Returns:
            Dict with flow_state and reasoning
        """
        # Get last bot message for context
        last_bot_message = ""
        if conversation_history:
            for msg in reversed(conversation_history):
                if 'bot' in msg:
                    last_bot_message = msg['bot']
                    break
        
        # Build context
        context = "\n".join([
            f"{'User' if 'user' in msg else 'Bot'}: {msg.get('user') or msg.get('bot')}"
            for msg in conversation_history[-3:]
        ])
        
        field_context = f"\nCurrent field being asked: {current_field}" if current_field else ""
        
        prompt = f"""Analyze the user's response to determine their state/intent during the qualification flow.

CONVERSATION CONTEXT:
{context}

LAST BOT MESSAGE:
{last_bot_message}
{field_context}

CURRENT USER MESSAGE:
{user_message}

FLOW STATES:

1. continuing - User is cooperating, providing information normally
   Examples: "In 6 months", "Bold coffee", "John Smith", "Yes", "No" (as valid answers)

2. wants_to_exit - User wants to stop the qualification entirely
   Examples: "Stop", "I don't want to do this", "Not interested", "Cancel", "Forget it"

3. refuses_contact_info - User doesn't want to provide phone/email (ONLY when asked for contact info)
   Examples: "I don't want to give my number", "I'm not comfortable sharing that", "No thanks" (when asked for phone/email)
   NOTE: "No" to other questions (like "do you need training?") is NOT refusal, it's "continuing"

4. asking_question - User is asking a question instead of answering
   Examples: "What is this for?", "Why do you need this?", "What coffee do you offer?"

NOTE: "wants_to_talk_to_person" and "wants_to_place_order" are detected by customer type detector, not here.

IMPORTANT CONTEXT AWARENESS:
- "No" to "What's your phone?" = refuses_contact_info
- "No" to "Do you need training?" = continuing (valid answer)
- "I don't need that" to preference questions = continuing (valid answer)
- Consider what was asked in the last bot message!

RESPOND WITH JSON:
{{
    "flow_state": "continuing" | "wants_to_exit" | "refuses_contact_info" | "asking_question",
    "reasoning": "Brief explanation of why this state was detected"
}}"""

        try:
            response = await self.llm_service.generate_response(
                messages=[{"role": "user", "content": prompt}],
                system_instruction="You are a helpful assistant that detects user flow states. Always respond with valid JSON.",
                temperature=0.0,
                max_tokens=200
            )
            
            result = json.loads(response["content"])
            logger.info(f"Flow state detected: {result['flow_state']} - {result['reasoning']}")
            return result
            
        except Exception as e:
            logger.error(f"Flow state detection failed: {e}")
            return {"flow_state": "continuing", "reasoning": "Detection failed, assuming continuing"}


# Singleton instance
flow_detector = FlowDetector()
