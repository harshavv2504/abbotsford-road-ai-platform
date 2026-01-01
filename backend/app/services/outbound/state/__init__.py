"""
State Module

Modularized state management with:
- Field definitions (fields.py)
- Field management (field_manager.py)
- Tracking utilities (tracking_mixin.py)
- Complete ConversationState (conversation_state.py)
"""

from app.services.outbound.state.conversation_state import ConversationState

__all__ = ['ConversationState']
