from typing import Dict, List, Optional
from datetime import datetime


class InboundBotBusinessLogic:
    """Business rules and logic for inbound chatbot"""
    
    # Issue categories
    CATEGORY_EQUIPMENT = "equipment"
    CATEGORY_ORDER = "order"
    CATEGORY_BILLING = "billing"
    CATEGORY_QUALITY = "quality"
    CATEGORY_DELIVERY = "delivery"
    CATEGORY_TRAINING = "training"
    CATEGORY_MACHINE = "machine"
    CATEGORY_MILK = "milk"
    CATEGORY_MENU = "menu"
    CATEGORY_GENERAL = "general"
    

    
    @staticmethod
    def categorize_issue(issue_text: str) -> str:
        """
        Categorize issue based on keywords
        
        Args:
            issue_text: Issue description
        
        Returns:
            Category string
        """
        text_lower = issue_text.lower()
        
        # Machine issues (SCENARIO 4 - interrupting service)
        machine_keywords = [
            "pressure", "temperature", "steam wand", "group head", "flow",
            "heating", "not heating", "temp", "steam", "wand", "group",
            "low pressure", "high pressure", "fluctuation"
        ]
        if any(kw in text_lower for kw in machine_keywords):
            return InboundBotBusinessLogic.CATEGORY_MACHINE
        
        # Milk issues (SCENARIO 5)
        milk_keywords = [
            "milk", "foam", "froth", "texture", "splitting", "stretching",
            "alternative milk", "oat milk", "almond milk", "soy milk",
            "plant milk", "steaming", "microfoam"
        ]
        if any(kw in text_lower for kw in milk_keywords):
            return InboundBotBusinessLogic.CATEGORY_MILK
        
        # Menu issues (SCENARIO 6)
        menu_keywords = [
            "menu", "recipe", "drinks", "too many", "complex", "sku",
            "standardization", "consistency", "staff struggle"
        ]
        if any(kw in text_lower for kw in menu_keywords):
            return InboundBotBusinessLogic.CATEGORY_MENU
        
        # Equipment issues (general)
        equipment_keywords = [
            "equipment", "grinder", "brewer", "broken", "not working",
            "malfunction", "repair", "maintenance", "jamming", "feeding"
        ]
        if any(kw in text_lower for kw in equipment_keywords):
            return InboundBotBusinessLogic.CATEGORY_EQUIPMENT
        
        # Order issues
        order_keywords = [
            "order", "ordered", "purchase", "buy", "stock", "inventory",
            "out of stock", "reorder", "shipment"
        ]
        if any(kw in text_lower for kw in order_keywords):
            return InboundBotBusinessLogic.CATEGORY_ORDER
        
        # Billing issues
        billing_keywords = [
            "bill", "invoice", "payment", "charge", "charged", "price",
            "pricing", "cost", "refund", "overcharged"
        ]
        if any(kw in text_lower for kw in billing_keywords):
            return InboundBotBusinessLogic.CATEGORY_BILLING
        
        # Quality issues (SCENARIO 1 - taste different)
        quality_keywords = [
            "quality", "taste", "flavor", "stale", "bad", "burnt",
            "inconsistent", "different", "wrong", "complaint", "bitter",
            "weak", "sour", "acidic"
        ]
        if any(kw in text_lower for kw in quality_keywords):
            return InboundBotBusinessLogic.CATEGORY_QUALITY
        
        # Delivery issues (SCENARIO 3 - urgent)
        delivery_keywords = [
            "delivery", "deliver", "late", "delayed", "arrived", "shipping",
            "received", "missing", "lost", "tracking", "run out", "running out"
        ]
        if any(kw in text_lower for kw in delivery_keywords):
            return InboundBotBusinessLogic.CATEGORY_DELIVERY
        
        # Training issues (SCENARIO 2 - dialing in)
        training_keywords = [
            "training", "teach", "learn", "how to", "barista", "staff",
            "employee", "instruction", "guide", "dial", "dialing"
        ]
        if any(kw in text_lower for kw in training_keywords):
            return InboundBotBusinessLogic.CATEGORY_TRAINING
        
        return InboundBotBusinessLogic.CATEGORY_GENERAL
    

    
    @staticmethod
    def validate_ticket_readiness(
        issue_summary: Optional[str],
        issue_details: Optional[str]
    ) -> Dict:
        """
        Validate if we have enough information to create a ticket
        
        Args:
            issue_summary: Brief summary of issue
            issue_details: Detailed description
        
        Returns:
            Dict with success status and message
        """
        if not issue_summary or not issue_summary.strip():
            return {
                "success": False,
                "message": "Missing issue summary"
            }
        
        if not issue_details or not issue_details.strip():
            return {
                "success": False,
                "message": "Missing issue details"
            }
        
        # Check if details are too vague
        if len(issue_details.strip()) < 10:
            return {
                "success": False,
                "message": "Issue details too brief"
            }
        
        return {
            "success": True,
            "message": "Ready for ticket creation"
        }
    
    @staticmethod
    def format_ticket_data(
        issue_summary: str,
        issue_details: str,
        user_id: str,
        user_name: str,
        user_email: str,
        conversation_id: str
    ) -> Dict:
        """
        Format ticket data for creation
        
        Args:
            issue_summary: Brief summary
            issue_details: Detailed description
            user_id: User's ID
            user_name: User's name
            user_email: User's email
            conversation_id: Conversation ID
        
        Returns:
            Formatted ticket data
        """
        category = InboundBotBusinessLogic.categorize_issue(issue_details)
        
        return {
            "summary": issue_summary,
            "details": issue_details,
            "category": category,
            "user_id": user_id,
            "user_name": user_name,
            "user_email": user_email,
            "conversation_id": conversation_id,
            "status": "open",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
    
    @staticmethod
    def should_ask_clarifying_question(
        issue_text: str,
        questions_asked: int
    ) -> bool:
        """
        Determine if we should ask a clarifying question
        
        Args:
            issue_text: Current issue description
            questions_asked: Number of questions already asked
        
        Returns:
            True if should ask more questions
        """
        # Don't ask more than 3 clarifying questions
        if questions_asked >= 3:
            return False
        
        # If issue is very brief, ask for more details
        if len(issue_text.strip()) < 20:
            return True
        
        # If issue lacks specifics, ask for clarification
        vague_indicators = [
            "not working", "broken", "problem", "issue", "wrong",
            "bad", "doesn't work"
        ]
        
        text_lower = issue_text.lower()
        has_vague_terms = any(term in text_lower for term in vague_indicators)
        
        # Check if they provided specifics
        specific_indicators = [
            "when", "how", "what", "where", "error", "message",
            "tried", "happens", "started", "since"
        ]
        has_specifics = any(term in text_lower for term in specific_indicators)
        
        # Ask if vague and no specifics
        return has_vague_terms and not has_specifics
    
    @staticmethod
    def get_clarifying_question(category: str, issue_text: str) -> str:
        """
        Get appropriate clarifying question that helps troubleshooting AND ticket building
        
        Args:
            category: Issue category
            issue_text: Current issue description
        
        Returns:
            Helpful clarifying question
        """
        text_lower = issue_text.lower()
        
        # SCENARIO 1: Coffee tastes different today
        if "taste" in text_lower or "different" in text_lower or "flavor" in text_lower:
            if "bitter" not in text_lower and "weak" not in text_lower and "sour" not in text_lower:
                return "Is it tasting more bitter, weaker, or more sour than usual?"
            elif "grind" not in text_lower:
                return "Check if the grind moved a click finer or coarser."
            elif "dose" not in text_lower:
                return "Make sure dose is consistent."
            elif "shot time" not in text_lower:
                return "Confirm shot time is still in your usual range."
            else:
                return "Would you like me to create a support case so the team can take a closer look?"
        
        # SCENARIO 2: Staff need help dialing in
        if "staff" in text_lower or "dial" in text_lower or "training" in text_lower or "barista" in text_lower:
            if "fast" not in text_lower and "slow" not in text_lower and "sour" not in text_lower and "bitter" not in text_lower:
                return "Are the shots running too fast, too slow, or does the taste seem off (sour/bitter)?"
            else:
                return "Would you like a simple dialing-in guide for your staff?"
        
        # SCENARIO 3: Urgent stock / missing delivery
        if any(word in text_lower for word in ["run out", "almost out", "urgent", "emergency", "not delivered", "missing delivery"]):
            if "order" not in text_lower:
                return "Do you have the order number or order date?"
            elif "tracking" not in text_lower:
                return "Did you receive a tracking email or SMS?"
            else:
                return "I'll escalate this right away so the team can chase the shipment or arrange urgent replacement."
        
        # SCENARIO 4: Machine issues interrupting service
        if category == InboundBotBusinessLogic.CATEGORY_MACHINE:
            if not any(word in text_lower for word in ["pressure", "temperature", "steam", "group", "grinder"]):
                return "Is the issue with pressure, temperature, steam wand, group head flow, or grinder feeding?"
            else:
                return "Most of the time this is calibration or cleaning, not a broken machine. Have you tried the basic checks?"
        
        # SCENARIO 5: Milk / alternative milk issues
        if category == InboundBotBusinessLogic.CATEGORY_MILK:
            if not any(word in text_lower for word in ["thin", "split", "foam", "stretch"]):
                return "Is the milk too thin, splitting, too foamy, or not stretching?"
            else:
                return "Would you like me to create a support case for the team to help with milk consistency?"
        
        # SCENARIO 6: Menu problems
        if category == InboundBotBusinessLogic.CATEGORY_MENU:
            if "struggle" not in text_lower:
                return "Are there any drinks that staff struggle with regularly?"
            else:
                return "Would you like guidance on simplifying menu flow or recipe standardization?"
        
        if category == InboundBotBusinessLogic.CATEGORY_EQUIPMENT:
            if "clean" not in text_lower and "daily" not in text_lower:
                return "Have you performed the daily cleaning cycle? Often flow issues are due to blockage."
            elif "steam" in text_lower and "block" not in text_lower:
                return "Is the steam wand tip blocked? Sometimes milk residue can cause pressure issues."
            elif "grinder" in text_lower and "gate" not in text_lower:
                return "Is the grinder hopper gate open? It's a common check for feeding issues."
            else:
                return "If those steps don't work, what else have you tried? I want to make sure our team doesn't repeat the same troubleshooting."
        
        elif category == InboundBotBusinessLogic.CATEGORY_QUALITY:
            if "grinder" not in text_lower and "calibrat" not in text_lower:
                return "Has the grinder been calibrated recently? Changes in humidity can affect the grind."
            elif "dose" not in text_lower:
                return "Have you checked the dose consistency? A small variance can change the taste significantly."
            elif "milk" in text_lower and "temp" not in text_lower:
                return "Are you using a thermometer for the milk? Temperature overshooting is a common cause of texture issues."
            else:
                return "How does the taste compare to what you normally expect? This detail helps our quality team investigate."
        
        elif category == InboundBotBusinessLogic.CATEGORY_ORDER:
            if "cafe" not in text_lower and "location" not in text_lower:
                return "To help you fast, what is your Café Name and Location?"
            elif "missing" in text_lower or "run out" in text_lower:
                return "What specific items are you missing? I'll get this to our production team immediately."
            else:
                return "When was this order needed by? I want to mark the urgency correctly."

        elif category == InboundBotBusinessLogic.CATEGORY_TRAINING:
            return "Are new staff members having trouble dialing in? We can share a guide or schedule a visit."
        
        elif category == InboundBotBusinessLogic.CATEGORY_DELIVERY:
            if "when" not in text_lower:
                return "While I look into your recent orders, when was this delivery supposed to arrive? This helps me check if it's actually late or just delayed."
            elif "order" not in text_lower:
                return "Do you have the order number handy? I can track it immediately and add the details to your case."
            else:
                return "Have you received any tracking updates or delivery notifications? I'll check our system and update your case with what I find."
        
        elif category == InboundBotBusinessLogic.CATEGORY_BILLING:
            if "invoice" not in text_lower and "order" not in text_lower:
                return "Which invoice or order is this about?"
            elif "amount" not in text_lower:
                return "What amount were you expecting vs what you were charged?"
            else:
                return "When did you notice this issue?"
        
        # Generic clarifying questions
        return "While you try those steps, can you tell me more about what's happening? The more details I have, the better I can help our team assist you."
    
    @staticmethod
    def prepare_farewell_message(farewell_type: str = "general") -> Dict:
        """
        Prepare farewell message for ending the chat
        
        Args:
            farewell_type: Type of farewell ("thanks", "general", "help")
        
        Returns:
            Dict with farewell message and metadata
        """
        if farewell_type == "thanks":
            message = "Thank you for reaching out! Have a great day!"
        elif farewell_type == "help":
            message = "Happy to help! Have a wonderful day!"
        else:  # general
            message = "Take care! Have a great day!"
        
        return {
            "status": "closing",
            "message": message,
            "farewell_type": farewell_type
        }


# Singleton instance
inbound_bot_business_logic = InboundBotBusinessLogic()
