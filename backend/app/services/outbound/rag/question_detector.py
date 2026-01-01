"""
Question Detector

What it does:
- Detects if a message is a question using rules and LLM
- Provides question intent detection
- Checks if user is answering vs asking
"""

from typing import Tuple, Dict
import json
from app.services.llm_service import llm_service
from app.services.outbound.rag.question_rules import question_rules
from app.utils.logger import logger


class QuestionDetector:
    """Detects questions using rules and LLM"""
    
    def __init__(self):
        self.llm_service = llm_service
        self.rules = question_rules
        
        # Define question intent detection function
        self.question_intent_function_def = [
            {
                "type": "function",
                "function": {
                    "name": "detect_question_intent",
                    "description": "Determine if the user's message is asking a question (seeking information) or providing an answer/statement.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "is_question": {
                                "type": "boolean",
                                "description": "True if user is asking a question or seeking information, False if answering or making a statement"
                            },
                            "confidence": {
                                "type": "string",
                                "enum": ["high", "medium", "low"],
                                "description": "Confidence level in the detection"
                            },
                            "reasoning": {
                                "type": "string",
                                "description": "Brief explanation of why this was classified as question or answer"
                            }
                        },
                        "required": ["is_question", "confidence", "reasoning"]
                    }
                }
            }
        ]
    
    def is_rag_question(self, message: str) -> bool:
        """
        Detect if message is a question using rule-based approach
        
        Args:
            message: User's message
        
        Returns:
            True if message appears to be a question
        """
        return self.rules.is_question(message)
    
    def detect_question_intent(self, message: str, last_bot_message: str = "") -> Tuple[bool, str]:
        """
        Centralized question intent detection using fast rules only
        Returns (is_question, 'rules')
        """
        is_question = self.is_rag_question(message)
        return (is_question, 'rules')
    
    async def detect_question_intent_with_llm(
        self,
        user_message: str,
        last_bot_message: str = ""
    ) -> Dict:
        """
        Use LLM to detect if user is asking a question or providing an answer
        
        Args:
            user_message: User's current message
            last_bot_message: Bot's last message for context
        
        Returns:
            Dict with is_question, confidence, and reasoning
        """
        context = f"Bot just asked: {last_bot_message}\n\n" if last_bot_message else ""
        
        prompt = f"""{context}User's message: "{user_message}"

Is the user ASKING A QUESTION (seeking information) or PROVIDING AN ANSWER/STATEMENT?

Examples of QUESTIONS:
- "What coffee do you offer?"
- "How much does it cost?"
- "Do you have organic options?"
- "Tell me about your training"

Examples of ANSWERS/STATEMENTS:
- "In 6 months" (answering timeline)
- "Bold coffee" (answering preference)
- "Yes" or "No" (answering a question)
- "I need training" (stating a need)
- "John Smith" (providing name)

Context matters! If bot asked "What's your timeline?", then "In 6 months" is an ANSWER, not a question."""

        try:
            response = await self.llm_service.generate_response(
                messages=[{"role": "user", "content": prompt}],
                tools=self.question_intent_function_def,
                tool_choice={"type": "function", "function": {"name": "detect_question_intent"}},
                temperature=0.0,
                max_tokens=150
            )
            
            if response.get("type") == "function_call":
                result = json.loads(response["function_args"])
                logger.info(f"Question intent (LLM): {result['is_question']} - {result['reasoning']}")
                return result
            else:
                logger.warning("LLM did not call question intent function")
                return {
                    "is_question": self.is_rag_question(user_message),
                    "confidence": "low",
                    "reasoning": "LLM detection failed, using rules"
                }
                
        except Exception as e:
            logger.error(f"Question intent detection failed: {e}")
            return {
                "is_question": self.is_rag_question(user_message),
                "confidence": "low",
                "reasoning": f"Error: {str(e)}"
            }
    
    def is_answering_current_field(
        self,
        user_message: str,
        last_bot_message: str,
        current_field: str = None
    ) -> bool:
        """
        Check if user is answering the current field question
        
        Args:
            user_message: User's message
            last_bot_message: Bot's last message
            current_field: Current field being asked
        
        Returns:
            True if user appears to be answering the current field
        """
        return self.rules.is_answering_field(user_message, last_bot_message, current_field)


# Singleton instance
question_detector = QuestionDetector()
