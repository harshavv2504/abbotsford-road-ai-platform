"""
State Fields Definition

What it does:
- Defines all state fields as a dataclass
- Core state structure without methods
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime


@dataclass
class StateFields:
    """Core state fields for conversation"""
    
    # Core state
    customer_type: Optional[str] = None
    intent_stage: str = "exploring"
    is_qualified: bool = False
    rag_questions_count: int = 0
    pending_phone: Optional[str] = None
    pending_phone_confirmation: Optional[str] = None
    country_code: str = "US"
    current_field_being_asked: Optional[str] = None
    current_field_ask_count: int = 0
    skipped_preferred_count: int = 0
    
    # Validation tracking
    phone_validation_attempts: int = 0
    phone_needs_manual_review: bool = False
    email_validation_attempts: int = 0
    email_typo_suggested: Optional[str] = None
    
    # BUG-001 FIX: Track contact preference indication
    email_preference_indicated: bool = False
    phone_preference_indicated: bool = False
    
    # BUG-004 FIX: Track contact refusals
    contact_refusal_count: int = 0
    last_refused_field: Optional[str] = None
    refusal_timestamps: List[datetime] = field(default_factory=list)
    
    # BUG-012 FIX: Track human connection confirmation
    human_connection_confirmed: bool = False
    # Track human connection flow stage: None, "awaiting_method", "awaiting_phone", "awaiting_email", "confirmed"
    human_connection_flow_stage: Optional[str] = None
    
    # BUG-014 FIX: Track bot's last offer
    last_bot_offer: Optional[str] = None
    
    # BUG-008 FIX: Track conversation memory
    discussed_topics: Dict[str, Dict] = field(default_factory=dict)
    user_uncertainties: List[str] = field(default_factory=list)
    
    # BUG-007 FIX: Track user engagement level
    user_engagement_level: str = "high"
    brief_response_count: int = 0
    
    # BUG-013 FIX: Track recently used phrases
    recent_phrases: List[str] = field(default_factory=list)
    
    # New cafe fields
    timeline: Optional[str] = None
    coffee_style: Optional[str] = None
    equipment: Optional[str] = None
    volume: Optional[str] = None
    
    # Existing cafe fields
    current_pain_points: Optional[str] = None
    cafe_count: Optional[str] = None
    support_needs: Optional[str] = None
    current_coffee_style: Optional[str] = None
    coffee_preference: Optional[str] = None
    
    # Contact fields (required for both types)
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    
    # Order/Sample request fields
    wants_to_place_order: bool = False
    order_details: Optional[str] = None
    
    # Metadata
    rag_question_topics: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
