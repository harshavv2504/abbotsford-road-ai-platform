"""
Tracking Mixin

What it does:
- Tracks RAG questions, refusals, engagement
- Manages validation attempts
- Handles intent stage transitions
"""

from typing import Dict
from datetime import datetime
from app.utils.logger import logger


class TrackingMixin:
    """Mixin for tracking various conversation metrics"""
    
    def increment_rag_count(self) -> int:
        """Increment RAG question count and return new count"""
        self.rag_questions_count += 1
        return self.rag_questions_count
    
    def reset_rag_count(self) -> None:
        """Reset RAG question counter"""
        self.rag_questions_count = 0
    
    def track_contact_refusal(self, field: str = "contact") -> None:
        """BUG-004 FIX: Track when user refuses to provide contact information"""
        self.contact_refusal_count += 1
        self.last_refused_field = field
        self.refusal_timestamps.append(datetime.now())
        logger.info(f"⚠️ BUG-004 FIX: Contact refusal tracked: {field} (total: {self.contact_refusal_count})")
    
    def should_stop_asking_contact(self) -> bool:
        """BUG-004 FIX: Check if we should stop asking for contact info after multiple refusals"""
        return self.contact_refusal_count >= 2
    
    def was_recently_refused(self, field: str, seconds: int = 60) -> bool:
        """BUG-004 FIX: Check if a field was recently refused"""
        if field != self.last_refused_field:
            return False
        
        if not self.refusal_timestamps:
            return False
        
        last_refusal = self.refusal_timestamps[-1]
        time_since_refusal = (datetime.now() - last_refusal).seconds
        return time_since_refusal < seconds
    
    def mark_topic_discussed(self, topic: str, value: any) -> None:
        """BUG-008 FIX: Mark that a topic was discussed"""
        self.discussed_topics[topic] = {
            "value": value,
            "timestamp": datetime.now(),
            "was_uncertain": value in ["unclear", "to_be_discussed_with_team", None]
        }
        logger.info(f"📝 BUG-008 FIX: Marked topic '{topic}' as discussed (value: {value})")
    
    def was_topic_discussed(self, topic: str) -> bool:
        """BUG-008 FIX: Check if topic was already discussed"""
        return topic in self.discussed_topics
    
    def mark_user_uncertain(self, topic: str) -> None:
        """BUG-008 FIX: Mark that user was uncertain about this topic"""
        if topic not in self.user_uncertainties:
            self.user_uncertainties.append(topic)
            logger.info(f"❓ BUG-008 FIX: Marked user uncertain about '{topic}'")
    
    def track_user_engagement(self, user_message: str) -> None:
        """BUG-007 FIX: Track user engagement level based on response patterns"""
        message_length = len(user_message.split())
        message_lower = user_message.lower().strip()
        
        # Brief disengaged responses
        brief_responses = ["no", "ok", "okay", "sure", "yes", "nope", "nah", "fine"]
        
        if message_length <= 3 and message_lower in brief_responses:
            self.brief_response_count += 1
        else:
            # Reset counter if user gives detailed response
            self.brief_response_count = max(0, self.brief_response_count - 1)
        
        # Update engagement level
        if self.brief_response_count >= 3:
            self.user_engagement_level = "low"
        elif self.brief_response_count >= 2:
            self.user_engagement_level = "medium"
        else:
            self.user_engagement_level = "high"
        
        logger.info(f"📊 BUG-007 FIX: User engagement: {self.user_engagement_level} (brief count: {self.brief_response_count})")
    
    def was_phrase_recently_used(self, phrase: str, lookback: int = 3) -> bool:
        """BUG-013 FIX: Check if phrase was used in recent responses"""
        return phrase in self.recent_phrases[-lookback:] if self.recent_phrases else False
    
    def track_phrase_used(self, phrase: str) -> None:
        """BUG-013 FIX: Track that a phrase was used"""
        self.recent_phrases.append(phrase)
        # Keep only last 10
        if len(self.recent_phrases) > 10:
            self.recent_phrases = self.recent_phrases[-10:]
    
    def add_rag_topic(self, topic: str) -> None:
        """Track a RAG question topic"""
        self.rag_question_topics.append(topic[:50])
    
    def increment_phone_attempts(self) -> int:
        """Increment phone validation attempts and return new count"""
        self.phone_validation_attempts += 1
        return self.phone_validation_attempts
    
    def reset_phone_attempts(self) -> None:
        """Reset phone validation attempts (when successfully validated)"""
        self.phone_validation_attempts = 0
    
    def flag_phone_for_review(self) -> None:
        """Flag phone number for manual review after max attempts"""
        self.phone_needs_manual_review = True
        logger.info("Phone flagged for manual review after max validation attempts")
    
    def increment_email_attempts(self) -> int:
        """Increment email validation attempts and return new count"""
        self.email_validation_attempts += 1
        return self.email_validation_attempts
    
    def reset_email_attempts(self) -> None:
        """Reset email validation attempts (when successfully validated)"""
        self.email_validation_attempts = 0
        self.email_typo_suggested = None
    
    def set_email_typo_suggested(self, suggested_email: str) -> None:
        """Track that we suggested a typo correction"""
        self.email_typo_suggested = suggested_email
    
    def set_intent_stage(self, stage: str) -> None:
        """Set intent stage with validation"""
        valid_stages = ["exploring", "interest_detected", "intent_confirmed", "qualifying", "qualified"]
        if stage not in valid_stages:
            raise ValueError(f"Invalid intent stage: {stage}. Must be one of {valid_stages}")
        self.intent_stage = stage
        logger.info(f"Intent stage changed to: {stage}")
    
    def can_start_qualification(self) -> bool:
        """Check if qualification can start based on intent stage"""
        return self.intent_stage in ["intent_confirmed", "qualifying"]
    
    def reset_to_exploration(self) -> None:
        """Reset to exploration mode"""
        old_stage = self.intent_stage
        self.intent_stage = "exploring"
        self.rag_questions_count = 0
        logger.info(f"Reset from {old_stage} to exploration mode")
    
    def track_field_ask(self, field: str) -> int:
        """Track that we asked for a field and return ask count"""
        if self.current_field_being_asked != field:
            # New field being asked
            self.current_field_being_asked = field
            self.current_field_ask_count = 1
        else:
            # Same field being asked again
            self.current_field_ask_count += 1
        
        logger.info(f"📝 Tracking field ask: {field} (count: {self.current_field_ask_count})")
        return self.current_field_ask_count
    
    def reset_field_tracking(self) -> None:
        """Reset field tracking (when field is collected or skipped)"""
        self.current_field_being_asked = None
        self.current_field_ask_count = 0
    
    def should_skip_field(self) -> bool:
        """Check if current field should be skipped after multiple asks"""
        MAX_ASKS = 2
        
        if self.current_field_ask_count >= MAX_ASKS:
            if self.current_field_being_asked and self.is_skippable_field(self.current_field_being_asked):
                logger.info(f"⏭️  Skipping field '{self.current_field_being_asked}' after {self.current_field_ask_count} asks")
                return True
        
        return False
