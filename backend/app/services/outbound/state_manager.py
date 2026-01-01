"""
State Manager (outbound)

DEPRECATED: This file is now a backward-compatible wrapper.
The actual implementation has been modularized into the state/ directory:
- state/fields.py - Field definitions
- state/field_manager.py - Field management methods
- state/tracking_mixin.py - Tracking utilities
- state/conversation_state.py - Complete ConversationState class

What it does:
- Holds `ConversationState` across turns, including stages, collected fields, counters, and helper methods
  for progression (e.g., missing/required fields, skip logic, rag counters).

If you change it:
- You impact invariants used by many modules. Keep method names stable and avoid hidden side effects; update
  `FlowController` and pipelines if you rename fields or transitions.
"""

from app.services.outbound.state import ConversationState

__all__ = ['ConversationState']
