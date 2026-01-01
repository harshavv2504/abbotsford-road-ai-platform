from typing import Dict, List
import json
from app.services.llm_service import llm_service
from app.services.rag.retriever import retriever
from app.services.inbound.prompt_handler import inbound_prompt_handler
from app.services.inbound.user_service import user_service
from app.services.inbound.bot_functions import inbound_bot_functions
from app.services.inbound.state_manager import InboundConversationState
from app.services.inbound.extraction_service import inbound_extraction_service
from app.services.inbound.bot_business_logic import inbound_bot_business_logic
from app.utils.logger import logger


class InboundBot:
    """Main orchestrator for inbound chatbot (customer support with extraction)"""
    
    def __init__(self):
        self.llm_service = llm_service
        self.retriever = retriever
        self.prompt_handler = inbound_prompt_handler
        self.user_service = user_service
        self.bot_functions = inbound_bot_functions
        self.extraction_service = inbound_extraction_service
        self.business_logic = inbound_bot_business_logic
    
    async def process_message(
        self,
        user_message: str,
        conversation_history: List[Dict],
        user_id: str,
        conversation_data: Dict
    ) -> str:
        """
        Process user message with structured extraction and response
        
        Args:
            user_message: User's message text
            conversation_history: List of previous messages
            user_id: Logged-in user ID
            conversation_data: Conversation metadata (will be converted to state)
        
        Returns:
            Bot response text
        """
        # Convert conversation_data dict to InboundConversationState
        state = InboundConversationState.from_dict(conversation_data)
        logger.info(f"Inbound conversation state: {state}")
        
        message_lower = user_message.lower().strip()
        
        # Check for goodbye phrases and conversation ending signals
        goodbye_phrases = ["bye", "goodbye", "see you", "talk later", "that's all", "that's it", "nothing else", "all set", "we're good", "i'm good", "thanks bye", "thank you bye"]
        ending_phrases = ["thanks", "thank you", "perfect", "great", "awesome", "sounds good", "got it", "ok thanks", "okay thanks"]
        
        # Direct goodbye
        if any(phrase in message_lower for phrase in goodbye_phrases):
            logger.info("User said goodbye - calling end_chat")
            farewell_type = "thanks" if "thank" in message_lower else "general"
            result = self.bot_functions.end_chat(farewell_type)
            conversation_data["should_close"] = True
            conversation_data.update(state.to_dict())
            return result["message"]
        
        # Check if user is just acknowledging after we've helped them
        if (any(phrase in message_lower for phrase in ending_phrases) and 
            len(user_message.split()) <= 3 and 
            (state.ticket_mentioned or state.create_ticket)):
            logger.info("User acknowledging after help - ending conversation")
            conversation_data["should_close"] = True
            conversation_data.update(state.to_dict())
            return self._clean_response_text("You're welcome! Have a great day!")
        
        # 1. Fetch user details for personalization
        user_details = await self.user_service.get_user_details(user_id)
        if user_details:
            logger.info(f"User: {user_details.get('name')} ({user_details.get('email')})")
        
        # Handle direct questions about user info
        if "what" in message_lower and "my name" in message_lower:
            if user_details and user_details.get("name"):
                return self._clean_response_text(f"Your name is {user_details['name']}!")
            else:
                return self._clean_response_text("I don't have your name on file. Could you tell me your name?")
        
        if "who am i" in message_lower or "what's my email" in message_lower or "my email" in message_lower:
            if user_details:
                parts = []
                if user_details.get("name"):
                    parts.append(f"You're {user_details['name']}")
                if user_details.get("email") and "email" in message_lower:
                    parts.append(f"your email is {user_details['email']}")
                if parts:
                    return self._clean_response_text(" and ".join(parts) + ".")
            return self._clean_response_text("I have your account information on file. How can I help you today?")
        
        # Get last bot message for context
        last_bot_message = ""
        if conversation_history:
            for msg in reversed(conversation_history):
                if 'bot' in msg:
                    last_bot_message = msg['bot']
                    break
        
        # ===== DETECT SPECIAL REQUESTS FIRST =====
        # Check for human escalation requests
        human_request_phrases = ["speak to someone", "talk to human", "connect me to support", "I want to speak", "get me someone", "human agent", "real person"]
        wants_human = any(phrase in message_lower for phrase in human_request_phrases)
        
        # Check for immediate solution requests (impatient users)
        solution_request_phrases = ["I want the solution now", "just fix it", "don't want to answer questions", "I need it fixed now", "give me the solution", "solve this now"]
        wants_immediate_solution = any(phrase in message_lower for phrase in solution_request_phrases)
        
        # Check for frustrated/angry customers
        frustrated_phrases = ["ridiculous", "terrible", "garbage", "awful", "worst", "hate this", "fed up", "sick of", "third time", "again and again"]
        is_frustrated = any(phrase in message_lower for phrase in frustrated_phrases)
        
        # Use LLM to detect if user refuses to share details or wants to skip questions
        refuses_details = False
        if last_bot_message and ("details" in last_bot_message.lower() or "share" in last_bot_message.lower() or "tell" in last_bot_message.lower()):
            # Only check if bot asked for information in the last message
            refusal_detection_prompt = f"""
            Bot asked: "{last_bot_message}"
            User replied: "{user_message}"
            
            Is the user refusing to share details, declining to answer questions, or asking to skip information gathering?
            
            Examples of refusal:
            - "I don't want to share anything"
            - "Just connect me to someone"
            - "I already told you I don't need help"
            - "No, just get me a person"
            - "Skip the questions"
            - "I'm not answering that"
            
            Answer only: YES or NO
            """
            
            try:
                refusal_response = await self.llm_service.generate_response(
                    messages=[{"role": "user", "content": refusal_detection_prompt}],
                    system_instruction="You are a classifier. Respond only with YES or NO.",
                    max_tokens=5
                )
                refuses_details = refusal_response.get("content", "").strip().upper() == "YES"
                logger.info(f"LLM refusal detection: {refuses_details}")
            except Exception as e:
                logger.error(f"Error in refusal detection: {e}")
                refuses_details = False
        
        # ===== LLM INTENT DETECTION =====
        # Use LLM to detect if customer is reporting a problem
        intent_result = await self.extraction_service.detect_problem_intent_with_llm(
            user_message,
            last_bot_message,
            has_existing_issue=bool(state.issue_summary)
        )
        
        has_problem = False
        if intent_result:
            has_problem = intent_result["has_problem"]
            logger.info(f"Customer has problem: {has_problem} (confidence: {intent_result['confidence']})")
        
        # ===== ISSUE EXTRACTION =====
        # Only run extraction if customer is reporting a problem
        if has_problem:
            is_first_problem = state.issue_summary is None
            logger.info(f"Running extraction (first_problem={is_first_problem})")
            extracted_data = await self.extraction_service.extract_issue_with_llm(
                user_message,
                conversation_history,
                existing_issue=state.issue_summary,
                is_first_problem=is_first_problem
            )
        else:
            logger.info("No problem detected - skipping extraction")
            extracted_data = {}
        
        logger.info(f"Extracted data: {list(extracted_data.keys()) if extracted_data else 'nothing'}")
        
        # ===== HANDLE EXTRACTED DATA =====
        is_urgent_delivery = False
        if extracted_data:
            # Check for urgent delivery scenario
            urgency = extracted_data.get("urgency")
            category = extracted_data.get("category")
            if urgency == "critical" and category in ["delivery", "order"]:
                is_urgent_delivery = True
                logger.info("URGENT DELIVERY SCENARIO DETECTED")
            
            # Check if this is an additional issue
            is_additional = extracted_data.get("additional_issue", False)
            
            if is_additional and state.issue_summary:
                # Customer mentioned ANOTHER issue
                logger.info("Customer mentioned additional issue")
                new_summary = extracted_data.get("issue_summary", "Additional issue")
                new_details = extracted_data.get("issue_details", user_message)
                state.add_additional_issue(new_summary, new_details)
                
                # Update category if provided
                if extracted_data.get("category"):
                    state.issue_category = extracted_data["category"]
                
            else:
                # First issue or updating existing issue
                if extracted_data.get("issue_summary"):
                    if not state.issue_summary:
                        state.issue_summary = extracted_data["issue_summary"]
                    # Don't overwrite if we already have a summary
                
                if extracted_data.get("issue_details"):
                    if not state.issue_details:
                        state.issue_details = extracted_data["issue_details"]
                    else:
                        # Append new details
                        state.issue_details += f"\n{extracted_data['issue_details']}"
                
                if extracted_data.get("category"):
                    state.issue_category = extracted_data["category"]
                
                # Store urgency
                if urgency:
                    state.issue_details = (state.issue_details or "") + f"\nUrgency: {urgency}"
                
                # Store additional context
                if extracted_data.get("when_started") and "when_started" not in (state.issue_details or ""):
                    state.issue_details = (state.issue_details or "") + f"\nStarted: {extracted_data['when_started']}"
                
                if extracted_data.get("what_tried") and "what_tried" not in (state.issue_details or ""):
                    state.issue_details = (state.issue_details or "") + f"\nAttempted: {extracted_data['what_tried']}"
                
                if extracted_data.get("business_impact") and "business_impact" not in (state.issue_details or ""):
                    state.issue_details = (state.issue_details or "") + f"\nImpact: {extracted_data['business_impact']}"
            
            logger.info(f"State after extraction: summary={state.issue_summary}, details_len={len(state.issue_details or '')}")
        
        # FALLBACK: If no problem detected but we have existing issue, try fallback extraction
        # (customer might be answering questions about existing issue)
        if not has_problem and state.issue_summary and last_bot_message:
            fallback_data = self.extraction_service.extract_issue_fallback(
                user_message,
                last_bot_message
            )
            if fallback_data:
                logger.info(f"Fallback extracted: {list(fallback_data.keys())}")
                # Append fallback data to issue_details
                for key, value in fallback_data.items():
                    if key == "issue_details" and not state.issue_details:
                        state.issue_details = value
                    elif key in ["when_started", "what_tried", "business_impact"]:
                        state.issue_details = (state.issue_details or "") + f"\n{key}: {value}"
        
        # ===== CHECK IF CUSTOMER IS CONFIRMING TICKET CREATION =====
        if state.ticket_confirmation_pending:
            # Use structured LLM function calling for robust classification
            classification = await self.extraction_service.classify_ticket_response_with_llm(
                user_message,
                last_bot_message
            )
            
            response_type = classification.get("response_type", "UNCLEAR")
            new_topic = classification.get("new_topic", "none")
            reasoning = classification.get("reasoning", "")
            
            logger.info(f"Ticket classification: {response_type}, New Topic: {new_topic}, Reason: {reasoning}")
            
            if response_type == "CONFIRMING":
                state.confirm_ticket()
                state.ticket_mentioned = True  # Mark as mentioned to prevent re-asking
                logger.info("Customer confirmed ticket creation")
            elif response_type == "DECLINING":
                state.decline_ticket()
                logger.info("Customer declined ticket creation")
                
                # Handle topic switching if user declined but wants something else
                if new_topic != "none":
                    logger.info(f"User switching topic to: {new_topic}")
                    # We don't need to do anything special here, the normal flow will 
                    # pick up the new topic in the next steps (intent detection/extraction)
                    # But we should ensure we don't force a "ticket declined" response if they moved on
                    state.ticket_declined = False  # Reset this so we don't give a "declined" message
            
            # If UNCLEAR, we continue normal conversation flow
        
        # ===== CHECK IF CONVERSATION IS COMPLETE (BEFORE BUILDING CONTEXT) =====
        # If no problem detected AND (ticket was mentioned OR conversation was already closed)
        conversation_complete = not has_problem and (state.ticket_mentioned or state.conversation_closed)
        if conversation_complete:
            logger.info("Conversation complete - customer just acknowledging")
        
        # ===== DETERMINE NEXT ACTION =====
        # Check if we should ask clarifying questions (but NOT if no problem detected)
        should_clarify = False
        clarifying_question = None
        
        if state.issue_summary and state.issue_details and (has_problem or (last_bot_message and "?" in last_bot_message)):
            # We have basic issue info - check if we need more details
            # Run this if problem detected OR if user is likely answering a previous question
            should_clarify = self.business_logic.should_ask_clarifying_question(
                state.issue_details,
                state.questions_asked
            )
            
            if should_clarify:
                category = state.issue_category or self.business_logic.categorize_issue(state.issue_details)
                clarifying_question = self.business_logic.get_clarifying_question(category, state.issue_details)
                state.increment_questions()
                logger.info(f"Asking clarifying question #{state.questions_asked}: {clarifying_question}")
        
        # ===== BUILD CONTEXT FOR LLM =====
        context_parts = []
        
        # Check if this is the first message (greeting)
        is_first_message = len(conversation_history) == 0 or (len(conversation_history) == 1 and 'user' in conversation_history[0])
        greeting_words = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
        is_greeting = any(word in message_lower for word in greeting_words) and len(user_message.split()) <= 3
        
        if is_first_message and is_greeting and user_details and user_details.get("name"):
            context_parts.append(f"FIRST MESSAGE: Customer just greeted you. Respond with: 'Hi {user_details['name']}! How can I help you today?' (or similar, using their name)")
        
        # Add RAG context if it's a question
        question_indicators = ['?', 'what', 'how', 'why', 'when', 'where', 'do you', 'can you', 'tell me']
        is_question = any(indicator in message_lower for indicator in question_indicators)
        
        # Detect out-of-scope questions (competitors, non-ARC topics)
        out_of_scope_keywords = ['starbucks', 'dunkin', 'costa', 'peet', 'competitor', 'weather', 'news', 'politics', 'sports']
        is_out_of_scope = any(keyword in message_lower for keyword in out_of_scope_keywords)
        
        if is_question:
            relevant_docs = self.retriever.retrieve(user_message, k=3)
            if relevant_docs:
                rag_context = self.retriever.format_context_for_llm(relevant_docs)
                context_parts.append(f"Knowledge base:\n{rag_context}")
                
                # For out-of-scope questions, add specific redirect instruction
                if is_out_of_scope and not has_problem and not state.issue_summary:
                    context_parts.append("OUT-OF-SCOPE QUERY: Customer asked about a competitor or non-ARC topic. Give a BRIEF neutral answer (1 sentence), then IMMEDIATELY redirect to ARC: 'How can I help with your Abbotsford Road Coffee needs today?' or 'Are you looking for something specific from our range?' DO NOT engage further on the out-of-scope topic.")
                # Topic switch during active troubleshooting
                elif not has_problem and state.issue_summary:
                    context_parts.append(f"TOPIC SWITCH DURING TROUBLESHOOTING: Customer asked a general question while you're helping with their '{state.issue_summary}' issue. You MUST: 1) Answer their question briefly (1-2 sentences), 2) Then IMMEDIATELY return to troubleshooting with a follow-up question about the equipment issue. Example format: '[Answer about syrups]. Now, back to your equipment - [specific troubleshooting question]?' This keeps both topics flowing naturally.")
                # For general product/info queries (not problems), keep responses concise
                elif not has_problem and not state.issue_summary:
                    context_parts.append("GENERAL QUERY: This is a product/info question, not a problem. Give the answer in EXACTLY 1 SENTENCE (under 30 words), FOCUS ON KEY POINTS ONLY (roast level, main flavors, best use), then ask a brief follow-up. NO new lines or paragraphs in the answer.")
        
        # Add issue tracking context with immediate help approach
        if state.issue_summary:
            context_parts.append(f"Issue identified: {state.issue_summary}")
            if state.issue_details:
                context_parts.append(f"Details collected: {len(state.issue_details)} chars")
            
            # Detect specific café-support scenarios
            issue_lower = state.issue_summary.lower()
            
            # SCENARIO 1: Coffee tastes different
            if any(word in issue_lower for word in ["taste", "different", "flavor", "bitter", "weak", "sour"]):
                if not state.ticket_mentioned and state.questions_asked < 2:
                    context_parts.append("SCENARIO 1 - COFFEE TASTES DIFFERENT: Acknowledge calmly: 'This happens sometimes — we can fix it with a few quick checks.' Provide simple checks (grind position, dose consistency, shot time). Use correct coffee science: finer grind = slower flow = stronger, coarser grind = faster flow = weaker. After guidance, ask ONCE: 'Would you like me to create a support case so the team can take a closer look?' Collect: Café name, location, order details.")
                elif state.ticket_mentioned:
                    context_parts.append("SCENARIO 1 - CASE CREATED: Support case already mentioned. DO NOT ask more troubleshooting questions. End with: 'The team will follow up shortly. I'm here if you need anything else.'")
            
            # SCENARIO 2: Staff need help dialing in
            elif any(word in issue_lower for word in ["staff", "dial", "training", "barista"]):
                if not state.ticket_mentioned and state.questions_asked < 2:
                    context_parts.append("SCENARIO 2 - STAFF DIALING IN: Acknowledge supportively: 'Dialing in can be tricky on busy shifts, we can keep it simple.' Ask ONE question: 'Are the shots running too fast, too slow, or does the taste seem off (sour/bitter)?' Provide symptom-based logic and simple base recipe (18g in → 36-40g out → 25-30s). After guidance, ask ONCE: 'Would you like a simple dialing-in guide for your staff?' Collect: Café name, location, machine + grinder, blend.")
                elif state.ticket_mentioned:
                    context_parts.append("SCENARIO 2 - CASE CREATED: Support case already mentioned. DO NOT ask more troubleshooting questions. End with: 'The team will follow up shortly. I'm here if you need anything else.'")
            
            # SCENARIO 4: Machine issues interrupting service
            elif any(word in issue_lower for word in ["pressure", "temperature", "steam wand", "group head", "machine"]) and state.issue_category == "machine":
                if not state.ticket_mentioned and state.questions_asked < 2:
                    context_parts.append("SCENARIO 4 - MACHINE ISSUES: Ask ONE question: 'Is the issue with pressure, temperature, steam wand, group head flow, or grinder feeding?' Keep troubleshooting simple (cleaning, flushing, purging, calibration). Emphasize: 'Most of the time this is calibration/cleaning, not a broken machine.' Provide 1-2 quick fixes. If unresolved, offer support case. Collect: Café name, location, machine model.")
                elif state.ticket_mentioned:
                    context_parts.append("SCENARIO 4 - CASE CREATED: Support case already mentioned. DO NOT ask more troubleshooting questions. End with: 'The team will follow up shortly. I'm here if you need anything else.'")
            
            # SCENARIO 5: Milk / alternative milk issues
            elif any(word in issue_lower for word in ["milk", "foam", "froth", "texture", "splitting", "stretching"]):
                if not state.ticket_mentioned and state.questions_asked < 2:
                    context_parts.append("SCENARIO 5 - MILK ISSUES: Ask ONE question: 'Is the milk too thin, splitting, too foamy, or not stretching?' Provide simple tips (lower steaming temp, consistent technique, check plant milks, try fresh carton). If unresolved, offer support case. Collect: Café name, location, milk type.")
                elif state.ticket_mentioned:
                    context_parts.append("SCENARIO 5 - CASE CREATED: Support case already mentioned. DO NOT ask more troubleshooting questions. End with: 'The team will follow up shortly. I'm here if you need anything else.'")
            
            # SCENARIO 6: Menu problems
            elif any(word in issue_lower for word in ["menu", "recipe", "complex", "struggle", "sku"]):
                if not state.ticket_mentioned and state.questions_asked < 2:
                    context_parts.append("SCENARIO 6 - MENU PROBLEMS: If user hints at recurring issues, say: 'Sometimes menu complexity can cause inconsistency. Are there any drinks that staff struggle with regularly?' Offer simple recipe standardization and guidance on simplifying menu flow. If revising menu, offer support case. Collect: Café name, location, menu details, problematic drinks.")
                elif state.ticket_mentioned:
                    context_parts.append("SCENARIO 6 - CASE CREATED: Support case already mentioned. DO NOT ask more troubleshooting questions. End with: 'The team will follow up shortly. I'm here if you need anything else.'")
            
            # Check if we already have the main issue details to avoid repeating questions
            elif state.ticket_mentioned:
                context_parts.append("ISSUE ALREADY DISCUSSED: You already know about their issue and mentioned creating a ticket. DO NOT ask about the machine issue again. Focus on next steps or closing the conversation.")
            elif state.issue_details and len(state.issue_details) > 50:  # Only if we have substantial details
                immediate_help = self._get_immediate_troubleshooting(state.issue_summary, state.issue_category)
                if immediate_help:
                    context_parts.append(f"PROVIDE HELP: {immediate_help}")
            else:
                # Not enough details yet - focus on gathering information
                context_parts.append("GATHER MORE INFO: Ask specific questions to understand the problem better. Don't mention tickets yet.")
        
        # ===== HANDLE SPECIAL REQUESTS FIRST =====
        # Handle urgent delivery scenario (SCENARIO 3)
        if is_urgent_delivery:
            logger.info("Handling urgent delivery scenario - immediate escalation")
            state.create_ticket = True
            state.ticket_mentioned = True
            context_parts.append("URGENT DELIVERY SCENARIO: Customer is running out of coffee or has missing delivery. Respond with priority tone: 'Thanks for flagging this quickly — let's sort it out fast.' Ask ONLY essential questions (order number/date, tracking email received). If confirmed (no tracking, not delivered, running out soon), escalate directly: 'I'll escalate this to the team immediately so they can chase the shipment or arrange urgent replacement.' After creating support case, DO NOT ask more tracking questions. Close politely.")
        
        # Handle human escalation requests
        elif wants_human:
            logger.info("Customer wants human contact - creating priority ticket")
            state.create_ticket = True
            state.ticket_mentioned = True
            # Check if we already asked for details to avoid repetition
            already_asked_details = any("details" in msg.get("bot", "").lower() or "share" in msg.get("bot", "").lower() for msg in conversation_history[-3:])
            if already_asked_details:
                context_parts.append("HUMAN ESCALATION (NO REPEAT): Customer wants to speak to someone and you already asked for details. Simply confirm: priority case created, team will reach out shortly. DO NOT ask for details again or mention contact methods.")
            else:
                context_parts.append("HUMAN ESCALATION: Customer wants to speak to someone. Acknowledge their request immediately, confirm you're creating a priority case and connecting them to the team. Mention the team will reach out shortly. DO NOT ask for contact preferences (call/zoom) - our team will decide.")
        
        # Handle immediate solution requests
        elif wants_immediate_solution and state.issue_summary:
            logger.info("Customer wants immediate solution - providing direct help")
            immediate_help = self._get_immediate_troubleshooting(state.issue_summary, state.issue_category)
            if immediate_help:
                context_parts.append(f"IMMEDIATE SOLUTION: Customer doesn't want questions. Acknowledge their urgency, provide immediate help: {immediate_help}, and mention creating a priority case for follow-up. Be direct and action-oriented.")
                state.create_ticket = True
        
        # Check for general negative responses to troubleshooting suggestions
        elif last_bot_message and any(word in last_bot_message.lower() for word in ["try", "check", "restart", "steps"]):
            # Bot suggested troubleshooting, check if user declined
            negative_response_prompt = f"""
            Bot suggested: "{last_bot_message}"
            User replied: "{user_message}"
            
            Is the user declining or refusing to try the suggested troubleshooting steps?
            
            Examples of declining:
            - "I already tried that"
            - "That won't work"
            - "I don't want to do that"
            - "Skip the troubleshooting"
            - "Just send someone"
            
            Answer only: YES or NO
            """
            
            try:
                negative_response = await self.llm_service.generate_response(
                    messages=[{"role": "user", "content": negative_response_prompt}],
                    system_instruction="You are a classifier. Respond only with YES or NO.",
                    max_tokens=5
                )
                declines_troubleshooting = negative_response.get("content", "").strip().upper() == "YES"
                logger.info(f"LLM troubleshooting decline detection: {declines_troubleshooting}")
                
                if declines_troubleshooting:
                    logger.info("Customer declined troubleshooting - offering alternatives")
                    if not state.ticket_mentioned:
                        state.create_ticket = True
                        state.ticket_mentioned = True
                        context_parts.append("TROUBLESHOOTING DECLINED: Customer doesn't want to try troubleshooting steps. Acknowledge their preference, offer to create a priority case for direct support, and ask if there's anything else you can help with immediately.")
                    else:
                        context_parts.append("TROUBLESHOOTING DECLINED (REPEAT): Customer already declined troubleshooting and you mentioned support. Give brief acknowledgment like 'Understood, our team will handle this directly' and ask if there's anything else.")
            except Exception as e:
                logger.error(f"Error in negative response detection: {e}")
        
        # Handle users who refuse to share details
        elif refuses_details:
            logger.info("Customer refuses to share details - respecting their decision")
            if not state.ticket_mentioned:
                state.create_ticket = True
                state.ticket_mentioned = True
                context_parts.append("USER REFUSES DETAILS: Customer doesn't want to share details. Respect their decision. Simply confirm: priority case created, team will reach out shortly. DO NOT ask for more information or contact preferences.")
            else:
                context_parts.append("USER REFUSES DETAILS (REPEAT): Customer already refused details and you mentioned the ticket. Give a brief acknowledgment like 'Understood, our team will contact you shortly' or 'No problem, you'll hear from us soon.' DO NOT ask for anything more.")
        
        # Handle frustrated customers
        elif is_frustrated:
            logger.info("Customer is frustrated - providing empathetic response")
            if state.issue_summary:
                immediate_help = self._get_immediate_troubleshooting(state.issue_summary, state.issue_category)
                context_parts.append(f"FRUSTRATED CUSTOMER: Show genuine empathy, acknowledge their frustration, take ownership of making it right, mention escalating as priority, and provide immediate help: {immediate_help or 'arrange for team contact'}. Be understanding and action-focused.")
                state.create_ticket = True
            else:
                context_parts.append("FRUSTRATED CUSTOMER: Show genuine empathy, acknowledge their frustration, take ownership of the situation, and ask what's happening so you can escalate properly. Be understanding and supportive.")
        
        # Check if customer indicated they're done
        elif conversation_complete:
            # Customer is just acknowledging - give brief response WITHOUT ticket info
            logger.info("Conversation complete - instructing brief acknowledgment only")
            context_parts.append("CRITICAL: Customer is just acknowledging (said 'ok', 'thanks', 'thank you', etc.). Give ONLY a brief friendly response: 'You're welcome!', 'Happy to help!', 'Anytime!', or 'Take care!'. NOTHING ELSE. NO ticket words. NO issue details. NO apologies. NO offers to create tickets. ONE sentence only.")
        
        # Handle negative responses that aren't acknowledgments
        elif message_lower in ["no", "nope", "no i dont", "i dont", "nothing", "none"]:
            logger.info("Customer gave negative response - not an acknowledgment")
            if state.ticket_mentioned:
                context_parts.append("NEGATIVE RESPONSE AFTER TICKET: Customer said no/nothing after ticket was mentioned. Respond with: 'Understood. Our team will contact you shortly.' Do not ask more questions.")
            else:
                context_parts.append("NEGATIVE RESPONSE: Customer said no/nothing. Acknowledge and offer to create a support case: 'No problem. Should I create a support case for our team to help you directly?'")
        elif state.create_ticket and not state.ticket_mentioned:
            # Customer confirmed ticket creation - acknowledge it with full context
            context_parts.append("SUPPORT CASE CONFIRMATION: Customer confirmed ticket creation. Respond with: 'The team will follow up shortly. I'm here if you need anything else.' DO NOT ask more troubleshooting questions. DO NOT repeat support case prompts. Conversation should close after this.")
            state.ticket_mentioned = True
        elif state.ticket_declined:
            # Customer declined ticket - acknowledge and offer help
            context_parts.append("Customer declined ticket. Acknowledge their choice positively and ask what else you can try to help them. Be supportive and solution-focused.")
        elif not has_problem and state.issue_summary and not state.ticket_mentioned and not state.ticket_confirmation_pending and not state.ticket_declined:
            # Customer has no new problem but we have an issue and haven't asked about ticket yet
            context_parts.append("Customer seems done with troubleshooting. Ask if they'd like you to create a case with the troubleshooting steps you've tried. Be helpful and offer it as a useful option.")
        # Check if we already told customer about ticket and they're just acknowledging
        elif state.ticket_mentioned and not extracted_data:
            # No new data extracted and ticket already mentioned - likely just acknowledging
            context_parts.append("CRITICAL: You already told customer about support case. Customer is likely just acknowledging. Give a BRIEF, DIFFERENT response like 'You're welcome!' or 'Happy to help!' - DO NOT repeat ticket information. DO NOT ask more troubleshooting questions. DO NOT mention support case again.")
        
        # Add clarifying question instruction
        if should_clarify and clarifying_question:
            context_parts.append(f"Ask this clarifying question: {clarifying_question}")
        elif state.issue_summary and state.issue_details and not state.ticket_confirmation_pending and not state.ticket_mentioned and not state.create_ticket and not state.ticket_declined:
            # Have enough info and haven't asked about ticket yet - ASK for confirmation
            context_parts.append("Enough information collected. Ask if they'd like you to create a support case with all the details and troubleshooting steps. Present it as a helpful option for getting expert assistance.")
        
        # Add response style instruction
        if context_parts:
            # Check if this is an out-of-scope query
            if is_out_of_scope and is_question and not has_problem and not state.issue_summary:
                context_parts.append("CRITICAL OVERRIDE: This is an OUT-OF-SCOPE question about competitors or non-ARC topics. You MUST respond with: '[Brief neutral answer in 1 sentence]. How can I help with your Abbotsford Road Coffee needs today?' DO NOT elaborate on the out-of-scope topic. IMMEDIATELY pivot to ARC services.")
            # Check if this is a general query and add specific instruction at the end
            elif is_question and not has_problem and not state.issue_summary:
                context_parts.append("CRITICAL OVERRIDE: This is a GENERAL PRODUCT QUESTION. You MUST respond with EXACTLY this format: '[Answer in 1 sentence with key points]. [Context-aware follow-up question]' EXAMPLES: For blends → 'Want to know about a specific blend?' For CEO → 'Need any other company info?' For products → 'Interested in any particular one?' IGNORE detailed knowledge base info - use ONLY key points.")
            elif has_problem or state.issue_summary:
                context_parts.append("PROBLEM RESPONSE: Start with a CONTEXT-AWARE question to understand their specific issue. Examples: Machine problems → 'What type of machine issue?' / Leakage → 'What's leaking from the machine?' / Order issues → 'What's happening with your order?' / Quality problems → 'What's wrong with the taste?'. FOCUS ON GATHERING DETAILS first. DO NOT make assumptions (like assuming water is leaking when they just said 'leakage'). DO NOT mention tickets, cases, or support team until you have a complete understanding of the problem. AVOID repetitive phrases.")
            else:
                context_parts.append("TONE: Be concise and direct. Vary your opening phrases. Keep responses under 2 sentences when possible.")
        
        # Add conversation context to prevent repetition
        if state.issue_summary and len(conversation_history) > 4:
            context_parts.append(f"CONVERSATION CONTEXT: You already know about their {state.issue_summary} issue. DO NOT ask 'What type of machine issue?' or repeat questions about the same problem. Focus on next steps or solutions.")
        
        # Build formatted message
        if context_parts:
            formatted_message = "\n\n".join(context_parts) + f"\n\nCustomer: {user_message}"
        else:
            formatted_message = user_message
        
        # ===== BUILD MESSAGE HISTORY =====
        messages = self._build_message_history(conversation_history, formatted_message)
        
        # ===== GET SYSTEM INSTRUCTION =====
        if user_details:
            system_instruction = self.prompt_handler.get_system_instruction(
                user_name=user_details.get("name"),
                customer_since=user_details.get("customer_since"),
                city=user_details.get("city"),
                country=user_details.get("country"),
                coffee_style=user_details.get("coffee_style"),
                current_serving_capacity=user_details.get("current_serving_capacity")
            )
        else:
            system_instruction = self.prompt_handler.get_system_instruction()
        
        # ===== GENERATE RESPONSE =====
        # Use fewer tokens for general queries to keep them concise
        max_tokens = 50 if (is_question and not has_problem and not state.issue_summary) else 80
        logger.info(f"Generating response (max_tokens={max_tokens})")
        response = await self.llm_service.generate_response(
            messages=messages,
            system_instruction=system_instruction,
            max_tokens=max_tokens
        )
        
        response_text = response.get("content", "I'm here to help! How can I assist you?")
        
        # Clean up response text - remove unwanted line breaks and extra spaces
        response_text = self._clean_response_text(response_text)
        
        logger.info(f"Bot response: {response_text[:100]}...")
        
        # ===== CHECK IF TICKET SHOULD BE CREATED =====
        # Mark ticket_mentioned when we CONFIRM creation (not when we ASK)
        if "ticket will be created" in response_text.lower() or "a ticket will be created" in response_text.lower():
            if not state.ticket_mentioned:
                state.ticket_mentioned = True
                logger.info("Bot confirmed ticket creation - marked as mentioned")
            # Also confirm ticket if it was pending
            if state.ticket_confirmation_pending:
                state.confirm_ticket()
        elif ("would you like" in response_text.lower() or "want me to create" in response_text.lower()) and "ticket" in response_text.lower() and not state.ticket_confirmation_pending:
            state.mark_ticket_pending()
            logger.info("Bot asked for ticket confirmation - marked as pending")
        
        # Update conversation_data with final state
        conversation_data.update(state.to_dict())
        logger.info(f"Updated state: {state}")
        
        # Return response content
        return response_text
    
    def _build_message_history(self, conversation_history: List[Dict], current_message: str) -> List[Dict]:
        """Build message history for LLM"""
        messages = []
        
        # Add previous messages (limit to last 10 for context window)
        for msg in conversation_history[-10:]:
            # Handle both formats: {'user': '...'} or {'speaker': 'user', 'text': '...'}
            if 'user' in msg:
                messages.append({
                    "role": "user",
                    "content": msg['user']
                })
            elif 'bot' in msg:
                messages.append({
                    "role": "assistant",
                    "content": msg['bot']
                })
            elif 'speaker' in msg and 'text' in msg:
                role = "user" if msg['speaker'] == 'user' else "assistant"
                messages.append({
                    "role": role,
                    "content": msg['text']
                })
        
        # Add current message
        messages.append({
            "role": "user",
            "content": current_message
        })
        
        return messages
    
    def _get_immediate_troubleshooting(self, issue_summary: str, issue_category: str) -> str:
        """Get immediate troubleshooting steps based on issue"""
        
        if not issue_summary:
            return ""
        
        issue_lower = issue_summary.lower()
        category_lower = (issue_category or "").lower()
        
        # SCENARIO 1: Coffee tastes different today
        if any(word in issue_lower for word in ["taste", "different", "flavor", "bitter", "weak", "sour"]):
            if "bitter" in issue_lower:
                return "For bitter taste: 1) Grind coarser (less resistance, faster flow) 2) Check shot time (should be 25-30s, not >35s) 3) Reduce dose slightly. Remember: finer grind = slower flow = more extraction = bitter."
            elif "weak" in issue_lower or "under" in issue_lower:
                return "For weak taste: 1) Grind finer (more resistance, slower flow) 2) Check shot time (should be 25-30s, not <20s) 3) Increase dose slightly. Remember: coarser grind = faster flow = less extraction = weak."
            elif "sour" in issue_lower:
                return "For sour taste: 1) Grind finer for longer extraction 2) Increase shot time to 25-30s 3) Check water temperature (should be 195-205°F)."
            else:
                return "Quick checks: 1) Check if grind moved a click 2) Confirm dose is consistent 3) Verify shot time is in usual range (25-30s)."
        
        # SCENARIO 2: Staff need help dialing in
        if any(word in issue_lower for word in ["staff", "dial", "training", "barista", "employee"]):
            return "Simple base recipe for consistency: 18g in → 36-40g out → 25-30 seconds. Fast shots (~15s)? Grind finer, stable dose, level tamp. Slow shots? Grind coarser, slightly lower dose. Taste sour? Grind finer. Taste bitter? Grind coarser."
        
        # SCENARIO 3: Urgent stock / missing delivery
        if any(word in issue_lower for word in ["run out", "almost out", "urgent", "emergency", "not delivered", "missing"]):
            return "I'll escalate this right away so the team can chase the shipment or arrange urgent replacement."
        
        # SCENARIO 4: Machine issues interrupting service
        if "machine" in category_lower or any(word in issue_lower for word in ["pressure", "temperature", "steam wand", "group head", "flow"]):
            if "pressure" in issue_lower:
                return "For pressure issues: 1) Check if machine needs cleaning 2) Flush group heads 3) Confirm routine calibration. Most of the time this is calibration/cleaning, not a broken machine."
            elif "temperature" in issue_lower or "temp" in issue_lower:
                return "For temperature issues: 1) Check water tank level 2) Run cleaning cycle 3) Check for error lights. Most of the time this is calibration/cleaning, not a broken machine."
            elif "steam" in issue_lower:
                return "For steam wand issues: 1) Purge steam wand 2) Check for milk residue blockage 3) Clean steam tip. Most of the time this is cleaning, not a broken machine."
            elif "group" in issue_lower:
                return "For group head issues: 1) Flush group heads 2) Run cleaning cycle 3) Check for blockages. Most of the time this is cleaning, not a broken machine."
            elif "grinder" in issue_lower and ("feed" in issue_lower or "jam" in issue_lower):
                return "For grinder feeding issues: 1) Check hopper for blockages 2) Clear any jammed beans 3) Check hopper gate is open. Most of the time this is a simple fix."
            else:
                return "Most of the time machine issues are calibration/cleaning, not a broken machine. Try: 1) Run cleaning cycle 2) Flush group heads 3) Check for blockages."
        
        # SCENARIO 5: Milk / alternative milk issues
        if "milk" in category_lower or any(word in issue_lower for word in ["milk", "foam", "froth", "texture", "splitting", "stretching"]):
            if "thin" in issue_lower or "split" in issue_lower:
                return "For thin/splitting milk: 1) Lower steaming temperature 2) Use consistent stretching technique 3) Try a fresh carton 4) Check if only plant milks are affected."
            elif "foam" in issue_lower or "stretch" in issue_lower:
                return "For foaming/stretching issues: 1) Lower steaming temperature 2) Use consistent stretching technique 3) Check if only plant milks are affected 4) Try different milk brand."
            else:
                return "For milk consistency: 1) Lower steaming temperature 2) Consistent stretching technique 3) Try a fresh carton 4) Check if only plant milks are affected."
        
        # SCENARIO 6: Menu problems
        if "menu" in category_lower or any(word in issue_lower for word in ["menu", "recipe", "complex", "struggle"]):
            return "Menu complexity can cause inconsistency. Consider: 1) Simple recipe standardization 2) Reducing complex drinks 3) Training on problematic drinks. Would you like guidance on simplifying menu flow?"
        
        # Equipment troubleshooting (general)
        if "equipment" in category_lower or any(word in issue_lower for word in ["equipment", "grinder"]):
            if any(word in issue_lower for word in ["heating", "heat", "hot"]):
                return "Try these steps: 1) Check power and water tank 2) Restart machine 3) Check water filter. If still not heating, use stovetop as backup."
            
            elif any(word in issue_lower for word in ["grinder", "grinding"]):
                return "Quick fixes: 1) Clear any jammed beans 2) Clean burr chamber 3) Try coarser setting 4) Different outlet. Use pre-ground coffee if needed."
            
            elif any(word in issue_lower for word in ["espresso", "coffee machine", "brewing"]):
                return "Check: 1) Water tank and power 2) Run cleaning cycle 3) Any error lights? 4) Try different outlet."
        
        # Quality issues (general)
        elif "quality" in category_lower:
            return "Adjust: 1) Grind size (coarser if bitter, finer if weak) 2) Water temp 195-205°F 3) Coffee ratio 1:15 4) Check bean freshness."
        
        # Order/delivery issues
        elif any(word in issue_lower for word in ["order", "delivery", "shipment"]):
            return "Check: 1) Email for tracking 2) Delivery address correct 3) Reception/neighbors received it."
        
        # Generic equipment issue
        elif any(word in issue_lower for word in ["broken", "not working", "stopped", "failed"]):
            return "Try: 1) Check power 2) Different outlet 3) Look for error messages 4) Restart device."
        
        return "I'll help troubleshoot while creating your support case."
    
    def _clean_response_text(self, text: str) -> str:
        """Clean response text to remove unwanted formatting"""
        if not text:
            return text
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Replace multiple spaces and newlines with single space
        text = ' '.join(text.split())
        
        # Remove any remaining line breaks
        text = text.replace('\n', ' ').replace('\r', ' ')
        
        return text


# Singleton instance
inbound_bot = InboundBot()
