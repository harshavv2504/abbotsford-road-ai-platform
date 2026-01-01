"""
Context Builder

What it does:
- Builds context from conversation state
- Formats collected data for LLM prompts
"""

from typing import Dict
from app.services.outbound.state_manager import ConversationState


class ContextBuilder:
    """Builds context for RAG responses"""
    
    @staticmethod
    def build_collected_data_context(state: ConversationState) -> str:
        """
        Build collected data context from state
        
        Args:
            state: Conversation state
        
        Returns:
            Formatted context string
        """
        if not state:
            return ""
        
        collected_data = {}
        
        # Get collected fields based on customer type
        if state.customer_type:
            all_fields = state.get_all_fields(state.customer_type)
            for field in all_fields:
                value = state.get_field(field)
                if value and value not in ["to_be_discussed_with_team", "user_declined"]:
                    collected_data[field] = value
        else:
            # Even without customer_type, show contact info if collected
            if state.name:
                collected_data["name"] = state.name
            if state.phone:
                collected_data["phone"] = state.phone
            if state.email:
                collected_data["email"] = state.email
        
        if not collected_data:
            return ""
        
        # Build context string
        context = "\n\n📋 USER'S INFORMATION (use this when relevant):\n"
        for field, value in collected_data.items():
            context += f"   • {field}: {value}\n"
        context += "\nCRITICAL: If the user asks about THEIR OWN information (their name, email, phone, timeline, etc.), use the USER'S INFORMATION above. DO NOT say you don't know or can't share it."
        
        return context
    
    @staticmethod
    def build_redirect_instruction(rag_count: int, next_field_question: str) -> str:
        """
        Build redirect instruction based on RAG question count
        
        Args:
            rag_count: Number of RAG questions asked
            next_field_question: Next question to ask
        
        Returns:
            Redirect instruction for LLM
        """
        if rag_count == 1:
            return f"""Answer their question using the knowledge base, then add a gentle redirect.

Example format: "Great question! [answer]. By the way, {next_field_question}"

Keep it natural and conversational (1-2 sentences max)."""
            
        elif rag_count == 2:
            return f"""Answer their question, then add a stronger redirect showing enthusiasm.

Example format: "[answer]. I'd love to help you more! {next_field_question}"

Keep it natural and conversational (1-2 sentences max)."""
            
        elif rag_count == 3:
            return f"""Answer their question, acknowledge their diligence, then redirect with value.

Example format: "[answer]. I can tell you're really thinking this through! {next_field_question}"

Keep it natural and conversational (1-2 sentences max)."""
            
        else:
            return f"""Politely defer and create urgency to qualify first.

Example format: "I can definitely help with that! Let me get a few quick details first, then I'll give you comprehensive answers to all your questions. {next_field_question}"

Keep it friendly but firm (1-2 sentences max)."""


# Singleton instance
context_builder = ContextBuilder()
