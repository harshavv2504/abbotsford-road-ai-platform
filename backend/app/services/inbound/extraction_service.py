"""
Extraction Service for Inbound Bot

Handles issue extraction from user messages using LLM function calling.
"""

from typing import Dict, List, Optional
import json
from app.services.llm_service import llm_service
from app.utils.logger import logger


class InboundExtractionService:
    """Service for extracting issue data from customer messages"""
    
    def __init__(self):
        self.llm_service = llm_service
        
        # Define intent detection function for problem detection
        self.intent_detection_function_def = [
            {
                "type": "function",
                "function": {
                    "name": "detect_customer_intent",
                    "description": "Determine if the customer is reporting a problem/issue or just chatting/asking questions/acknowledging.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "has_problem": {
                                "type": "boolean",
                                "description": "True if customer is reporting ANY problem/issue (first or additional), False if just greeting/chatting/answering questions/acknowledging/saying they're done"
                            },
                            "confidence": {
                                "type": "string",
                                "enum": ["high", "medium", "low"],
                                "description": "Confidence level in the detection"
                            },
                            "reasoning": {
                                "type": "string",
                                "description": "Brief explanation of why this was classified as having a problem or not"
                            }
                        },
                        "required": ["has_problem", "confidence", "reasoning"]
                    }
                }
            }
        ]
        
        # Define extraction function for OpenAI function calling
        self.extraction_function_def = [
            {
                "type": "function",
                "function": {
                    "name": "extract_issue_data",
                    "description": "Extract issue information from the customer's message. Call this for EVERY customer message to extract any issue details they provide.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "issue_summary": {
                                "type": "string",
                                "description": "Brief one-line summary of the issue (e.g., 'Espresso machine not heating', 'Late delivery', 'Billing error on invoice'). Use null if no clear issue mentioned."
                            },
                            "issue_details": {
                                "type": "string",
                                "description": "Detailed description including: what's wrong, when it started, what they've tried, impact on business. Use null if not enough details provided."
                            },
                            "category": {
                                "type": "string",
                                "enum": ["equipment", "order", "billing", "quality", "delivery", "training", "machine", "milk", "menu", "general", "null"],
                                "description": "Issue category: 'equipment' (general equipment, grinders), 'order' (purchasing, stock, run out), 'billing' (invoices, payments), 'quality' (taste, flavor issues), 'delivery' (shipping, late arrivals), 'training' (dialing in, staff training), 'machine' (pressure, temperature, steam wand, group head, interrupting service), 'milk' (milk texture, foam, alternative milk, splitting), 'menu' (menu complexity, recipe issues, too many SKUs), 'general' (other), or 'null' if unclear"
                            },
                            "urgency": {
                                "type": "string",
                                "enum": ["critical", "high", "normal", "null"],
                                "description": "Urgency level: 'critical' (run out of coffee, few hours left, emergency, not delivered), 'high' (affecting business now), 'normal' (standard issue), or 'null' if unclear"
                            },

                            "when_started": {
                                "type": "string",
                                "description": "When the issue started (e.g., 'this morning', 'yesterday', '3 days ago', 'last week'). Use null if not mentioned."
                            },
                            "what_tried": {
                                "type": "string",
                                "description": "What customer has already tried to fix it. Use null if not mentioned."
                            },
                            "business_impact": {
                                "type": "string",
                                "description": "How it's affecting their business (e.g., 'can't serve customers', 'losing sales', 'customers complaining'). Use null if not mentioned."
                            },
                            "additional_issue": {
                                "type": "boolean",
                                "description": "True ONLY if customer mentions a COMPLETELY NEW AND DIFFERENT problem (e.g., 'Also, my grinder is broken' when already discussing coffee machine, or 'And my delivery was late' when discussing equipment). False for: answering questions, providing details about existing issue, clarifying existing issue, saying no/nothing, acknowledging. Default: false"
                            }
                        },
                        "required": []
                    }
                }
            }
        ]
    
    async def extract_issue_with_llm(
        self, 
        user_message: str,
        conversation_history: Optional[List[Dict]] = None,
        existing_issue: Optional[str] = None,
        is_first_problem: bool = True
    ) -> Dict:
        """
        Extract issue information from message using LLM function calling
        
        Args:
            user_message: User's current message
            conversation_history: Recent conversation for context
            existing_issue: Summary of existing issue if any
            is_first_problem: True if this is the first problem, False if additional
        
        Returns:
            Dict of extracted fields (only non-null values)
        """
        # Build context from recent conversation
        context_str = ""
        last_bot_question = ""
        if conversation_history:
            recent_messages = []
            for msg in conversation_history[-3:]:  # Last 3 messages for context
                if 'user' in msg:
                    recent_messages.append(f"Customer: {msg['user']}")
                elif 'bot' in msg:
                    recent_messages.append(f"Bot: {msg['bot']}")
                    last_bot_question = msg['bot']  # Track last bot message
            
            if recent_messages:
                context_str = "\n\nRecent conversation:\n" + "\n".join(recent_messages)
        
        # Add explicit context about what bot just asked
        if last_bot_question:
            context_str += f"\n\n⚠️ Bot just asked: \"{last_bot_question}\"\nThis means customer is likely ANSWERING that question, NOT reporting a new issue."
        
        # Add existing issue context based on state
        existing_context = ""
        if not is_first_problem and existing_issue:
            existing_context = f"\n\n⚠️ IMPORTANT: Customer already reported issue: '{existing_issue}'\n"
            existing_context += "This is an ADDITIONAL problem. Mark additional_issue=true.\n"
            existing_context += "Examples of additional issues:\n"
            existing_context += "- Already discussing coffee machine → customer mentions grinder problem = additional_issue: true\n"
            existing_context += "- Already discussing equipment → customer mentions delivery delay = additional_issue: true\n"
            existing_context += "- Already discussing billing → customer mentions quality issue = additional_issue: true"
        elif is_first_problem:
            existing_context = "\n\n✅ This is the FIRST problem being reported. Mark additional_issue=false."
        
        # Add hint based on problem tracking
        additional_hint = ""
        if not is_first_problem:
            additional_hint = "\n\n🚨 STATE TRACKING: This is NOT the first problem - customer already reported an issue. Mark additional_issue=true."
        
        extraction_prompt = f"""Extract issue information from this customer message. Be thorough - extract all available details.

Current message: "{user_message}"{context_str}{existing_context}{additional_hint}

EXTRACTION RULES:

✅ EXTRACT if mentioned:
- issue_summary: One-line summary of the problem (ONLY if this is a NEW issue being reported)
- issue_details: Full description with context (ONLY if this is a NEW issue being reported)
- category: Type of issue (equipment, order, billing, quality, delivery, training, general)
- when_started: When problem began
- what_tried: What they've already attempted
- business_impact: How it affects their business
- additional_issue: True ONLY if customer mentions a COMPLETELY NEW/DIFFERENT problem

❌ USE "null" if:
- Information not mentioned in message
- Too vague to be useful
- Unclear or ambiguous
- Customer is saying NO to additional issues (e.g., "no", "no that's it", "nothing else", "that's all")
- Customer is just acknowledging (e.g., "ok", "thanks", "got it")
- Customer is answering a question about the EXISTING issue

⚠️ CRITICAL - additional_issue should be FALSE when:
- Customer is answering a question (e.g., "from the early morning" when asked "when did it start?")
- Customer is providing more details about the SAME issue
- Customer says "no" or "nothing" in response to a question
- Customer is clarifying or elaborating on the existing problem
- There is NO new problem being introduced

EXAMPLES:

Message: "My espresso machine stopped heating this morning. I tried turning it off and on but nothing. Can't serve customers now."
Extract:
- issue_summary: "Espresso machine not heating"
- issue_details: "Espresso machine stopped heating this morning. Customer tried power cycling but issue persists. Unable to serve customers."
- category: "equipment"
- urgency: "high"
- when_started: "this morning"
- what_tried: "turned it off and on"
- business_impact: "can't serve customers"
- additional_issue: false

Message: "We're about to run out of coffee in a few hours"
Extract:
- issue_summary: "Running out of coffee"
- issue_details: "Café will run out of coffee in a few hours"
- category: "order"
- urgency: "critical"
- business_impact: "will run out of coffee"
- additional_issue: false

Message: "My delivery hasn't arrived and I ordered it 3 days ago"
Extract:
- issue_summary: "Missing delivery"
- issue_details: "Delivery not received, ordered 3 days ago"
- category: "delivery"
- urgency: "critical"
- when_started: "ordered 3 days ago"
- additional_issue: false

Message: "My coffee tastes different today"
Extract:
- issue_summary: "Coffee tastes different"
- issue_details: "Coffee taste has changed from usual"
- category: "quality"
- urgency: "normal"
- when_started: "today"
- additional_issue: false

Message: "My staff are having trouble dialing in the espresso"
Extract:
- issue_summary: "Staff need help dialing in"
- issue_details: "Staff members having difficulty dialing in espresso"
- category: "training"
- urgency: "normal"
- additional_issue: false

Message: "The machine pressure is low and we can't serve customers"
Extract:
- issue_summary: "Low machine pressure interrupting service"
- issue_details: "Machine pressure is low, unable to serve customers"
- category: "machine"
- urgency: "high"
- business_impact: "can't serve customers"
- additional_issue: false

Message: "The milk keeps splitting and won't foam properly"
Extract:
- issue_summary: "Milk splitting and not foaming"
- issue_details: "Milk keeps splitting and won't foam properly"
- category: "milk"
- urgency: "normal"
- additional_issue: false

Message: "Our menu is too complex and staff are struggling with consistency"
Extract:
- issue_summary: "Menu complexity causing consistency issues"
- issue_details: "Menu is too complex, staff struggling with consistency"
- category: "menu"
- urgency: "normal"
- additional_issue: false

Message: "Also, my last delivery was 2 days late"
Extract:
- issue_summary: "Late delivery"
- issue_details: "Last delivery arrived 2 days late"
- category: "delivery"
- urgency: "normal"
- when_started: "last delivery"
- additional_issue: true (DIFFERENT issue from machine problem)

Message: "It started this morning" (answering when question about machine)
Extract:
- when_started: "this morning"
- additional_issue: false (answering question about EXISTING issue)

Message: "from the early morning" (answering when question)
Extract:
- when_started: "from the early morning"
- additional_issue: false (answering question about EXISTING issue)

Message: "No, I haven't noticed any error messages" (answering about machine)
Extract:
- additional_issue: false (answering question about EXISTING issue, not a new problem)

Message: "i have checked with everything" (answering troubleshooting question)
Extract:
- what_tried: "checked everything"
- additional_issue: false (answering question about EXISTING issue)

Message: "no that's it" (when asked if anything else)
Extract:
- additional_issue: false (explicitly saying NO to additional issues)

CRITICAL RULES FOR additional_issue:
1. additional_issue = true ONLY when customer introduces a BRAND NEW problem
2. additional_issue = false when: answering questions, providing details, clarifying, saying no/nothing
3. If customer is responding to a bot question, additional_issue should almost ALWAYS be false
4. Examples of TRUE: "Also my grinder broke", "And I have a billing issue too", "Plus my delivery was late"
5. Examples of FALSE: "from this morning", "no", "I tried everything", "it's not working", "no error messages"

Extract all available information from the message."""

        try:
            response = await self.llm_service.generate_response(
                messages=[{"role": "user", "content": extraction_prompt}],
                tools=self.extraction_function_def,
                tool_choice={"type": "function", "function": {"name": "extract_issue_data"}},
                temperature=0.0,
                max_tokens=400
            )
            
            # Check if function was called
            if response.get("type") == "function_call":
                function_args = json.loads(response["function_args"])
                
                # Filter out null values
                extracted = {k: v for k, v in function_args.items() if v and v != "null"}
                
                logger.info(f"LLM extracted issue fields: {list(extracted.keys())}")
                return extracted
            else:
                logger.warning("LLM did not call extraction function")
                return {}
                
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return {}
    
    def extract_issue_fallback(
        self,
        user_message: str,
        last_bot_message: str
    ) -> Dict:
        """
        Fallback extraction based on what bot just asked for
        
        Args:
            user_message: User's message
            last_bot_message: Bot's last message
        
        Returns:
            Dict with extracted field (if any)
        """
        if not last_bot_message:
            return {}
        
        bot_lower = last_bot_message.lower()
        extracted = {}
        
        # Check what bot asked for
        if any(phrase in bot_lower for phrase in ["when did", "when start", "when happen"]):
            extracted["when_started"] = user_message.strip()
            logger.info(f"Fallback extracted when_started: {user_message}")
        
        elif any(phrase in bot_lower for phrase in ["what have you tried", "tried so far", "already tried"]):
            extracted["what_tried"] = user_message.strip()
            logger.info(f"Fallback extracted what_tried: {user_message}")
        
        elif any(phrase in bot_lower for phrase in ["how is it affecting", "impact", "affecting your business"]):
            extracted["business_impact"] = user_message.strip()
            logger.info(f"Fallback extracted business_impact: {user_message}")
        
        elif any(phrase in bot_lower for phrase in ["tell me more", "what's happening", "describe", "explain"]):
            # Bot asked for more details
            if len(user_message.split()) > 5:
                extracted["issue_details"] = user_message.strip()
                logger.info(f"Fallback extracted issue_details: {user_message}")
        
        return extracted
    
    async def detect_problem_intent_with_llm(
        self,
        user_message: str,
        last_bot_message: str = "",
        has_existing_issue: bool = False
    ) -> Optional[Dict]:
        """
        Use LLM to detect if customer is reporting a problem
        
        Args:
            user_message: User's message
            last_bot_message: Bot's last message for context
            has_existing_issue: Whether customer already reported an issue
        
        Returns:
            Dict with has_problem, confidence, reasoning or None if failed
        """
        context = f"Bot just asked: {last_bot_message}\n" if last_bot_message else ""
        existing_context = "Customer already reported an issue earlier.\n" if has_existing_issue else ""
        
        detection_prompt = f"""{context}{existing_context}Customer said: "{user_message}"

Is the customer REPORTING A PROBLEM/ISSUE or just chatting/answering questions/acknowledging?

Examples of HAS PROBLEM (has_problem = true):
- "My espresso machine is broken" (first problem)
- "The coffee tastes burnt" (first problem)
- "My delivery was late" (first problem)
- "Also, my grinder stopped working" (additional problem)
- "Plus I have a billing issue" (additional problem)
- "And another thing, my order was wrong" (additional problem)

Examples of NO PROBLEM (has_problem = false):
- "Hi" / "Hello" / "Hey" (greeting)
- "It started this morning" (answering when question)
- "No, I haven't noticed any error messages" (answering question)
- "I tried restarting it" (providing details about existing issue)
- "Ok" / "Thanks" / "Got it" (acknowledging)
- "No, that's it" / "Nothing else" (done, no more issues)
- "Yes, please create a ticket" (confirming action)

CRITICAL: If customer is answering a question about an EXISTING issue, that's NOT a new problem (has_problem = false).
If customer mentions a COMPLETELY NEW/DIFFERENT problem, that IS a problem (has_problem = true).

Classify this message."""

        try:
            response = await self.llm_service.generate_response(
                messages=[{"role": "user", "content": detection_prompt}],
                tools=self.intent_detection_function_def,
                tool_choice={"type": "function", "function": {"name": "detect_customer_intent"}},
                temperature=0.0,
                max_tokens=150
            )
            
            if response.get("type") == "function_call":
                function_args = json.loads(response["function_args"])
                logger.info(f"LLM intent detection: has_problem={function_args['has_problem']} (confidence: {function_args['confidence']}, reason: {function_args['reasoning']})")
                return function_args
            else:
                logger.warning("LLM did not call intent detection function")
                return None
                
        except Exception as e:
            logger.error(f"LLM intent detection failed: {e}")
            return None


    async def classify_ticket_response_with_llm(
        self,
        user_message: str,
        last_bot_message: str
    ) -> Dict:
        """
        Classify user response to ticket creation offer
        
        Args:
            user_message: User's message
            last_bot_message: Bot's last message (asking about ticket)
            
        Returns:
            Dict with response_type, reasoning, new_topic
        """
        from app.services.inbound.bot_functions import inbound_bot_functions
        
        classification_prompt = f"""
        Bot asked: "{last_bot_message}"
        User replied: "{user_message}"
        
        Classify the user's response to the ticket offer.
        
        Examples:
        - "Yes please" -> CONFIRMING
        - "No, I want to buy beans" -> DECLINING (reason: wants sales, new_topic: sales)
        - "No, I fixed it" -> DECLINING (reason: fixed, new_topic: none)
        - "Actually, do you have cups?" -> DECLINING (reason: asking about products, new_topic: sales)
        - "Not now" -> DECLINING
        - "What is the price?" -> UNCLEAR (or DECLINING with new_topic: sales if asking about product price)
        """
        
        try:
            response = await self.llm_service.generate_response(
                messages=[{"role": "user", "content": classification_prompt}],
                tools=inbound_bot_functions.get_ticket_classification_definition(),
                tool_choice={"type": "function", "function": {"name": "classify_ticket_response"}},
                temperature=0.0,
                max_tokens=150
            )
            
            if response.get("type") == "function_call":
                function_args = json.loads(response["function_args"])
                logger.info(f"LLM ticket classification: {function_args}")
                return function_args
            else:
                logger.warning("LLM did not call classification function")
                return {"response_type": "UNCLEAR", "reasoning": "LLM failed to classify", "new_topic": "none"}
                
        except Exception as e:
            logger.error(f"LLM ticket classification failed: {e}")
            return {"response_type": "UNCLEAR", "reasoning": f"Error: {e}", "new_topic": "none"}


# Singleton instance
inbound_extraction_service = InboundExtractionService()
