"""
RAG Handler for Outbound Bot

DEPRECATED: This file is now a backward-compatible wrapper.
The actual implementation has been modularized into the rag/ directory:
- rag/question_detector.py - Question detection
- rag/answer_handler.py - Answer handling

What it does:
- Detects whether a message is a question
- Retrieves KB context and answers with redirect strategy
- Provides full answers for qualified or exploring users

If you change it:
- You impact how questions are detected and answered across the bot
"""

from typing import Dict, Optional, Tuple
from app.services.outbound.rag import question_detector, answer_handler
from app.services.outbound.state_manager import ConversationState


class RAGHandler:
    """Handles RAG questions with intelligent redirect strategy"""
    
    def __init__(self):
        self.question_detector = question_detector
        self.answer_handler = answer_handler
        # Keep old attributes for backward compatibility
        self.retriever = answer_handler.retriever
        self.llm_service = answer_handler.llm_service
        self.prompt_handler = answer_handler.prompt_handler
        self._rag_initialized = answer_handler._rag_initialized
        self.question_intent_function_def = question_detector.question_intent_function_def
    
    def _ensure_rag_initialized(self):
        """Ensure RAG services are initialized (lazy loading)"""
        self.answer_handler._ensure_rag_initialized()
        self._rag_initialized = self.answer_handler._rag_initialized
    
    def is_rag_question(self, message: str) -> bool:
        return self.question_detector.is_rag_question(message)
    
    def detect_question_intent(self, message: str, last_bot_message: str = "") -> Tuple[bool, str]:
        return self.question_detector.detect_question_intent(message, last_bot_message)
    
    async def detect_question_intent_with_llm(
        self,
        user_message: str,
        last_bot_message: str = ""
    ) -> Dict:
        return await self.question_detector.detect_question_intent_with_llm(user_message, last_bot_message)
    
    def is_answering_current_field(
        self,
        user_message: str,
        last_bot_message: str,
        current_field: str = None
    ) -> bool:
        return self.question_detector.is_answering_current_field(user_message, last_bot_message, current_field)
    
    async def handle_rag_question(
        self,
        user_message: str,
        state: ConversationState,
        next_field_question: str
    ) -> Dict:
        return await self.answer_handler.handle_rag_question(user_message, state, next_field_question)
    
    async def answer_rag_question_unlimited(self, user_message: str, state=None) -> Dict:
        return await self.answer_handler.answer_rag_question_unlimited(user_message, state)


# Singleton instance
rag_handler = RAGHandler()
