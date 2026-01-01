"""
Response Builder

What it does:
- Generates the bot's natural-language reply by assembling context (via PromptComposer) and calling the LLM
  with the appropriate system instruction and tool definitions.

If you change it:
- You affect how final responses are produced. Keep this thin and delegate context/prompt assembly to
  `core/prompt_composer.py` to avoid duplication.
"""

from typing import Dict, List
from app.services.llm_service import llm_service
from app.services.rag.retriever import retriever
from app.services.outbound.rag_handler import rag_handler
from app.services.outbound.prompt_handler import outbound_prompt_handler
from app.services.outbound.bot_functions import OUTBOUND_FUNCTION_DEFINITIONS
from app.services.outbound.state_manager import ConversationState
from app.utils.logger import logger
from app.services.outbound.core.prompt_composer import PromptComposer


class ResponseBuilder:
    """Builds context and generates responses for outbound bot.

    Modify only when you need to change LLM call parameters or how context is stitched together.
    Keep persona/instruction logic in PromptComposer.
    """
    
    def __init__(self):
        self.llm_service = llm_service
        self.retriever = retriever
        self.prompt_handler = outbound_prompt_handler
        self.composer = PromptComposer()
    
    def build_message_history(self, conversation_history: List[Dict], current_message: str) -> List[Dict]:
        return self.composer.build_message_history(conversation_history, current_message)
    
    def build_context(
        self, 
        user_message: str, 
        state: ConversationState,
        is_question: bool
    ) -> List[str]:
        """Build context parts for LLM prompt"""
        return self.composer.build_context(user_message, state, is_question)
    
    async def generate_response(
        self,
        user_message: str,
        conversation_history: List[Dict],
        state: ConversationState,
        use_rag_instruction: bool = False,
        just_provided_contact: List[str] = None
    ) -> str:
        """Generate LLM response"""
        
        # Determine if this is a question (centralized)
        is_question, _ = rag_handler.detect_question_intent(user_message, conversation_history[-1]['bot'] if conversation_history and 'bot' in conversation_history[-1] else "")
        
        # Build context
        context_parts = self.build_context(user_message, state, is_question)
        
        # Add note about just-provided contact info (for acknowledgment)
        if just_provided_contact:
            context_parts.append(f"⚡ USER JUST PROVIDED: {', '.join(just_provided_contact)}")
            context_parts.append("   → Acknowledge this warmly in your response!")
            context_parts.append("")
        
        # Build formatted message
        if context_parts:
            formatted_message = "\n\n".join(context_parts) + f"\n\nUser: {user_message}"
        else:
            formatted_message = user_message
        
        # Build message history
        messages = self.build_message_history(conversation_history, formatted_message)
        
        # Get system instruction
        system_instruction = self.composer.select_system_instruction(use_rag_instruction)
        
        # Generate response from LLM
        llm_response = await self.llm_service.generate_response(
            messages=messages,
            system_instruction=system_instruction,
            tools=OUTBOUND_FUNCTION_DEFINITIONS
        )
        
        response_text = llm_response["content"]
        
        return response_text


# Singleton instance
response_builder = ResponseBuilder()
