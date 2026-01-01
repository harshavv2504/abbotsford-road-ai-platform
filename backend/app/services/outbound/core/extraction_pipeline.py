from typing import Dict, List, Optional

"""
Extraction Pipeline (core)

What it does:
- Runs LLM extraction, validates/normalizes fields (phone/email/name), asks clarifications, handles
  fallback extraction, and special phone-country/email-typo flows.

If you change it:
- You alter how user inputs are captured and cleaned across the whole bot. Add new fields or rules here
  to keep extraction concerns out of the orchestrator.
"""

from app.services.outbound.state_manager import ConversationState
from app.utils.logger import logger


class ExtractionPipeline:
	"""Handles field extraction, validation/normalization, and clarification prompts.

	Modify this class to tweak extraction thresholds, validation strategy, or clarification prompts.
	Keep return values short-circuiting when we need to respond immediately.
	"""

	def __init__(self, *, extraction_service, validation_service, question_generator):
		self.extraction_service = extraction_service
		self.validation_service = validation_service
		self.question_generator = question_generator

	async def process(self, user_message: str, conversation_history: List[Dict], state: ConversationState, conversation_data: Dict, early_extracted_fields: Dict = None) -> Optional[Dict]:
		"""
		Run extraction + validation. Returns an early response dict when a clarification
		or follow-up question should be asked immediately; otherwise None.
		
		Args:
			early_extracted_fields: Pre-extracted fields from parallel execution (optional)
		"""
		# BUG-007 FIX: Track user engagement
		state.track_user_engagement(user_message)
		
		# BUG-007 FIX: If user is disengaged, offer to simplify or end detailed discussion
		if state.user_engagement_level == "low" and state.can_start_qualification():
			logger.info("⚠️ BUG-007 FIX: User showing low engagement - offering to simplify")
			conversation_data.update(state.to_dict())
			return {
				"response": "I sense you might want to keep things simple. Would you like me to just get your contact info so our team can reach out directly?",
				"should_end": False
			}
		
		# Contact refusal is now handled by flow state detection in outbound_bot.py
		# This ensures consistent handling via the flow state "refuses_contact_info"
		
		# Handle phone confirmation response FIRST (before extraction)
		# This prevents "yes" from being misinterpreted as other fields
		if state.pending_phone_confirmation and not state.phone:
			message_lower = user_message.lower().strip()
			# Check for affirmative responses
			if any(word in message_lower for word in ["yes", "yeah", "yep", "correct", "right", "that's right", "yup", "sure", "ok", "okay"]):
				# User confirmed the number
				state.phone = state.pending_phone_confirmation
				state.pending_phone_confirmation = None
				state.reset_phone_attempts()
				logger.info(f"✅ Phone confirmed by user: {state.phone}")
				
				# Check if we need email backup
				if not state.email and (state.can_start_qualification() or state.wants_to_place_order) and not state.human_connection_confirmed:
					conversation_data.update(state.to_dict())
					return {
						"response": "Awesome, thanks for confirming! Just to be safe, what's your email in case we can't reach you by phone?",
						"should_end": False
					}
				
				# Check if qualification is complete
				if state.is_complete(state.customer_type):
					logger.info(f"✅ Qualification complete after phone confirmation")
					state.is_qualified = True
					from app.utils.validators import format_phone_for_display
					contact = state.email if state.email else format_phone_for_display(state.phone)
					conversation_data.update(state.to_dict())
					return {
						"response": f"Perfect! I've got all your details, {state.name}. Our team will reach out to you at {contact}. Is there anything else you'd like to know about our coffee?",
						"should_end": False
					}
				
				# Continue to next field
				result_next = self._next_field_question(state)
				if result_next:
					conversation_data.update(state.to_dict())
					return result_next
			else:
				# User rejected or provided a different number - check if they provided a new number with country code
				from app.utils.validators import extract_phone_from_text
				new_phone = extract_phone_from_text(user_message)
				if new_phone and (new_phone.startswith("+") or "+" in user_message):
					# Try to validate the new number
					result = self.validation_service.validate_and_format_phone(new_phone, state.country_code, user_message)
					if result["success"]:
						state.phone = result["formatted_phone"]
						state.pending_phone_confirmation = None
						state.reset_phone_attempts()
						if result.get("country"):
							state.country_code = result["country"]
						logger.info(f"✅ User provided corrected phone: {state.phone}")
						
						# Check if we need email backup
						if not state.email and (state.can_start_qualification() or state.wants_to_place_order) and not state.human_connection_confirmed:
							conversation_data.update(state.to_dict())
							return {
								"response": "Perfect! Just to be safe, what's your email in case we can't reach you by phone?",
								"should_end": False
							}
						
						# Check if qualification is complete
						if state.is_complete(state.customer_type):
							logger.info(f"✅ Qualification complete after phone correction")
							state.is_qualified = True
							from app.utils.validators import format_phone_for_display
							contact = state.email if state.email else format_phone_for_display(state.phone)
							conversation_data.update(state.to_dict())
							return {
								"response": f"Perfect! I've got all your details, {state.name}. Our team will reach out to you at {contact}. Is there anything else you'd like to know about our coffee?",
								"should_end": False
							}
						
						# Continue to next field
						result_next = self._next_field_question(state)
						if result_next:
							conversation_data.update(state.to_dict())
							return result_next
				
				# No valid phone provided, ask again
				state.pending_phone_confirmation = None
				conversation_data.update(state.to_dict())
				return {"response": "No problem! Please provide your phone number with the country code (e.g., +1 555-123-4567 for US).", "should_end": False}

		extracted_fields: Dict = {}
		should_extract = False
		# Enable extraction during qualification OR when handling order flow (even without customer type)
		if state.customer_type:
			if state.can_start_qualification() and not state.is_qualified:
				should_extract = True
			elif not state.name or not state.phone or not state.email:
				should_extract = True
		elif state.wants_to_place_order:
			# For order flow, we still want to extract/validate phone/email
			should_extract = True
		elif not state.name or not state.phone or not state.email:
			# Extract contact info anytime it's volunteered, even during exploration
			should_extract = True
		if not should_extract:
			logger.info(f"Skipping extraction - all contact fields collected and not in qualification")
			return None

		# OPTIMIZATION: Use early extracted fields if available (from parallel execution)
		if early_extracted_fields:
			extracted_fields = early_extracted_fields
			logger.info(f"✅ Using parallel-extracted fields: {list(extracted_fields.keys()) if extracted_fields else 'nothing'}")
		else:
			# Primary LLM extraction (default to "new_cafe" when type unknown)
			extracted_fields = await self.extraction_service.extract_fields_with_llm(
				user_message,
				state.customer_type or "new_cafe",
				conversation_history,
				state
			)
			logger.info(f"LLM extracted: {list(extracted_fields.keys()) if extracted_fields else 'nothing'}")

		# Mark as qualifying when we start active qualification
		if state.can_start_qualification() and not state.is_qualified and state.intent_stage == "intent_confirmed":
			state.set_intent_stage("qualifying")

		# Handle explicit email refusal during order flow (mirror talk-to-person behavior)
		try:
			from app.services.outbound.extraction.validators import ExtractionValidators
			extractor_validators = ExtractionValidators()
		except Exception:
			extractor_validators = None
		if state.wants_to_place_order and extractor_validators and state.phone and not state.email:
			if extractor_validators.detect_refusal(user_message):
				state.track_contact_refusal("email")
				state.email = "user_declined"
				phone_display = f"*****{state.phone[-4:]}"
				conversation_data.update(state.to_dict())
				return {"response": f"No problem! We'll use {phone_display} to connect. Is there anything else you'd like to know?", "should_end": False}

		# Validate and store
		if extracted_fields:
			for key, value in extracted_fields.items():
				if not value or state.get_field(key):
					continue
				
				# BUG-008 FIX: Validate extraction consistency
				if not self.extraction_service.validate_extraction_consistency(user_message, key, value):
					logger.warning(f"⚠️ BUG-008 FIX: Skipping {key} due to extraction mismatch")
					continue
				
				# BUG-005 FIX: Check for ambiguous numbers in volume/timeline fields
				if key in ["volume", "timeline"] and self.extraction_service.is_ambiguous_number(user_message, key):
					conversation_data.update(state.to_dict())
					if key == "volume":
						return {
							"response": f"{user_message} what? Cups per day, or something else?",
							"should_end": False
						}
					elif key == "timeline":
						return {
							"response": f"{user_message} what? Days, weeks, months, or something else?",
							"should_end": False
						}
				
				if key == "name":
					result = self.validation_service.validate_name(value)
					if not result["success"]:
						continue
					value = result["cleaned_name"]
				elif key == "phone":
					# Try to validate phone number (will default to US for 10-digit numbers)
					result = self.validation_service.validate_and_format_phone(value, state.country_code, user_message)
					if not result["success"]:
						# Treat order flow like qualification for validation UX
						if (state.can_start_qualification() and not state.is_qualified) or state.wants_to_place_order:
							attempts = state.increment_phone_attempts()
							if attempts == 1:
								# First attempt: Try to format as US number and ask for confirmation
								digits_only = ''.join(filter(str.isdigit, value))
								if len(digits_only) == 10:
									# Format as US number for confirmation
									formatted_display = f"+1 {digits_only[:3]} {digits_only[3:6]} {digits_only[6:]}"
									state.pending_phone_confirmation = f"+1{digits_only}"
									conversation_data.update(state.to_dict())
									return {"response": f"Is {formatted_display} the best number to reach you? If not, please share your number with the country code.", "should_end": False}
								else:
									conversation_data.update(state.to_dict())
									# Align error copy with human-connection flow for first failure
									return {"response": "I didn't catch that number. Could you share it again? (US numbers like 555-123-4567, or include +1 if you prefer)", "should_end": False}
							# After max attempts, format with country code before storing for manual review
							state.flag_phone_for_review()
							state.reset_phone_attempts()
							# Format phone with detected country code from message or state
							from app.utils.validators import extract_country_from_text
							detected_country = extract_country_from_text(user_message) or state.country_code or "US"
							digits_only = ''.join(filter(str.isdigit, value))
							
							# Map country to country code prefix
							country_code_map = {
								"US": "+1", "CA": "+1",
								"GB": "+44", "UK": "+44",
								"AU": "+61", "NZ": "+64",
								"IN": "+91", "CN": "+86", "JP": "+81"
							}
							country_prefix = country_code_map.get(detected_country, "+1")
							
							if len(digits_only) >= 10:
								value = f"{country_prefix}{digits_only}"
								logger.info(f"Formatted phone for manual review: {value} (country: {detected_country})")
								# Store the detected country
								if detected_country:
									state.country_code = detected_country
						else:
							logger.info("Phone validation failed outside qualification/order - skipping")
							continue
					else:
						# Validation succeeded - check if we should ask for confirmation
						# If it's a 10-digit number without explicit country code in the message, ask for confirmation
						digits_only = ''.join(filter(str.isdigit, value))
						has_explicit_country = value.startswith("+") or any(indicator in user_message.lower() for indicator in ["+1", "us number", "usa", "united states", "country code"])
						
						if len(digits_only) == 10 and not has_explicit_country and (state.can_start_qualification() or state.wants_to_place_order):
							# Ask for confirmation with formatted display
							from app.utils.validators import format_phone_for_display
							formatted_display = format_phone_for_display(result["formatted_phone"])
							state.pending_phone_confirmation = result["formatted_phone"]
							conversation_data.update(state.to_dict())
							return {"response": f"Is {formatted_display} the best number to reach you? If not, please share your number with the country code.", "should_end": False}
						
						# Otherwise, store directly
						state.reset_phone_attempts()
						value = result["formatted_phone"]
						if result.get("country"):
							state.country_code = result["country"]
				elif key == "email":
					result = self.validation_service.validate_and_format_email(value)
					if not result["success"]:
						# Treat order flow like qualification for validation UX
						if (state.can_start_qualification() and not state.is_qualified) or state.wants_to_place_order:
							attempts = state.increment_email_attempts()
							if attempts == 1:
								if result.get("typo_detected") and result.get("suggested_correction"):
									suggested = result["suggested_correction"]
									state.set_email_typo_suggested(suggested)
									conversation_data.update(state.to_dict())
									return {"response": f"I think you meant {suggested}—is that right?", "should_end": False}
								conversation_data.update(state.to_dict())
								# Friendly invalid-email message (mirrors human-connection tone)
								return {"response": f"{result['error']} Please share a valid email address.", "should_end": False}
							# On subsequent attempts, allow storing as-is to avoid loops (will be handled downstream if needed)
							state.reset_email_attempts()
							value = value
						else:
							logger.info("Email validation failed outside qualification/order - skipping")
							continue
					else:
						state.reset_email_attempts()
						value = result["normalized_email"]
				elif key == "current_pain_points":
					if value == "unclear" or self.validation_service.is_vague_pain_point(value):
						logger.info("Vague/unclear pain point detected")
						clarification_question = self.question_generator.get_clarification(key, user_message, state)
						if clarification_question:
							conversation_data.update(state.to_dict())
							return {"response": clarification_question, "should_end": False}
						continue
				elif key == "coffee_preference":
					if value == "interested_unspecified":
						conversation_data.update(state.to_dict())
						return {"response": "what styles are you thinking about—bold, classic, specialty, or something specific?", "should_end": False}
					elif value == "unclear":
						state.coffee_preference = "needs_discussion_with_team"
						conversation_data.update(state.to_dict())
						return {"response": "no worries! Our team can walk through all the options when they connect with you", "should_end": False}
				# Store validated
				state.set_field(key, value)
				state.reset_field_tracking()
				logger.info(f"Stored {key}: {value}")
				
				# BUG-008 FIX: Track that this topic was discussed
				state.mark_topic_discussed(key, value)
				
				# BUG-008 FIX: Track if user was uncertain
				if value in ["unclear", "to_be_discussed_with_team"]:
					state.mark_user_uncertain(key)
				
				# Order flow: after phone, ask for email backup; after email/refusal, confirm outreach
				if state.wants_to_place_order:
					if key == "phone" and not state.email:
						conversation_data.update(state.to_dict())
						return {"response": "Perfect! Just to be safe, what's your email in case we can't reach you by phone?", "should_end": False}
					if key == "email" or (key == "phone" and state.email == "user_declined"):
						from app.utils.validators import format_phone_for_display
						if key == "email" and state.email and state.email != "user_declined":
							contact = state.email
						else:
							contact = format_phone_for_display(state.phone)
						logger.info(f"✅ ORDER FLOW: Contact info collected for order request - {key}: {contact}")
						conversation_data.update(state.to_dict())
						return {
							"response": f"Awesome! I've noted your request. Our team will reach out to you at {contact} to process your order. They'll get back to you shortly!",
							"should_end": False
						}
				
				# Check if qualification is complete after collecting contact info
				if key in ["phone", "email"]:
					if state.is_complete(state.customer_type):
						logger.info(f"✅ Qualification complete after collecting {key}")
						state.is_qualified = True
						from app.utils.validators import format_phone_for_display
						contact = state.email if state.email else format_phone_for_display(state.phone)
						conversation_data.update(state.to_dict())
						return {
							"response": f"Perfect! I've got all your details, {state.name}. Our team will reach out to you at {contact}. Is there anything else you'd like to know about our coffee?",
							"should_end": False
						}
				
				# BUG-003 FIX: After phone is collected, ask for email backup (also in order flow)
				# BUT: Don't ask if human connection is confirmed (they only need one contact method)
				if key == "phone" and not state.email and (state.can_start_qualification() or state.wants_to_place_order) and not state.human_connection_confirmed:
					logger.info("✅ BUG-003 FIX: Phone collected, requesting email backup")
					conversation_data.update(state.to_dict())
					return {
						"response": "Awesome, thanks for sharing your phone number! Just to be safe, what's your email in case we can't reach you by phone?",
						"should_end": False
					}

		# NOTE: Country clarification is now handled inline during phone validation
		# NOTE: Phone confirmation is now handled at the start of process() to prevent "yes" misinterpretation
		
		# Pending phone with provided country
		if state.pending_phone and not state.phone:
			from app.utils.validators import extract_country_from_text
			country = extract_country_from_text(user_message)
			if country:
				result = self.validation_service.validate_and_format_phone(state.pending_phone, country)
				if result["success"]:
					state.phone = result["formatted_phone"]
					state.country_code = country
					state.pending_phone = None
					logger.info(f"Formatted phone with country {country}: {state.phone}")
					result_next = self._next_field_question(state)
					if result_next:
						conversation_data.update(state.to_dict())
						return result_next
				else:
					state.pending_phone = None
					conversation_data.update(state.to_dict())
					return {"response": result["error"], "should_end": False}
			else:
				conversation_data.update(state.to_dict())
				return {"response": "I didn't catch the country. Is this a US number, or from another country? (like +1 for US, +44 for UK, etc.)", "should_end": False}

		# Vague pain point clarification via validator
		if "current_pain_points" in extracted_fields and self.validation_service.is_vague_pain_point(extracted_fields["current_pain_points"]):
			conversation_data.update(state.to_dict())
			return {"response": self.validation_service.get_clarification_prompt("current_pain_points", extracted_fields["current_pain_points"]), "should_end": False}

		# Fallback extraction if nothing was found but bot asked something
		last_bot_message = ""
		if conversation_history:
			for msg in reversed(conversation_history):
				if 'bot' in msg:
					last_bot_message = msg['bot']
					break
		if last_bot_message and not extracted_fields and state.customer_type:
			missing_fields = state.get_missing_fields(state.customer_type)
			# Skip fallback if user is qualified or if contact info is complete (even if declined)
			has_contact_info = (state.phone or state.phone == "user_declined") and (state.email or state.email == "user_declined")
			if missing_fields and not state.is_qualified and not has_contact_info:
				fallback = self.extraction_service.extract_fields_fallback(user_message, last_bot_message, state.customer_type, missing_fields)
				if fallback:
					for key, value in fallback.items():
						if key == "phone":
							result = self.validation_service.validate_and_format_phone(value, state.country_code)
							if not result["success"]:
								conversation_data.update(state.to_dict())
								return {"response": result["error"], "should_end": False}
							value = result["formatted_phone"]
						elif key == "email":
							result = self.validation_service.validate_and_format_email(value)
							if not result["success"]:
								if result.get("typo_detected") and result.get("suggested_correction"):
									suggested = result["suggested_correction"]
									if state.email_typo_suggested != suggested:
										state.set_email_typo_suggested(suggested)
										conversation_data.update(state.to_dict())
										return {"response": f"I think you meant {suggested}—is that right?", "should_end": False}
								conversation_data.update(state.to_dict())
								return {"response": result["error"], "should_end": False}
							value = result["normalized_email"]
						state.set_field(key, value)
						state.reset_field_tracking()
						logger.info(f"Fallback stored {key}: {value}")

		# BUG-001 FIX: Check if user indicated contact preference but didn't provide actual info
		if state.email_preference_indicated and not state.email:
			# Order flow: attempt direct validation of raw message before re-asking
			if state.wants_to_place_order:
				result = self.validation_service.validate_and_format_email(user_message)
				if result["success"]:
					state.email = result["normalized_email"]
					conversation_data.update(state.to_dict())
					return {"response": f"Awesome! I've noted your request. Our team will reach out to you at {state.email} to process your order. They'll get back to you shortly!", "should_end": False}
				else:
					# Offer typo correction if available; otherwise friendly error
					if result.get("typo_detected") and result.get("suggested_correction"):
						suggested = result["suggested_correction"]
						state.set_email_typo_suggested(suggested)
						conversation_data.update(state.to_dict())
						return {"response": f"I think you meant {suggested}—is that right?", "should_end": False}
					conversation_data.update(state.to_dict())
					return {"response": result["error"], "should_end": False}
			# Non-order flow fallback: re-ask
			logger.info("⚠️ BUG-001 FIX: User indicated email preference, requesting actual email")
			state.email_preference_indicated = False  # Reset flag
			conversation_data.update(state.to_dict())
			return {"response": "Great! What's your email address?", "should_end": False}
		
		if state.phone_preference_indicated and not state.phone:
			# Order flow: attempt direct validation on raw message before re-asking
			if state.wants_to_place_order:
				result = self.validation_service.validate_and_format_phone(user_message, state.country_code, user_message)
				if result["success"]:
					state.phone = result["formatted_phone"]
					if result.get("country"):
						state.country_code = result["country"]
					conversation_data.update(state.to_dict())
					return {"response": "Perfect! Just to be safe, what's your email in case we can't reach you by phone?", "should_end": False}
				else:
					conversation_data.update(state.to_dict())
					return {"response": "I didn't catch that number. Could you share it again? (US numbers like 555-123-4567, or include +1 if you prefer)", "should_end": False}
			# Non-order flow fallback: re-ask
			logger.info("⚠️ BUG-001 FIX: User indicated phone preference, requesting actual phone number")
			state.phone_preference_indicated = False  # Reset flag
			conversation_data.update(state.to_dict())
			return {"response": "I didn't catch a valid phone number. Could you please share it again?", "should_end": False}

		# Reset RAG counter if any field answered
		if extracted_fields:
			old_count = state.rag_questions_count
			if old_count > 0:
				state.reset_rag_count()
				logger.info(f"User answered field - reset RAG counter from {old_count} to 0")

		return None

	def _next_field_question(self, state: ConversationState) -> Optional[Dict]:
		missing_fields = state.get_missing_fields(state.customer_type)
		if not missing_fields:
			return None
		next_field = missing_fields[0]
		from app.services.outbound.question_generator import question_generator
		next_field_question = question_generator.get_field_question(next_field, state.customer_type)
		return {"response": f"Perfect! {next_field_question}", "should_end": False}


