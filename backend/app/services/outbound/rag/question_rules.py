"""
Question Detection Rules

What it does:
- Provides rule-based question detection patterns
- Fast heuristic checks for question indicators
"""


class QuestionRules:
    """Rule-based question detection patterns"""
    
    # Question words at start of sentence
    QUESTION_STARTERS = [
        'what', 'how', 'why', 'when', 'where', 'which', 'who',
        'do you', 'can you', 'could you', 'would you', 'will you',
        'are you', 'is there', 'does', 'did you', 'have you'
    ]
    
    # Question phrases anywhere in message
    QUESTION_PHRASES = [
        'tell me about', 'tell me more', 'i want to know',
        'i need to know', 'wondering about', 'curious about',
        'explain', 'describe', 'what about', 'how about',
        'can i get', 'could i get', 'may i know',
        'id like to know', "i'd like to know", 'i wanna know',
        'want to know more', 'would like to know', 'more details',
        'know more details', 'details first', 'information first',
        'before providing', 'before giving', 'first i would like'
    ]
    
    # Informational request patterns
    INFO_REQUESTS = [
        'info on', 'information on', 'information about',
        'details on', 'details about', 'more about'
    ]
    
    # Field-specific keywords for answer detection
    FIELD_KEYWORDS = {
        "timeline": ["when", "timeline", "planning to open", "open"],
        "coffee_style": ["coffee", "style", "preference", "bold", "classic", "specialty"],
        "equipment": ["equipment", "machine", "gear"],
        "volume": ["volume", "cups", "daily", "serve", "many"],
        "current_pain_points": ["pain", "issue", "problem", "frustrat"],
        "cafe_count": ["how many", "locations", "cafés"],
        "support_needs": ["support", "help", "need", "training"],
        "name": ["name", "call you"],
        "phone": ["phone", "number"],
        "email": ["email"]
    }
    
    @staticmethod
    def is_question(message: str) -> bool:
        """
        Check if message is a question using rules
        
        Args:
            message: User's message
        
        Returns:
            True if message appears to be a question
        """
        message_lower = message.lower().strip()
        
        # Question indicators
        has_question_mark = '?' in message
        starts_with_question = any(message_lower.startswith(word) for word in QuestionRules.QUESTION_STARTERS)
        has_question_phrase = any(phrase in message_lower for phrase in QuestionRules.QUESTION_PHRASES)
        has_info_request = any(pattern in message_lower for pattern in QuestionRules.INFO_REQUESTS)
        
        return has_question_mark or starts_with_question or has_question_phrase or has_info_request
    
    @staticmethod
    def is_answering_field(user_message: str, last_bot_message: str, current_field: str = None) -> bool:
        """
        Check if user is answering the current field question
        
        Args:
            user_message: User's message
            last_bot_message: Bot's last message
            current_field: Current field being asked
        
        Returns:
            True if user appears to be answering the current field
        """
        if not last_bot_message or not current_field:
            return False
        
        message_lower = user_message.lower().strip()
        bot_lower = last_bot_message.lower()
        
        # Check if bot asked about this field
        if current_field in QuestionRules.FIELD_KEYWORDS:
            keywords = QuestionRules.FIELD_KEYWORDS[current_field]
            bot_asked_field = any(keyword in bot_lower for keyword in keywords)
            
            if bot_asked_field:
                # User is likely answering if message is short and direct
                is_short_answer = len(message_lower.split()) <= 10
                is_not_question = not QuestionRules.is_question(user_message)
                
                return is_short_answer and is_not_question
        
        return False


# Singleton instance
question_rules = QuestionRules()
