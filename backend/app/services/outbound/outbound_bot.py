"""
Outbound Bot - Main Orchestrator

What it does:
- Coordinates the full outbound conversation turn: quick exits (goodbye), early intents,
  RAG Q&A routing, extraction/validation pipeline, qualification completion, and general response.

If you change it:
- You affect the overall flow/order of decision-making for every message. Keep side effects confined to
  state updates and delegate specific logic to `core/flow_controller.py` and `core/extraction_pipeline.py`.
  Modify here when you need to change orchestration order or add/remove a step.
"""

from typing import Dict, List
from app.services.outbound.bot_functions import outbound_bot_functions
from app.services.outbound.state_manager import ConversationState
from app.services.outbound.validation_service import validation_service
from app.services.outbound.extraction_service import extraction_service
from app.services.outbound.rag_handler import rag_handler
from app.services.outbound.customer_type_detector import customer_type_detector
from app.services.outbound.question_generator import question_generator
from app.services.outbound.response_builder import response_builder
from app.utils.logger import logger
from app.services.outbound.core.flow_controller import FlowController
from app.services.outbound.core.extraction_pipeline import ExtractionPipeline


class OutboundBot:
    """
    Main orchestrator for outbound chatbot (lead generation).
    
    Changing this class impacts how all sub-services are wired and the final response path. Prefer
    adding new steps via `FlowController` and keep this class thin.
    """
    
    def __init__(self):
        # Service dependencies
        self.bot_functions = outbound_bot_functions
        self.validation_service = validation_service
        self.extraction_service = extraction_service
        self.rag_handler = rag_handler
        self.customer_type_detector = customer_type_detector
        self.question_generator = question_generator
        self.response_builder = response_builder
        
        self.extraction_pipeline = ExtractionPipeline(
            extraction_service=self.extraction_service,
            validation_service=self.validation_service,
            question_generator=self.question_generator,
        )
        self.flow_controller = FlowController(
            customer_type_detector=self.customer_type_detector,
            rag_handler=self.rag_handler,
            question_generator=self.question_generator,
            extraction_service=self.extraction_service,
            validation_service=self.validation_service,
            bot_functions=self.bot_functions,
            extraction_pipeline=self.extraction_pipeline,
        )
    
    def get_next_field_question(self, state: ConversationState, prefix: str = "") -> Dict:
        """
        Get the next qualification question with tracking/skipping rules.
        
        Changing this alters how we prompt users during qualification sequencing.
        Returns a dict: {"response": str, "should_end": bool} or None when complete.
        """
        # BUG-012 FIX: Don't ask more questions if human connection is confirmed
        if state.human_connection_confirmed:
            logger.info("⚠️ BUG-012 FIX: Skipping qualification - human connection already confirmed")
            return None
        
        missing_fields = state.get_missing_fields(state.customer_type)
        
        # BUG-008 FIX: Filter out topics that were already discussed
        if missing_fields:
            original_count = len(missing_fields)
            missing_fields = [f for f in missing_fields if not state.was_topic_discussed(f)]
            if len(missing_fields) < original_count:
                logger.info(f"⚠️ BUG-008 FIX: Filtered out {original_count - len(missing_fields)} already-discussed topics")
        
        if not missing_fields:
            # No more fields needed
            return None
        
        next_field = missing_fields[0]
        
        # Track that we're asking for this field
        ask_count = state.track_field_ask(next_field)
        
        # Check if we should skip this field (asked too many times)
        if state.should_skip_field():
            logger.info(f"⏭️  Skipping '{next_field}' after {ask_count} attempts - marking as 'to_be_discussed'")
            
            # Mark field as "to_be_discussed" so we can move on
            state.set_field(next_field, "to_be_discussed_with_team")
            state.reset_field_tracking()
            
            # Try next field
            return self.get_next_field_question(state, prefix)
        
        # Generate question for this field
        next_question = self.question_generator.get_field_question(next_field, state.customer_type)
        
        # Add prefix if provided
        if prefix:
            response = f"{prefix} {next_question}"
        else:
            response = next_question
        
        return {"response": response, "should_end": False}
    
    # Delegation now handled by FlowController
    
    async def process_message(
        self,
        user_message: str,
        conversation_history: List[Dict],
        conversation_data: Dict,
        country_code: str = "US"
    ) -> Dict:
        """
        Process user message and generate response
        
        Args:
            user_message: User's message text
            conversation_history: List of previous messages
            conversation_data: Extracted data (will be converted to ConversationState)
            country_code: Default country code
        
        Returns:
            Dict with response text and optional end flag
        """
        # Convert conversation_data dict to ConversationState
        state = ConversationState.from_dict(conversation_data)
        if not state.country_code:
            state.country_code = country_code
        # Initialize in-memory debug trace and helper
        debug_trace = conversation_data.get("debug_trace", [])
        def _trace(step: str, data: Dict):
            try:
                from datetime import datetime as _dt
                debug_trace.append({"ts": _dt.utcnow().isoformat(), "step": step, "data": data})
            except Exception:
                pass
        _trace("start", {"stage": state.intent_stage, "customer_type": state.customer_type, "is_qualified": state.is_qualified})
        
        # Check for goodbye FIRST
        message_lower = user_message.lower()
        if any(word in message_lower for word in ["bye", "goodbye", "see you", "talk later"]):
            return {
                "response": "Goodbye! Have a nice day!",
                "should_end": True
            }
        
        # BUG-013 FIX: Check for post-qualification closure BEFORE running detection
        # This prevents the bot from resetting to "unclear" when user says "ok" after qualification
        logger.info(f"🔍 DEBUG: state.is_qualified={state.is_qualified}, state.customer_type={state.customer_type}, state.intent_stage={state.intent_stage}")
        if state.is_qualified:
            post_qual_exit = await self.flow_controller.handle_post_qualification_flow(user_message, conversation_history, state, conversation_data)
            if post_qual_exit:
                logger.info(f"🛑 Post-qualification exit triggered: should_end={post_qual_exit.get('should_end')}")
                return post_qual_exit
        
        # ===== PARALLEL CONTEXT DETECTION (OPTIMIZED) =====
        # Run parallel detection based on conversation state
        import asyncio
        from app.services.outbound.detection.type_detector import type_detector
        from app.services.outbound.detection.flow_detector import flow_detector
        
        # Determine current field for context
        current_field = None
        if state.customer_type and state.can_start_qualification() and not state.is_qualified:
            missing_fields = state.get_missing_fields(state.customer_type)
            current_field = missing_fields[0] if missing_fields else None
        
        # Conditional parallel detection based on state
        if state.customer_type and state.customer_type in ["new_cafe", "existing_cafe"]:
            # After intent confirmed: Check if in qualification to run extraction in parallel too
            if state.can_start_qualification() and not state.is_qualified:
                # In qualification: flow + extraction (2 parallel calls)
                logger.info(f"🎯 Running PARALLEL detection: flow + extraction (2 calls)...")

                # Create all tasks immediately for true parallel execution
                flow_task = asyncio.create_task(flow_detector.detect_flow_state(user_message, conversation_history, current_field))
                
                await asyncio.sleep(0.1)
                extraction_task = asyncio.create_task(self.extraction_service.extract_fields_with_llm(
                    user_message,
                    state.customer_type,
                    conversation_history,
                    state
                ))

                # Wait for both to complete
                flow_state_result, early_extracted_fields = await asyncio.gather(
                    flow_task, extraction_task
                )
                customer_type_result = None

                logger.info(f"✅ Parallel detection complete (flow + extraction)")
            else:
                # After intent but not in qualification: flow state only
                logger.info(f"🎯 Running detection: flow state...")

                flow_state_result = await flow_detector.detect_flow_state(user_message, conversation_history, current_field)
                customer_type_result = None
                early_extracted_fields = None

                logger.info(f"✅ Detection complete (flow)")
        else:
            # Before intent confirmed: customer type + extraction (2 parallel calls)
            logger.info(f"🎯 Running PARALLEL detection: customer type + extraction (2 calls)...")

            # Create both tasks for parallel execution
            type_task = asyncio.create_task(type_detector.detect_with_llm(user_message, conversation_history))
            
            await asyncio.sleep(0.1)
            extraction_task = asyncio.create_task(self.extraction_service.extract_fields_with_llm(
                user_message,
                "unclear",  # Use "unclear" to restrict extraction to contact info only
                conversation_history,
                state
            ))

            # Wait for both to complete
            customer_type_result, early_extracted_fields = await asyncio.gather(
                type_task, extraction_task
            )
            flow_state_result = {"state": "continuing", "reasoning": "Intent not yet confirmed"}

            logger.info(f"✅ Parallel detection complete (type + extraction)")

        # BUG-012 FIX: Check for human connection request
        human_connection = await self.flow_controller.handle_human_connection_request(user_message, state, conversation_data)
        _trace("human_connection_check", {"triggered": bool(human_connection)})
        if human_connection:
            return human_connection
        
        # Step 2: early flow intents (using results from type detection if available)
        early = await self.flow_controller.handle_early_flow(user_message, conversation_history, state, conversation_data, customer_type_result)
        _trace("early_flow", {"handled": bool(early)})
        if early:
            return early
        
        # ===== FLOW STATE HANDLING =====
        # Use flow state from unified detection
        flow_state = flow_state_result.get("flow_state") if flow_state_result else None
        
        if flow_state_result and flow_state:
            
            # Handle different flow states
            if flow_state == "wants_to_exit":
                logger.info(f"🚪 User wants to exit: {flow_state_result['reasoning']}")
                state.reset_to_exploration()
                conversation_data.update(state.to_dict())
                return {
                    "response": "No problem! Feel free to ask me anything about Abbotsford Road Coffee.",
                    "should_end": False
                }
            
            elif flow_state == "refuses_contact_info":
                logger.info(f"🙅 User refuses contact info: {flow_state_result['reasoning']}")
                
                # Detect what contact info was being asked for based on context
                # Check if phone or email is in missing fields
                missing_fields = state.get_missing_fields(state.customer_type)
                needs_phone = "phone" in missing_fields
                needs_email = "email" in missing_fields
                
                # If refusing phone (either current_field is phone OR phone is needed and not email)
                if (current_field == "phone") or (needs_phone and not state.phone and not state.email):
                    if not state.email and needs_email:
                        # Mark phone as declined and offer email alternative
                        logger.info(f"✅ User refused phone - marking as user_declined and offering email")
                        state.set_field("phone", "user_declined")
                        state.reset_field_tracking()
                        conversation_data.update(state.to_dict())
                        return {
                            "response": "I understand! Would you prefer to share your email instead so our team can reach out?",
                            "should_end": False
                        }
                    elif state.email:
                        # Already have email, mark phone as declined and continue
                        logger.info(f"✅ User refused phone but has email - marking phone as user_declined and continuing")
                        state.set_field("phone", "user_declined")
                        state.reset_field_tracking()
                        conversation_data.update(state.to_dict())
                        if state.is_complete(state.customer_type):
                            return {
                                "response": "No worries! We'll use your email to connect. Is there anything else you'd like to know?",
                                "should_end": False
                            }
                        else:
                            remaining_fields = state.get_missing_fields(state.customer_type)
                            if remaining_fields:
                                next_question = self.question_generator.get_field_question(remaining_fields[0], state.customer_type)
                                return {
                                    "response": f"No worries! {next_question}",
                                    "should_end": False
                                }
                
                # If refusing email (either current_field is email OR email is needed)
                elif (current_field == "email") or (needs_email and not state.email and not state.phone):
                    if not state.phone and needs_phone:
                        # Mark email as declined and offer phone alternative
                        logger.info(f"✅ User refused email - marking as user_declined and offering phone")
                        state.set_field("email", "user_declined")
                        state.reset_field_tracking()
                        conversation_data.update(state.to_dict())
                        return {
                            "response": "No problem! Would you prefer to share your phone number instead?",
                            "should_end": False
                        }
                    elif state.phone:
                        # Already have phone, mark email as declined and continue
                        logger.info(f"✅ User refused email but has phone - marking email as user_declined and continuing")
                        state.set_field("email", "user_declined")
                        state.reset_field_tracking()
                        conversation_data.update(state.to_dict())
                        if state.is_complete(state.customer_type):
                            return {
                                "response": "No problem! We'll use your phone to connect. Is there anything else you'd like to know?",
                                "should_end": False
                            }
                        else:
                            remaining_fields = state.get_missing_fields(state.customer_type)
                            if remaining_fields:
                                next_question = self.question_generator.get_field_question(remaining_fields[0], state.customer_type)
                                return {
                                    "response": f"No problem! {next_question}",
                                    "should_end": False
                                }
                
                # If refusing both or no alternatives, offer exploration
                else:
                    state.reset_to_exploration()
                    conversation_data.update(state.to_dict())
                    return {
                        "response": "No worries! Would you like to just explore and learn more about our coffee for now?",
                        "should_end": False
                    }
            
            elif flow_state == "asking_question":
                logger.info(f"❓ User asking question during qualification: {flow_state_result['reasoning']}")
                
                # Answer their question using RAG
                is_question = self.rag_handler.is_rag_question(user_message)
                if is_question:
                    result = await self.rag_handler.answer_rag_question_unlimited(user_message)
                    # Add gentle return to qualification
                    if missing_fields:
                        next_question = self.question_generator.get_field_question(missing_fields[0], state.customer_type)
                        result["response"] = f"{result['response']} Now, {next_question}"
                    conversation_data.update(state.to_dict())
                    return result
            
            # If flow_state is "continuing", proceed with normal flow below
        
        # ===== CASUAL BROWSER DETECTION =====
        casual = await self.flow_controller.handle_casual_browser(user_message, conversation_history, state, conversation_data)
        if casual:
            return casual
        
        # ===== MULTI-STAGE INTENT DETECTION =====
        # Use customer type from unified detection
        prev_stage = state.intent_stage
        await self.flow_controller.handle_intent_detection(user_message, conversation_history, state, pre_detected_result=customer_type_result)
        _trace("intent_detection", {"stage_before": prev_stage, "stage_after": state.intent_stage, "customer_type": state.customer_type})
        
        # Get last bot message for context
        last_bot_message = ""
        if conversation_history:
            for msg in reversed(conversation_history):
                if 'bot' in msg:
                    last_bot_message = msg['bot']
                    break
        
        # ===== HANDLE EMAIL TYPO CONFIRMATION =====
        email_fix = await self.flow_controller.handle_email_typo_confirmation(user_message, conversation_history, state, conversation_data)
        _trace("email_typo_confirmation", {"handled": bool(email_fix)})
        if email_fix:
            return email_fix
        
        # Step 3: RAG question handling during qualification
        rag_qa = await self.flow_controller.handle_rag_during_qualification(user_message, conversation_history, state, conversation_data)
        _trace("rag_during_qualification", {"handled": bool(rag_qa)})
        if rag_qa:
            return rag_qa
        
        # HUMAN CONNECTION: Handled by the state machine in handle_human_connection_request
        
        # If qualified OR still exploring/interest stage, handle all messages naturally
        if (state.is_qualified or 
            state.intent_stage in ["exploring", "interest_detected"]):
            
            is_question = self.rag_handler.is_rag_question(user_message)
            if is_question:
                if state.is_qualified:
                    logger.info("User is qualified - answering question without redirect")
                else:
                    logger.info(f"User in {state.intent_stage} stage - answering question naturally")
                result = await self.rag_handler.answer_rag_question_unlimited(user_message, state)
                conversation_data.update(state.to_dict())
                return result
        
        # ===== COMMITMENT SIGNAL DETECTION =====
        # If in interest_detected stage and user provides timeline/commitment signals, upgrade to intent_confirmed
        if state.intent_stage == "interest_detected" and state.customer_type:
            commitment_signals = {
                "new_cafe": ["timeline", "equipment", "volume"],
                "existing_cafe": ["current_pain_points", "cafe_count"]
            }
            
            # Check if user has provided any commitment signal fields
            signals = commitment_signals.get(state.customer_type, [])
            has_commitment = any(getattr(state, field, None) for field in signals)
            
            if has_commitment:
                logger.info(f"🎯 Commitment signal detected - upgrading from interest_detected to intent_confirmed")
                state.set_intent_stage("intent_confirmed")
                _trace("commitment_upgrade", {"upgraded": True})
            else:
                _trace("commitment_upgrade", {"upgraded": False})
        
        # ===== FIELD EXTRACTION + VALIDATION (delegated) =====
        extraction_outcome = await self.flow_controller.handle_extraction_and_validation(
            user_message, conversation_history, state, conversation_data, early_extracted_fields
        )
        _trace("extraction_validation", {"early_response": bool(extraction_outcome)})
        if extraction_outcome:
            return extraction_outcome
        
        # Upgrade stage if commitment signals appear
        self.flow_controller.handle_commitment_upgrade(state)

        # ===== CHECK QUALIFICATION COMPLETE =====
        qualification = self.flow_controller.evaluate_qualification_completion(state)
        _trace("qualification_check", {"qualified": bool(qualification)})
        if qualification:
            conversation_data.update(state.to_dict())
            return qualification
        
        # ===== GENERATE RESPONSE =====
        # Check if this is a RAG question before customer type is detected
        use_rag_instruction = not state.customer_type
        
        # Check if contact info was just provided in this message (for acknowledgment)
        just_provided_contact = []
        message_lower = user_message.lower()
        if state.name and any(word in message_lower for word in ["i'm", "im", "my name", "name is"]):
            just_provided_contact.append(f"name ({state.name})")
        if state.email and ("@" in user_message or "email" in message_lower):
            just_provided_contact.append(f"email ({state.email})")
        if state.phone and any(char.isdigit() for char in user_message):
            just_provided_contact.append(f"phone ({state.phone})")
        
        # Generate response using response builder
        response_text = await self.response_builder.generate_response(
            user_message=user_message,
            conversation_history=conversation_history,
            state=state,
            use_rag_instruction=use_rag_instruction,
            just_provided_contact=just_provided_contact
        )
        
        # Update conversation_data with final state
        conversation_data.update(state.to_dict())
        conversation_data["debug_trace"] = debug_trace[-50:]
        
        return {
            "response": response_text,
            "should_end": False
        }


# Singleton instance
outbound_bot = OutboundBot()
