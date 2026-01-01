"""
Answer Handler

What it does:
- Handles RAG question answering with redirect strategy
- Manages 3-strike redirect during qualification
- Provides unlimited answers for qualified users
"""

from typing import Dict
from app.services.rag.retriever import retriever
from app.services.llm_service import llm_service
from app.services.outbound.prompt_handler import outbound_prompt_handler
from app.services.outbound.state_manager import ConversationState
from app.services.outbound.rag.context_builder import context_builder
from app.utils.logger import logger


class AnswerHandler:
    """Handles RAG question answering"""
    
    def __init__(self):
        self.retriever = retriever
        self.llm_service = llm_service
        self.prompt_handler = outbound_prompt_handler
        self.context_builder = context_builder
        self._rag_initialized = False
    
    def _ensure_rag_initialized(self):
        """Ensure RAG services are initialized (lazy loading)"""
        if not self._rag_initialized:
            try:
                from app.services.rag.embedding_service import embedding_service
                from app.services.rag.vector_store import vector_store
                
                # Initialize embedding model
                if embedding_service.model is None:
                    logger.info("Initializing embedding model for RAG...")
                    embedding_service.initialize_model()
                
                # Load vector index
                if vector_store.index is None or vector_store.get_index_size() == 0:
                    logger.info("Loading vector index for RAG...")
                    vector_store.load_index()
                
                self._rag_initialized = True
                logger.info(f"✅ RAG initialized ({vector_store.get_index_size()} documents)")
            except Exception as e:
                logger.error(f"Failed to initialize RAG: {e}")
                self._rag_initialized = False
    
    async def handle_rag_question(
        self,
        user_message: str,
        state: ConversationState,
        next_field_question: str
    ) -> Dict:
        """
        Handle RAG question with 3-strike redirect strategy
        
        Args:
            user_message: User's question
            state: Conversation state
            next_field_question: Next question to ask
        
        Returns:
            Dict with response and should_end flag
        """
        # Increment RAG question count
        rag_count = state.increment_rag_count()
        state.add_rag_topic(user_message[:50])
        
        logger.info(f"RAG question #{rag_count}: {user_message[:50]}")
        
        # Get RAG answer
        self._ensure_rag_initialized()
        relevant_docs = self.retriever.retrieve(user_message, k=2)
        
        if relevant_docs:
            rag_context = self.retriever.format_context_for_llm(relevant_docs)
        else:
            rag_context = "No specific information found in knowledge base."
        
        # Build redirect instruction using context builder
        redirect_instruction = self.context_builder.build_redirect_instruction(rag_count, next_field_question)
        
        # Build collected data context using context builder
        collected_data_context = self.context_builder.build_collected_data_context(state)
        
        # Build LLM prompt
        prompt = f"""User asked: {user_message}
{collected_data_context}

Knowledge base context:
{rag_context}

{redirect_instruction}

You're Logan - warm, helpful, and conversational."""
        
        # Generate response
        try:
            response = await self.llm_service.generate_response(
                messages=[{"role": "user", "content": prompt}],
                system_instruction=self.prompt_handler.get_system_instruction(),
                temperature=0.7,
                max_tokens=250
            )
            
            return {
                "response": response["content"],
                "should_end": False
            }
        except Exception as e:
            logger.error(f"Failed to generate RAG response: {e}")
            return {
                "response": f"That's a great question! Let me get a few details about your café first, then I can give you the best answer. {next_field_question}",
                "should_end": False
            }
    
    async def answer_rag_question_unlimited(self, user_message: str, state=None) -> Dict:
        """
        Answer RAG question without redirect (for qualified users or exploration)
        
        Args:
            user_message: User's question
            state: Optional conversation state
        
        Returns:
            Dict with response and should_end flag
        """
        # Get RAG answer
        self._ensure_rag_initialized()
        relevant_docs = self.retriever.retrieve(user_message, k=3)
        
        if relevant_docs:
            rag_context = self.retriever.format_context_for_llm(relevant_docs)
        else:
            rag_context = "No specific information found in knowledge base."
        
        # Build collected data context using context builder
        collected_data_context = self.context_builder.build_collected_data_context(state)
        
        prompt = f"""User asked: {user_message}
{collected_data_context}

Knowledge base context:
{rag_context}

Provide a helpful, comprehensive answer. You're Logan - warm and conversational."""
        
        try:
            response = await self.llm_service.generate_response(
                messages=[{"role": "user", "content": prompt}],
                system_instruction=self.prompt_handler.get_system_instruction(),
                temperature=0.7,
                max_tokens=300
            )
            
            return {
                "response": response["content"],
                "should_end": False
            }
        except Exception as e:
            logger.error(f"Failed to generate RAG response: {e}")
            return {
                "response": "I'd be happy to help with that! Could you rephrase your question?",
                "should_end": False
            }


# Singleton instance
answer_handler = AnswerHandler()
