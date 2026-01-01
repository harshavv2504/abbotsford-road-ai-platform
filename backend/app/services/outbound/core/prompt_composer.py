from typing import Dict, List

"""
Prompt Composer (core)

What it does:
- Builds LLM message history and dynamic context (RAG snippets, collected fields, stage guidance) and
  selects the correct system instruction for the turn.

If you change it:
- You affect the LLM’s inputs and persona enforcement. Adjust here to change prompt framing without
  touching business logic.
"""

from app.services.rag.retriever import retriever
from app.services.outbound.prompt_handler import outbound_prompt_handler
from app.services.outbound.state_manager import ConversationState
from app.utils.logger import logger


class PromptComposer:
	"""Builds message history and LLM context for outbound responses.

	Edit here to adjust how much history we include, what context we surface, and which
	instructions are selected by stage.
	"""

	def __init__(self):
		self.retriever = retriever
		self.prompt_handler = outbound_prompt_handler

	def build_message_history(self, conversation_history: List[Dict], current_message: str) -> List[Dict]:
		messages: List[Dict] = []
		for msg in conversation_history[-6:]:
			if 'user' in msg:
				messages.append({"role": "user", "content": msg['user']})
			elif 'bot' in msg:
				messages.append({"role": "assistant", "content": msg['bot']})
		messages.append({"role": "user", "content": current_message})
		return messages

	def build_context(self, user_message: str, state: ConversationState, is_question: bool) -> List[str]:
		context_parts: List[str] = []
		if is_question:
			relevant_docs = self.retriever.retrieve(user_message, k=2)
			if relevant_docs:
				rag_context = self.retriever.format_context_for_llm(relevant_docs)
				context_parts.append(f"Knowledge base:\n{rag_context}")
		collected_data = {}
		if state.customer_type:
			all_fields = state.get_all_fields(state.customer_type)
			for field in all_fields:
				value = state.get_field(field)
				if value and value != "to_be_discussed_with_team":
					collected_data[field] = value
		else:
			if state.name:
				collected_data["name"] = state.name
			if state.phone:
				collected_data["phone"] = state.phone
			if state.email:
				collected_data["email"] = state.email
		if collected_data:
			context_parts.append("📋 ALREADY COLLECTED DATA (NEVER ask for these again):")
			for field, value in collected_data.items():
				context_parts.append(f"   • {field}: {value}")
			context_parts.append("")
			context_parts.append("💡 IMPORTANT:")
			context_parts.append("   - Reference this data naturally in your responses")
			context_parts.append("   - NEVER ask for information you already have")
			context_parts.append("")
			
			# Only show "talk to person" instructions if human connection is NOT already confirmed
			if not state.human_connection_confirmed:
				if collected_data.get('phone'):
					context_parts.append("📞 IF USER ASKS TO TALK TO A PERSON/TEAM/SOMEONE:")
					context_parts.append(f"   → Say: 'Great! Our team will reach out to you at {collected_data['phone']}. Is that still the best number?'")
					context_parts.append("   → After they confirm, ask: 'And what's your email in case we can't reach you by phone?'")
					context_parts.append("")
				else:
					context_parts.append("📞 IF USER ASKS TO TALK TO A PERSON/TEAM/SOMEONE:")
					context_parts.append("   → Ask: 'I'd be happy to connect you with our team! What's the best number to reach you?'")
					context_parts.append("   → After getting phone, ask: 'And what's your email in case we can't reach you by phone?'")
					context_parts.append("")
		if state.intent_stage == "exploring":
			context_parts.append("🔍 Stage: EXPLORING - User is asking questions. Answer naturally and help them explore.")
			context_parts.append("💡 If user shares contact info (name/email/phone), acknowledge it warmly before continuing.")
		elif state.intent_stage == "interest_detected":
			context_parts.append("🔍 Stage: INTEREST DETECTED - User showed interest but hasn't committed.")
			context_parts.append("� GResponse style:")
			context_parts.append("   - Answer their questions fully and naturally")
			context_parts.append("   - Occasionally (not every time) include a gentle nudge to gauge their readiness")
			context_parts.append("   - Don't be pushy - let them explore at their own pace")
			context_parts.append("💡 Gentle nudge examples (use sparingly):")
			context_parts.append("   'Sounds like you're thinking about opening a café?'")
			context_parts.append("   'Are you planning to open soon, or still exploring?'")
			context_parts.append("   'Curious - are you opening a new place or already running one?'")
		elif state.intent_stage == "intent_confirmed":
			context_parts.append("✅ Stage: INTENT CONFIRMED - This is the FIRST message after detecting user's intent.")
			context_parts.append("🎯 CRITICAL: You MUST start with a warm transition that:")
			context_parts.append("   1. Celebrates their plans enthusiastically AND acknowledges specific details they shared")
			context_parts.append("   2. Asks permission to learn more (don't just start interrogating)")
			context_parts.append("   3. Then asks the FIRST qualification question naturally")
			context_parts.append("")
			context_parts.append("💬 REQUIRED FORMAT:")
			context_parts.append("   [Celebrate + Acknowledge specifics] + [Ask permission] + [First question]")
			context_parts.append("")
			context_parts.append("✅ GOOD EXAMPLES:")
			context_parts.append("   'That's so exciting! Opening a café is a big adventure. Mind if I ask a few questions so we can help you out? When are you thinking of opening?'")
			context_parts.append("   'Love it! Four cafés—that's impressive! I'd love to learn more about your operation. Mind if I ask a few questions? What's been your biggest challenge with your current supplier?'")
			context_parts.append("   'This is going to be amazing! Opening in 3 months—that's coming up fast! Let me learn a bit about your vision. What kind of coffee style are you thinking?'")
			context_parts.append("")
			context_parts.append("💡 ACKNOWLEDGE SPECIFICS from collected data:")
			if collected_data:
				if collected_data.get('cafe_count'):
					cafe_count_display = collected_data['cafe_count'].replace('_', ' ')
					context_parts.append(f"   → They mentioned: {cafe_count_display} - acknowledge this!")
				if collected_data.get('timeline'):
					timeline_display = collected_data['timeline'].replace('_', ' ')
					context_parts.append(f"   → They mentioned timeline: {timeline_display} - acknowledge this!")
			context_parts.append("")
			context_parts.append("❌ BAD (Don't do this):")
			context_parts.append("   'When are you thinking of opening?' (Too abrupt, no celebration!)")
			context_parts.append("   'Let me ask a few questions. What's your timeline?' (Sounds like interrogation!)")
			context_parts.append("   'That's fantastic! When are you opening?' (Missing permission/transition!)")
			context_parts.append("   'Got it! Who am I chatting with?' (Ignores what they just told you!)")
		elif state.intent_stage == "qualifying":
			if state.customer_type:
				collected_fields = state.get_collected_fields(state.customer_type)
				missing_fields = state.get_missing_fields(state.customer_type)
				required_fields = state.get_required_fields(state.customer_type)
				logger.info(f"Collected fields: {collected_fields}")
				logger.info(f"Missing fields: {missing_fields}")
				logger.info(f"Skipped preferred count: {state.skipped_preferred_count}")
				MAX_PREFERRED_SKIPS = 2
				if state.skipped_preferred_count >= MAX_PREFERRED_SKIPS:
					context_parts.append(f"🎯 SMART SKIP: User skipped {state.skipped_preferred_count} preferred fields - they're in early exploration phase")
					context_parts.append("💡 Use friendly transition with celebration:")
					context_parts.append("   'No worries! Sounds like you're still in the early planning stages—that's totally normal!'")
					context_parts.append("   'Our team can help you figure out all the details when they connect with you.'")
				if collected_fields:
					context_parts.append(f"✅ Already collected: {', '.join(collected_fields)}")
				if missing_fields:
					from app.services.outbound.question_generator import question_generator
					next_field = missing_fields[0]
					is_required = next_field in required_fields
					ask_count = state.track_field_ask(next_field)
					if state.should_skip_field():
						state.set_field(next_field, "to_be_discussed_with_team")
						state.reset_field_tracking()
						missing_fields = state.get_missing_fields(state.customer_type)
						if missing_fields:
							next_field = missing_fields[0]
							is_required = next_field in required_fields
							ask_count = state.track_field_ask(next_field)
					next_field_question = question_generator.get_field_question(next_field, state.customer_type)
					missing_required = [f for f in missing_fields if f in required_fields]
					missing_preferred = [f for f in missing_fields if f not in required_fields]
					if missing_required:
						context_parts.append(f"🔴 REQUIRED (must have): {', '.join(missing_required)}")
					if missing_preferred:
						context_parts.append(f"🟡 PREFERRED (nice to have, can skip if unclear): {', '.join(missing_preferred)}")
					# Contact requirement (phone OR email)
					needs_contact = not (state.phone or state.email)
					if needs_contact:
						context_parts.append("🔴 REQUIRED: phone OR email (at least one)")
					if is_required:
						context_parts.append(f"🎯 Ask EXACTLY (REQUIRED): {next_field_question}")
					else:
						# Treat contact fields as required if neither is present
						if next_field in ["phone", "email"] and needs_contact:
							context_parts.append(f"🎯 Ask EXACTLY (REQUIRED): {next_field_question}")
						else:
							context_parts.append(f"🎯 Ask EXACTLY (optional, can skip if they don't know): {next_field_question}")
		elif state.intent_stage == "qualified":
			context_parts.append("✅ Customer is qualified! They've shared their info - be warm and supportive.")
			context_parts.append("💡 Keep the conversation going:")
			context_parts.append("   - Answer their questions enthusiastically")
			context_parts.append("   - Show excitement about their journey")
			context_parts.append("   - Reference their plans naturally")
			context_parts.append("   - Keep door open: 'Any other questions while we're chatting?'")
			context_parts.append("")
			context_parts.append("✅ GOOD: 'Great question! [answer]. This is going to be so cool for your café!'")
			context_parts.append("❌ BAD: '[answer]' (Too cold, no warmth)")
		return context_parts

	def select_system_instruction(self, use_rag_instruction: bool) -> str:
		if use_rag_instruction:
			logger.info("Using RAG answer instruction (no customer type detected)")
			return self.prompt_handler.get_rag_answer_instruction()
		return self.prompt_handler.get_system_instruction()


