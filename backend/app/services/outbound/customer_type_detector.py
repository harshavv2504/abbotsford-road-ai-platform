"""
Customer Type Detector (outbound)

DEPRECATED: This file is now a backward-compatible wrapper.
The actual implementation has been modularized into the detection/ directory:
- detection/flow_detector.py - Flow state detection
- detection/type_detector.py - Customer type detection

What it does:
- Infers customer type and flow states using LLM signals and heuristics
- Detects early intents (talk to a person, place order)

If you change it:
- You influence routing and stage selection throughout the bot
"""

from typing import Dict, List, Optional
from app.services.outbound.detection import flow_detector, type_detector


class CustomerTypeDetector:
    """Backward-compatible wrapper for modularized detection"""
    
    def __init__(self):
        self.flow_detector = flow_detector
        self.type_detector = type_detector
        # Keep old attributes for backward compatibility
        self.llm_service = type_detector.llm_service
    
    async def detect_flow_state(self, user_message: str, conversation_history: List[Dict], current_field: Optional[str] = None) -> Dict:
        return await self.flow_detector.detect_flow_state(user_message, conversation_history, current_field)
    
    async def detect_with_llm(
        self, 
        user_message: str, 
        conversation_history: List[Dict]
    ) -> Optional[Dict]:
        return await self.type_detector.detect_with_llm(user_message, conversation_history)


# Singleton instance
customer_type_detector = CustomerTypeDetector()
