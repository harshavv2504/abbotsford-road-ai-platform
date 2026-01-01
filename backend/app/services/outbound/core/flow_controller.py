from typing import Dict, List, Optional

"""
Flow Controller (core)

What it does:
- Encapsulates step-by-step decision handlers used by the orchestrator: early flow intents,
  casual browsing, intent detection, email-typo flow, RAG during qualification, commitment upgrade, and
  final qualification completion.

If you change it:
- You change per-step behaviors without touching the high-level order in `OutboundBot`. Add new steps here
  and call them from `OutboundBot` to keep orchestration readable and testable.
"""

from app.services.outbound.state_manager import ConversationState
from app.utils.logger import logger


class FlowController:
	"""Encapsulates stepwise flow handling for outbound conversations.

	Use this to evolve individual steps safely. Keep methods small and side effects explicit
	by updating `ConversationState` and returning early responses when needed.
	"""

	def __init__(self, *, customer_type_detector, rag_handler, question_generator, extraction_service=None, validation_service=None, bot_functions=None, extraction_pipeline=None):
		self.customer_type_detector = customer_type_detector
		self.rag_handler = rag_handler
		self.question_generator = question_generator
		self.extraction_service = extraction_service
		self.validation_service = validation_service
		self.bot_functions = bot_functions
		self.extraction_pipeline = extraction_pipeline

	async def handle_human_connection_request(self, user_message: str, state: ConversationState, conversation_data: Dict) -> Optional[Dict]:
		"""BUG-012 FIX: Handle requests to connect with a real person - Multi-stage flow"""
		
		if not self.extraction_service:
			return None
		
		user_msg_lower = user_message.lower().strip()
		
		# STAGE 1: Initial human connection request detected
		if self.extraction_service.detect_human_connection_request(user_message):
			logger.info("🤝 BUG-012 FIX: User requested human connection")
			
			# Check if we already have contact info
			has_contact = bool(state.phone or state.email)
			
			if has_contact:
				# We have contact, confirm connection
				contact_method = state.phone if state.phone else state.email
				
				# Format phone for display if it's a phone number
				if state.phone:
					from app.utils.validators import format_phone_for_display
					contact_display = format_phone_for_display(state.phone)
				else:
					contact_display = contact_method
				
				# Mark as qualified and connection confirmed
				if not state.is_qualified and state.name:
					state.is_qualified = True
					state.set_intent_stage("qualified")
				
				state.human_connection_confirmed = True
				state.human_connection_flow_stage = "confirmed"
				
				response = f"Great! Our team will reach out to you at {contact_display}. Is that still the best way to reach you?"
				
				conversation_data.update(state.to_dict())
				return {
					"response": response,
					"should_end": False
				}
			else:
				# Need contact info first - ask for method preference
				state.human_connection_flow_stage = "awaiting_method"
				response = "I'd be happy to connect you with our team! What's the best way to reach you—phone or email?"
				conversation_data.update(state.to_dict())
				return {
					"response": response,
					"should_end": False
				}
		
		# STAGE 2: User is choosing contact method (phone or email)
		if state.human_connection_flow_stage == "awaiting_method":
			logger.info(f"🤝 BUG-012 FIX: Processing contact method choice: '{user_message}'")
			# Detector: If user refuses email during method selection, pivot to phone (no hardcoding)
			try:
				from app.services.outbound.extraction.validators import ExtractionValidators
				extractor_validators = ExtractionValidators()
			except Exception:
				extractor_validators = None
			
			user_msg_lower = user_message.lower()
			if extractor_validators and ("email" in user_msg_lower or "mail" in user_msg_lower):
				if extractor_validators.detect_refusal(user_message):
					state.track_contact_refusal("email")
					state.human_connection_flow_stage = "awaiting_phone"
					state.email_preference_indicated = False
					response = "Got it! What's your phone number?"
					conversation_data.update(state.to_dict())
					return {
						"response": response,
						"should_end": False
					}
			
			# BUG-297 FIX: Check if user wants both phone and email
			if any(word in user_msg_lower for word in ["both", "either", "any", "all"]):
				state.human_connection_flow_stage = "awaiting_phone"
				state.phone_preference_indicated = True
				state.email_preference_indicated = True
				response = "Perfect! Let's start with your phone number."
				conversation_data.update(state.to_dict())
				return {
					"response": response,
					"should_end": False
				}
			
			# Check if user chose phone
			elif any(word in user_msg_lower for word in ["phone", "call", "number", "mobile", "cell"]):
				state.human_connection_flow_stage = "awaiting_phone"
				state.phone_preference_indicated = True
				response = "Got it! What's your phone number?"
				conversation_data.update(state.to_dict())
				return {
					"response": response,
					"should_end": False
				}
			
			# Check if user chose email
			elif any(word in user_msg_lower for word in ["email", "mail", "e-mail"]):
				state.human_connection_flow_stage = "awaiting_email"
				state.email_preference_indicated = True
				response = "Perfect! What's your email address?"
				conversation_data.update(state.to_dict())
				return {
					"response": response,
					"should_end": False
				}
			
			# User didn't clearly specify - ask again
			else:
				response = "I'd like to make sure I connect you with the right person. Would you prefer to be contacted by phone or email?"
				conversation_data.update(state.to_dict())
				return {
					"response": response,
					"should_end": False
				}
		
		# STAGE 3: User is providing phone number
		if state.human_connection_flow_stage == "awaiting_phone":
			logger.info(f"🤝 BUG-012 FIX: Processing phone number: '{user_message}'")
			
			# Try to extract and validate phone
			from app.services.outbound.extraction_service import extraction_service
			from app.services.outbound.validation_service import validation_service
			
			extraction_result = await extraction_service.extract_fields_with_llm(
				user_message=user_message,
				customer_type=state.customer_type or "new_cafe",
				conversation_history=[],
				state=state
			)
			
			if extraction_result.get("phone"):
				raw_phone = extraction_result["phone"]
				
				# Validate and format the phone number
				validation_result = validation_service.validate_and_format_phone(raw_phone)
				
				if validation_result["success"]:
					phone = validation_result["formatted_phone"]
					state.phone = phone
					state.country_code = validation_result.get("country_code")
					state.human_connection_flow_stage = "awaiting_phone_confirmation"
					
					# Format phone for display: +1 777 777 7777
					from app.utils.validators import format_phone_for_display
					phone_display = format_phone_for_display(phone)
					
					response = f"Is {phone_display} the best number to reach you? If not, please provide your number with country code."
					conversation_data.update(state.to_dict())
					return {
						"response": response,
						"should_end": False
					}
				else:
					# Validation failed - ask again with error message
					response = f"{validation_result['error']} Please share your phone number again (e.g., 555-123-4567 or +1 555-123-4567)."
					conversation_data.update(state.to_dict())
					return {
						"response": response,
						"should_end": False
					}
			
			# Couldn't extract valid phone - ask again
			response = "I didn't catch that number. Could you share it again? (US numbers like 555-123-4567, or include +1 if you prefer)"
			conversation_data.update(state.to_dict())
			return {
				"response": response,
				"should_end": False
			}
		
		# STAGE 3.5: User is confirming phone number
		if state.human_connection_flow_stage == "awaiting_phone_confirmation":
			logger.info(f"🤝 BUG-012 FIX: User confirming phone: '{user_message}'")
			
			# Check if user confirms (yes/correct/that's right) or denies (no/wrong)
			user_lower = user_message.lower().strip()
			is_confirmation = any(word in user_lower for word in ["yes", "yeah", "yep", "correct", "right", "sure", "ok", "okay", "yup"])
			is_denial = any(word in user_lower for word in ["no", "nope", "wrong", "incorrect", "not"])
			
			if is_denial:
				# User says phone is wrong - ask for correct phone
				state.phone = None
				state.human_connection_flow_stage = "awaiting_phone"
				response = "No problem! What's the correct phone number?"
				conversation_data.update(state.to_dict())
				return {
					"response": response,
					"should_end": False
				}
			elif is_confirmation:
				# BUG-297 FIX: Check if user indicated they want both phone and email
				if state.email_preference_indicated and not state.email:
					# User said "both" earlier - ask for email as primary contact, not backup
					state.human_connection_flow_stage = "awaiting_email"
					response = "Great! Now, what's your email address?"
					conversation_data.update(state.to_dict())
					return {
						"response": response,
						"should_end": False
					}
				else:
					# User only chose phone - ask for email backup
					state.human_connection_flow_stage = "awaiting_email_backup"
					response = "Perfect! Just to be safe, what's your email in case we can't reach you by phone?"
					conversation_data.update(state.to_dict())
					return {
						"response": response,
						"should_end": False
					}
			else:
				# Unclear response - ask again
				from app.utils.validators import format_phone_for_display
				phone_display = format_phone_for_display(state.phone)
				
				response = f"Just to confirm, is {phone_display} the best number to reach you? (Yes or No)"
				conversation_data.update(state.to_dict())
				return {
					"response": response,
					"should_end": False
				}
		
		# STAGE 4: User is providing email backup after phone confirmation
		if state.human_connection_flow_stage == "awaiting_email_backup":
			logger.info(f"🤝 BUG-012 FIX: Processing email backup: '{user_message}'")
			
			# Detector: If user refuses providing email backup, accept phone-only and confirm connection
			try:
				from app.services.outbound.extraction.validators import ExtractionValidators
				extractor_validators = ExtractionValidators()
			except Exception:
				extractor_validators = None
			
			if extractor_validators and extractor_validators.detect_refusal(user_message):
				state.track_contact_refusal("email")
				state.email = "user_declined"
				state.human_connection_confirmed = True
				state.human_connection_flow_stage = "confirmed"
				# Optionally mark qualified if we have the name
				if not state.is_qualified and state.name:
					state.is_qualified = True
					state.set_intent_stage("qualified")
				
				# Format phone for display
				from app.utils.validators import format_phone_for_display
				phone_display = format_phone_for_display(state.phone) if state.phone else "your phone"
				
				conversation_data.update(state.to_dict())
				return {
					"response": f"No problem! We'll use {phone_display} to connect. Is there anything else you'd like to know?",
					"should_end": False
				}
			
			# Try to extract and validate email
			from app.services.outbound.extraction_service import extraction_service
			from app.services.outbound.validation_service import validation_service
			
			extraction_result = await extraction_service.extract_fields_with_llm(
				user_message=user_message,
				customer_type=state.customer_type or "new_cafe",
				conversation_history=[],
				state=state
			)
			
			if extraction_result.get("email"):
				raw_email = extraction_result["email"]
				
				# Validate the email address
				validation_result = validation_service.validate_and_format_email(raw_email)
				
				if validation_result["success"]:
					email = validation_result["normalized_email"]
					state.email = email
					state.human_connection_confirmed = True
					state.human_connection_flow_stage = "confirmed"
					
					# Mark as qualified if we have name
					if not state.is_qualified and state.name:
						state.is_qualified = True
						state.set_intent_stage("qualified")
					
					# Format phone for display
					from app.utils.validators import format_phone_for_display
					phone_display = format_phone_for_display(state.phone)
					
					response = f"Awesome! Our team will reach out to you at {phone_display} or {email}. We'll be in touch soon!"
					conversation_data.update(state.to_dict())
					return {
						"response": response,
						"should_end": False
					}
				else:
					# Validation failed - ask again with error message
					response = f"{validation_result['error']} Please share a valid email address."
					conversation_data.update(state.to_dict())
					return {
						"response": response,
						"should_end": False
					}
			
			# Couldn't extract valid email - ask again
			response = "I didn't catch that email address. Could you share it again? (e.g., name@example.com)"
			conversation_data.update(state.to_dict())
			return {
				"response": response,
				"should_end": False
			}
		
		# STAGE 5: User is providing email address (when they chose email as primary contact)
		if state.human_connection_flow_stage == "awaiting_email":
			logger.info(f"🤝 BUG-012 FIX: Processing email address: '{user_message}'")

			# Detector: If user refuses email here, set flag and pivot to phone (no hardcoding)
			try:
				from app.services.outbound.extraction.validators import ExtractionValidators
				extractor_validators = ExtractionValidators()
			except Exception:
				extractor_validators = None
			
			if extractor_validators and extractor_validators.detect_refusal(user_message):
				state.track_contact_refusal("email")
				# Mark email as declined for downstream logic
				state.email = "user_declined"
				state.human_connection_flow_stage = "awaiting_phone"
				conversation_data.update(state.to_dict())
				return {
					"response": "No problem! Would you prefer to share your phone number instead?",
					"should_end": False
				}
			
			# Try to extract and validate email
			from app.services.outbound.extraction_service import extraction_service
			from app.services.outbound.validation_service import validation_service
			
			extraction_result = await extraction_service.extract_fields_with_llm(
				user_message=user_message,
				customer_type=state.customer_type or "new_cafe",
				conversation_history=[],
				state=state
			)
			
			if extraction_result.get("email"):
				raw_email = extraction_result["email"]
				
				# Validate the email address
				validation_result = validation_service.validate_and_format_email(raw_email)
				
				if validation_result["success"]:
					email = validation_result["normalized_email"]
					state.email = email
					state.human_connection_confirmed = True
					state.human_connection_flow_stage = "confirmed"
					
					# Mark as qualified if we have name
					if not state.is_qualified and state.name:
						state.is_qualified = True
						state.set_intent_stage("qualified")
					
					# BUG-297 FIX: If user provided both phone and email, acknowledge both
					if state.phone and state.phone_preference_indicated:
						# Format phone for display
						from app.utils.validators import format_phone_for_display
						phone_display = format_phone_for_display(state.phone)
						response = f"Perfect! Our team will reach out to you at {email} or {phone_display}. We'll be in touch soon!"
					else:
						response = f"Great! Our team will reach out to you at {email}. We'll be in touch soon!"
					
					conversation_data.update(state.to_dict())
					return {
						"response": response,
						"should_end": False
					}
				else:
					# Validation failed - ask again with error message
					response = f"{validation_result['error']} Please share a valid email address."
					conversation_data.update(state.to_dict())
					return {
						"response": response,
						"should_end": False
					}
			
			# Couldn't extract valid email - ask again
			response = "I didn't catch that email address. Could you share it again? (e.g., name@example.com)"
			conversation_data.update(state.to_dict())
			return {
				"response": response,
				"should_end": False
			}
		
		# STAGE 5: User is confirming/acknowledging after connection is confirmed
		if state.human_connection_flow_stage == "confirmed" and state.human_connection_confirmed:
			logger.info(f"🤝 BUG-012 FIX: User message after confirmation: '{user_message}'")
			
			# Check if user is just confirming (yes, ok, correct, etc.)
			confirmation_words = ["yes", "yeah", "yep", "yup", "correct", "right", "that's right", "ok", "okay", "sure", "perfect"]
			if any(word in user_msg_lower for word in confirmation_words):
				# User confirmed - end the human connection flow gracefully
				response = "Perfect! Our team will be in touch soon. Looking forward to connecting with you!"
				conversation_data.update(state.to_dict())
				return {
					"response": response,
					"should_end": False
				}
		
		return None


	async def handle_extraction_and_validation(self, user_message: str, conversation_history: List[Dict], state: ConversationState, conversation_data: Dict, early_extracted_fields: Dict = None) -> Optional[Dict]:
		if not self.extraction_pipeline:
			return None
		return await self.extraction_pipeline.process(user_message, conversation_history, state, conversation_data, early_extracted_fields)

	async def handle_casual_browser(self, user_message: str, conversation_history: List[Dict], state: ConversationState, conversation_data: Dict) -> Optional[Dict]:
		message_lower = user_message.lower()
		casual_phrases = [
			"just browsing", "just looking", "just curious", "just exploring",
			"just checking", "just want to know", "just wondering",
			"no commitment", "not ready", "not sure yet", "maybe later"
		]
		if not state.customer_type and any(phrase in message_lower for phrase in casual_phrases):
			logger.info("User is casual browser - staying in exploration mode")
			is_question = self.rag_handler.is_rag_question(user_message)
			if is_question:
				result = await self.rag_handler.answer_rag_question_unlimited(user_message, state)
				result["response"] = f"Cool! No pressure. {result['response']}"
				conversation_data.update(state.to_dict())
				return result
			conversation_data.update(state.to_dict())
			return {
				"response": "No worries! Browse away. What would you like to know about our coffee?",
				"should_end": False
			}
		return None

	async def handle_intent_detection(self, user_message: str, conversation_history: List[Dict], state: ConversationState, pre_detected_result=None) -> None:
		if state.customer_type:
			return
		
		# Use pre-detected result from parallel execution if available
		if pre_detected_result:
			intent_result = pre_detected_result
		else:
			intent_result = await self.customer_type_detector.detect_with_llm(user_message, conversation_history)
		if intent_result and intent_result["customer_type"] != "unclear":
			if intent_result["confidence"] == "high":
				state.customer_type = intent_result["customer_type"]
				state.set_intent_stage("intent_confirmed")
				logger.info(f"✅ Intent confirmed: {state.customer_type} (HIGH confidence)")
				logger.info(f"Reasoning: {intent_result['reasoning']}")
				
				# BUG-011 FIX: Ensure we transition to qualifying to start collecting info
				if state.can_start_qualification():
					logger.info("✅ BUG-011 FIX: Transitioning to qualifying stage to collect lead info")
				if intent_result.get("contact_info"):
					contact_info = intent_result["contact_info"]
					if contact_info.get("name") and not state.name:
						state.name = contact_info["name"]
						logger.info(f"Extracted from intent detection - name: {state.name}")
					if contact_info.get("phone") and not state.phone:
						state.phone = contact_info["phone"]
						logger.info(f"Extracted from intent detection - phone: {state.phone}")
					if contact_info.get("email") and not state.email:
						state.email = contact_info["email"]
						logger.info(f"Extracted from intent detection - email: {state.email}")
				# Extract from current and recent messages now that we know the type
				if self.extraction_service:
					# First, re-extract from the CURRENT message with the confirmed customer type
					# This captures fields that were filtered out during parallel detection
					current_extracted = await self.extraction_service.extract_fields_with_llm(
						user_message,
						state.customer_type,
						conversation_history,
						state
					)
					for key, value in current_extracted.items():
						if value and not state.get_field(key):
							state.set_field(key, value)
							logger.info(f"Re-extracted from current message with confirmed type - {key}: {value}")
					
					# Then check previous messages if available
					if conversation_history:
						for msg in reversed(conversation_history[-3:]):
							if 'user' in msg:
								prev_extracted = await self.extraction_service.extract_fields_with_llm(
									msg['user'],
									state.customer_type,
									conversation_history,
									state
								)
								for key, value in prev_extracted.items():
									if value and not state.get_field(key):
										state.set_field(key, value)
										logger.info(f"Extracted from previous message - {key}: {value}")
								break
		elif intent_result and intent_result["confidence"] == "medium":
			state.customer_type = intent_result["customer_type"]
			state.set_intent_stage("interest_detected")
			logger.info(f"🔍 Interest detected: {state.customer_type} (MEDIUM confidence)")
			logger.info(f"Reasoning: {intent_result['reasoning']}")
			if intent_result.get("contact_info"):
				contact_info = intent_result["contact_info"]
				if contact_info.get("name") and not state.name:
					state.name = contact_info["name"]
					logger.info(f"Extracted from intent detection - name: {state.name}")
				if contact_info.get("phone") and not state.phone:
					state.phone = contact_info["phone"]
					logger.info(f"Extracted from intent detection - phone: {state.phone}")
				if contact_info.get("email") and not state.email:
					state.email = contact_info["email"]
					logger.info(f"Extracted from intent detection - email: {state.email}")
		else:
			logger.info("⏳ Customer type unclear - Stage: exploring")
			if intent_result and intent_result.get("contact_info"):
				contact_info = intent_result["contact_info"]
				if contact_info.get("name") and not state.name:
					state.name = contact_info["name"]
					logger.info(f"Extracted from intent detection - name: {state.name}")
				if contact_info.get("phone") and not state.phone:
					state.phone = contact_info["phone"]
					logger.info(f"Extracted from intent detection - phone: {state.phone}")
				if contact_info.get("email") and not state.email:
					state.email = contact_info["email"]
					logger.info(f"Extracted from intent detection - email: {state.email}")

	async def handle_email_typo_confirmation(self, user_message: str, conversation_history: List[Dict], state: ConversationState, conversation_data: Dict) -> Optional[Dict]:
		if state.email_typo_suggested and not state.email:
			message_lower = user_message.lower().strip()
			if message_lower in ["yes", "yeah", "yep", "correct", "right", "that's right", "yup", "y"]:
				if not self.validation_service:
					return None
				result = self.validation_service.validate_and_format_email(state.email_typo_suggested)
				if result["success"]:
					state.email = result["normalized_email"]
					state.email_typo_suggested = None
					logger.info(f"User confirmed typo correction: {state.email}")
					missing_fields = state.get_missing_fields(state.customer_type)
					if missing_fields:
						next_question = self.question_generator.get_field_question(missing_fields[0], state.customer_type)
						conversation_data.update(state.to_dict())
						return {"response": f"Perfect! {next_question}", "should_end": False}
					conversation_data.update(state.to_dict())
					return {"response": "Great! Let me get your details together.", "should_end": False}
			elif "@" in user_message:
				state.email_typo_suggested = None
			elif message_lower in ["no", "nope", "nah", "n"]:
				state.email_typo_suggested = None
				conversation_data.update(state.to_dict())
				return {
					"response": "No worries! What's the correct email?",
					"should_end": False
				}
		return None

	def handle_commitment_upgrade(self, state: ConversationState) -> None:
		if state.intent_stage == "interest_detected" and state.customer_type:
			commitment_signals = {
				"new_cafe": ["timeline", "equipment", "volume"],
				"existing_cafe": ["current_pain_points", "cafe_count"]
			}
			signals = commitment_signals.get(state.customer_type, [])
			has_commitment = any(getattr(state, field, None) for field in signals)
			if has_commitment:
				logger.info("🎯 Commitment signal detected - upgrading from interest_detected to intent_confirmed")
				state.set_intent_stage("intent_confirmed")

	def evaluate_qualification_completion(self, state: ConversationState) -> Optional[Dict]:
		if not (state.customer_type and state.can_start_qualification() and not state.is_qualified and state.is_complete(state.customer_type)):
			return None
		if not self.bot_functions:
			return None
		if state.customer_type == "new_cafe":
			result = self.bot_functions.qualify_new_cafe_customer(
				timeline=state.timeline or "",
				coffee_style=state.coffee_style or "",
				equipment=state.equipment or "",
				volume=state.volume or "",
				name=state.name or "",
				phone=state.phone or "",
				email=state.email or "",
				phone_needs_review=state.phone_needs_manual_review
			)
		else:
			result = self.bot_functions.qualify_existing_cafe_customer(
				current_pain_points=state.current_pain_points or "",
				cafe_count=state.cafe_count or "",
				support_needs=state.support_needs or "",
				current_coffee_style=state.current_coffee_style or "",
				coffee_preference=state.coffee_preference or "",
				name=state.name or "",
				phone=state.phone or "",
				email=state.email or "",
				phone_needs_review=state.phone_needs_manual_review
			)
		if result.get("success"):
			state.is_qualified = True
			state.set_intent_stage("qualified")
			name = result['data']['name']
			if state.customer_type == "new_cafe":
				timeline_map = {
					"within_4_weeks": "within 4 weeks",
					"1_3_months": "in 1-3 months",
					"3_6_months": "in 3-6 months",
					"6_12_months": "in 6-12 months",
					"over_1_year": "in over a year",
					"in_6_months": "in 6 months",
					"six_months": "in 6 months",
					"unclear": "soon"  # Fallback for unclear timelines
				}
				timeline = timeline_map.get(state.timeline, state.timeline or "soon")
				completion_msg = f"This is going to be amazing, {name}! Opening {timeline}—so exciting! Our team will reach out soon to help bring your café to life. In the meantime, any other questions?"
			else:
				completion_msg = f"Love it, {name}! Our team will reach out soon to help take your café to the next level. In the meantime, what else can I help you with?"
			return {"response": completion_msg, "should_end": False}
		validation_errors = result.get("validation_errors", {})
		if validation_errors:
			error_field = list(validation_errors.keys())[0]
			error_message = validation_errors[error_field]
			invalid_value = state.get_field(error_field) or ""
			state.set_field(error_field, None)
			from app.utils.validators import get_smart_validation_feedback
			friendly_message = get_smart_validation_feedback(error_field, invalid_value, error_message)
			return {"response": friendly_message, "should_end": False}
		return None

	async def handle_early_flow(self, user_message: str, conversation_history: List[Dict], state: ConversationState, conversation_data: Dict, pre_detected_result: Dict = None) -> Optional[Dict]:
		# BUG-228 FIX: Check if user wants details/information before providing name
		message_lower = user_message.lower()
		wants_details_first = any(phrase in message_lower for phrase in [
			"want to know more details", "would like to know more", "more details",
			"details first", "information first", "before providing",
			"before giving", "first i would like", "want details",
			"need more information", "tell me more first", "know more about"
		])
		
		# Check if bot just asked for name or if user is in early conversation
		last_bot_message = ""
		if conversation_history:
			for msg in reversed(conversation_history):
				if 'bot' in msg:
					last_bot_message = msg['bot']
					break
		
		bot_asked_for_name = any(phrase in last_bot_message.lower() for phrase in [
			"who am i chatting with", "what's your name", "what is your name",
			"who am i talking to", "what should i call you"
		])
		
		# Also check if this is early in conversation (within first 3 messages)
		is_early_conversation = len(conversation_history) <= 3
		
		if wants_details_first and (bot_asked_for_name or is_early_conversation):
			logger.info("🔍 BUG-228 FIX: User wants details before providing name - providing information")
			
			# Provide comprehensive information about services
			response = "We support cafés in three ways: helping new cafés with coffee selection, equipment, and training; supporting existing cafés with quality improvement and growth; and answering any coffee questions. We offer seven signature blends, commercial equipment, hands-on training, and ongoing support. What would you like to know more about?"
			
			conversation_data.update(state.to_dict())
			return {
				"response": response,
				"should_end": False
			}
		
		# Check for ordering requests in ALL stages (not just qualification)
		# This handles users who want to order samples before going through qualification
		# Use pre-detected results from type detection if available (no extra LLM call)
		if pre_detected_result:
			wants_order = pre_detected_result.get("wants_to_place_order", False)
			wants_talk = pre_detected_result.get("wants_to_talk_to_person", False)
		else:
			# No early intents during qualification (flow state detector doesn't check these anymore)
			wants_order = False
			wants_talk = False
		
		if wants_order:
			logger.info(f"🛒 User wants to place order (detected from type detection)")
			
			# Check if this is the first time user is requesting order
			is_first_request = not state.wants_to_place_order
			
			if is_first_request:
				state.wants_to_place_order = True
				state.order_details = user_message
			
			# Check if we have ACTUAL contact info (not just preference)
			has_actual_phone = bool(state.phone and state.phone.startswith('+'))
			has_actual_email = bool(state.email and '@' in state.email)
			
			# If we have actual contact info, confirm and let them know team will reach out
			if has_actual_phone or has_actual_email:
				contact = state.phone if has_actual_phone else state.email
				conversation_data.update(state.to_dict())
				return {
					"response": f"Awesome! I've noted your request. Our team will reach out to you at {contact} to process your order. They'll get back to you shortly!",
					"should_end": False
				}
			
			# Only ask for contact info on the FIRST request
			if is_first_request:
				conversation_data.update(state.to_dict())
				return {
					"response": "I'd love to help with that! Our team handles orders directly. What's the best way to reach you—phone or email?",
					"should_end": False
				}
			
			# If we already asked and the user is now choosing a method, mirror human-connection prompts
			user_msg_lower = user_message.lower()
			if any(word in user_msg_lower for word in ["phone", "call", "number", "mobile", "cell"]):
				# Align the phone prompt with talk-to-person flow and mark preference
				state.phone_preference_indicated = True
				conversation_data.update(state.to_dict())
				return {
					"response": "Got it! What's your phone number?",
					"should_end": False
				}
			elif any(word in user_msg_lower for word in ["email", "mail", "e-mail"]):
				state.email_preference_indicated = True
				conversation_data.update(state.to_dict())
				return {
					"response": "Perfect! What's your email address?",
					"should_end": False
				}
			
			# If we already asked and they're providing contact, let extraction pipeline handle it
			return None
		
		# Only check other early flow intents during qualification (not exploration)
		if not (state.customer_type and state.can_start_qualification() and not state.is_qualified):
			return None
		
		# NOTE: "wants_to_talk_to_person" is now handled by handle_human_connection_request()
		# which uses a proper state machine (human_connection_flow_stage) to track the multi-step flow.
		# We removed the duplicate logic from here to avoid conflicts.
		
		return None

	async def handle_rag_during_qualification(self, user_message: str, conversation_history: List[Dict], state: ConversationState, conversation_data: Dict) -> Optional[Dict]:
		if not (state.customer_type and state.can_start_qualification() and not state.is_qualified):
			return None
		last_bot_message = ""
		if conversation_history:
			for msg in reversed(conversation_history):
				if 'bot' in msg:
					last_bot_message = msg['bot']
					break
		is_question_rules = self.rag_handler.is_rag_question(user_message)
		is_answering = self.rag_handler.is_answering_current_field(user_message, last_bot_message, state.current_field_being_asked)
		is_question = is_question_rules
		word_count = len(user_message.split())
		is_edge_case = last_bot_message and ((is_question_rules and word_count > 10) or (not is_question_rules and not is_answering and word_count > 5))
		if is_edge_case:
			llm_result = await self.rag_handler.detect_question_intent_with_llm(user_message, last_bot_message)
			if llm_result and llm_result.get("confidence") in ["high", "medium"]:
				is_question = bool(llm_result.get("is_question"))
		if is_question and not is_answering:
			missing_fields = state.get_missing_fields(state.customer_type)
			next_field_question = self.question_generator.get_field_question(missing_fields[0], state.customer_type) if missing_fields else ""
			result = await self.rag_handler.handle_rag_question(user_message, state, next_field_question)
			conversation_data.update(state.to_dict())
			return result
		return None

	async def handle_post_qualification_flow(self, user_message: str, conversation_history: List[Dict], state: ConversationState, conversation_data: Dict) -> Optional[Dict]:
		"""BUG-013 FIX: Handle post-qualification conversation flow (prevent loops)"""
		# Allow exit if qualified OR if we are in advanced stages (qualifying/intent_confirmed) and user wants to leave
		if not state.is_qualified and state.intent_stage not in ["qualifying", "intent_confirmed"]:
			return None
			
		# Check for negative/exit responses (no, nothing else, that's it)
		user_lower = user_message.lower().strip()
		exit_phrases = ["no", "nope", "nah", "nothing", "none", "that's it", "that's all", "im good", "i'm good", "all good"]
		
		# NEW: Check for simple acknowledgments after qualification (ok, thanks, great, etc.)
		acknowledgment_phrases = ["ok", "okay", "k", "thanks", "thank you", "great", "perfect", "sounds good", "got it", "alright", "cool"]
		
		# Check if this is a simple acknowledgment (short message with acknowledgment phrase)
		is_acknowledgment = len(user_lower.split()) <= 3 and any(phrase == user_lower or user_lower.startswith(phrase + " ") or user_lower.endswith(" " + phrase) for phrase in acknowledgment_phrases)
		
		# If message is short and contains exit phrase OR is a simple acknowledgment
		if len(user_lower.split()) < 10 and (any(phrase in user_lower for phrase in exit_phrases) or is_acknowledgment):
			logger.info(f"🛑 BUG-013 FIX: User indicated conversation closure (qualified={state.is_qualified}): '{user_message}'")
			
			# Build closing message
			name_part = f", {state.name}" if state.name else ""
			from app.utils.validators import format_phone_for_display
			contact_part = f" at {format_phone_for_display(state.phone)}" if state.phone else (f" at {state.email}" if state.email else "")
			
			# Use different response for acknowledgments vs explicit "no"
			if is_acknowledgment:
				response = f"Perfect! Our team will be in touch soon{contact_part}. Looking forward to connecting with you!"
			else:
				response = f"No worries{name_part}! We're all set. Our team will contact you soon{contact_part}. If you think of anything else, just message me anytime!"
			
			conversation_data.update(state.to_dict())
			return {
				"response": response,
				"should_end": True  # End the conversation
			}
			
		return None


