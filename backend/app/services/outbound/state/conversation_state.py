"""
Conversation State

What it does:
- Complete ConversationState class combining all mixins
- Manages conversation state with type safety
- Provides serialization methods
"""

from typing import Dict
from datetime import datetime
from app.services.outbound.state.fields import StateFields
from app.services.outbound.state.field_manager import FieldManagerMixin
from app.services.outbound.state.tracking_mixin import TrackingMixin


class ConversationState(StateFields, FieldManagerMixin, TrackingMixin):
    """
    Structured conversation state for outbound chatbot
    
    Manages all conversation data with type safety and helper methods
    for field tracking, validation, and serialization.
    """
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage/API responses"""
        return {
            "customer_type": self.customer_type,
            "intent_stage": self.intent_stage,
            "is_qualified": self.is_qualified,
            "rag_questions_count": self.rag_questions_count,
            "pending_phone": self.pending_phone,
            "pending_phone_confirmation": self.pending_phone_confirmation,
            "country_code": self.country_code,
            "current_field_being_asked": self.current_field_being_asked,
            "current_field_ask_count": self.current_field_ask_count,
            "skipped_preferred_count": self.skipped_preferred_count,
            "phone_validation_attempts": self.phone_validation_attempts,
            "phone_needs_manual_review": self.phone_needs_manual_review,
            "email_validation_attempts": self.email_validation_attempts,
            "email_typo_suggested": self.email_typo_suggested,
            # BUG-001 FIX fields
            "email_preference_indicated": self.email_preference_indicated,
            "phone_preference_indicated": self.phone_preference_indicated,
            # BUG-004 FIX fields
            "contact_refusal_count": self.contact_refusal_count,
            "last_refused_field": self.last_refused_field,
            "refusal_timestamps": [ts.isoformat() for ts in self.refusal_timestamps],
            # BUG-012 FIX fields
            "human_connection_confirmed": self.human_connection_confirmed,
            "human_connection_flow_stage": self.human_connection_flow_stage,
            # BUG-014 FIX fields
            "last_bot_offer": self.last_bot_offer,
            # BUG-008 FIX fields
            "discussed_topics": {
                topic: {
                    "value": data.get("value"),
                    "timestamp": data.get("timestamp").isoformat() if data.get("timestamp") else None,
                    "was_uncertain": data.get("was_uncertain", False)
                }
                for topic, data in self.discussed_topics.items()
            },
            "user_uncertainties": self.user_uncertainties,
            # BUG-007 FIX fields
            "user_engagement_level": self.user_engagement_level,
            "brief_response_count": self.brief_response_count,
            # BUG-013 FIX fields
            "recent_phrases": self.recent_phrases,
            # New cafe fields
            "timeline": self.timeline,
            "coffee_style": self.coffee_style,
            "equipment": self.equipment,
            "volume": self.volume,
            # Existing cafe fields
            "current_pain_points": self.current_pain_points,
            "cafe_count": self.cafe_count,
            "support_needs": self.support_needs,
            "current_coffee_style": self.current_coffee_style,
            "coffee_preference": self.coffee_preference,
            # Contact fields
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            # Order/Sample request fields
            "wants_to_place_order": self.wants_to_place_order,
            "order_details": self.order_details,
            # Metadata
            "rag_question_topics": self.rag_question_topics,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ConversationState':
        """Create ConversationState from dictionary"""
        # Extract datetime if present
        created_at = data.get("created_at")
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        # Parse refusal timestamps
        refusal_timestamps = []
        for ts in data.get("refusal_timestamps", []):
            if isinstance(ts, str):
                refusal_timestamps.append(datetime.fromisoformat(ts))
            elif isinstance(ts, datetime):
                refusal_timestamps.append(ts)
        
        # Parse discussed topics
        discussed_topics = {}
        for topic, topic_data in data.get("discussed_topics", {}).items():
            timestamp = topic_data.get("timestamp")
            if timestamp and isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            discussed_topics[topic] = {
                "value": topic_data.get("value"),
                "timestamp": timestamp,
                "was_uncertain": topic_data.get("was_uncertain", False)
            }
        
        return cls(
            customer_type=data.get("customer_type"),
            intent_stage=data.get("intent_stage", "exploring"),
            is_qualified=data.get("is_qualified", False),
            rag_questions_count=data.get("rag_questions_count", 0),
            pending_phone=data.get("pending_phone"),
            pending_phone_confirmation=data.get("pending_phone_confirmation"),
            country_code=data.get("country_code", "US"),
            current_field_being_asked=data.get("current_field_being_asked"),
            current_field_ask_count=data.get("current_field_ask_count", 0),
            skipped_preferred_count=data.get("skipped_preferred_count", 0),
            phone_validation_attempts=data.get("phone_validation_attempts", 0),
            phone_needs_manual_review=data.get("phone_needs_manual_review", False),
            email_validation_attempts=data.get("email_validation_attempts", 0),
            email_typo_suggested=data.get("email_typo_suggested"),
            # BUG-001 FIX fields
            email_preference_indicated=data.get("email_preference_indicated", False),
            phone_preference_indicated=data.get("phone_preference_indicated", False),
            # BUG-004 FIX fields
            contact_refusal_count=data.get("contact_refusal_count", 0),
            last_refused_field=data.get("last_refused_field"),
            refusal_timestamps=refusal_timestamps,
            # BUG-012 FIX fields
            human_connection_confirmed=data.get("human_connection_confirmed", False),
            human_connection_flow_stage=data.get("human_connection_flow_stage"),
            # BUG-014 FIX fields
            last_bot_offer=data.get("last_bot_offer"),
            # BUG-008 FIX fields
            discussed_topics=discussed_topics,
            user_uncertainties=data.get("user_uncertainties", []),
            # BUG-007 FIX fields
            user_engagement_level=data.get("user_engagement_level", "high"),
            brief_response_count=data.get("brief_response_count", 0),
            # BUG-013 FIX fields
            recent_phrases=data.get("recent_phrases", []),
            # New cafe fields
            timeline=data.get("timeline"),
            coffee_style=data.get("coffee_style"),
            equipment=data.get("equipment"),
            volume=data.get("volume"),
            # Existing cafe fields
            current_pain_points=data.get("current_pain_points"),
            cafe_count=data.get("cafe_count"),
            support_needs=data.get("support_needs"),
            current_coffee_style=data.get("current_coffee_style"),
            coffee_preference=data.get("coffee_preference"),
            # Contact fields
            name=data.get("name"),
            phone=data.get("phone"),
            email=data.get("email"),
            # Order/Sample request fields
            wants_to_place_order=data.get("wants_to_place_order", False),
            order_details=data.get("order_details"),
            # Metadata
            rag_question_topics=data.get("rag_question_topics", []),
            created_at=created_at or datetime.now(),
        )
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        if self.customer_type:
            collected = len(self.get_collected_fields(self.customer_type))
            total = len(self.get_required_fields(self.customer_type))
            return f"<ConversationState {self.customer_type} [{self.intent_stage}] {collected}/{total} fields {'✓ qualified' if self.is_qualified else ''}>"
        return f"<ConversationState [no customer type set]>"
