"""
LLM-based Extractor

What it does:
- Uses LLM function calling to extract structured data from user messages
- Validates extracted contact information
- Handles context-aware extraction for different customer types
"""

from typing import Dict, List, Optional
import json
from app.services.llm_service import llm_service
from app.services.outbound.extraction.function_defs import EXTRACTION_FUNCTION_DEF
from app.services.outbound.extraction.validators import extraction_validators
from app.utils.logger import logger


class LLMExtractor:
    """LLM-based field extraction using function calling"""
    
    def __init__(self):
        self.llm_service = llm_service
        self.extraction_function_def = EXTRACTION_FUNCTION_DEF
        self.validators = extraction_validators
    
    async def extract_fields_with_llm(
        self, 
        user_message: str, 
        customer_type: str,
        conversation_history: Optional[List[Dict]] = None,
        state = None
    ) -> Dict:
        """
        Extract all possible fields from message using LLM function calling
        
        Args:
            user_message: User's current message
            customer_type: "new_cafe" or "existing_cafe"
            conversation_history: Recent conversation for context
            state: ConversationState for context-aware extraction
        
        Returns:
            Dict of extracted fields (only non-null values)
        """
        if customer_type == "new_cafe":
            context = "This is for someone OPENING A NEW CAFÉ. Use 'coffee_style' for their coffee preference."
        elif customer_type == "existing_cafe":
            context = """This is for an EXISTING CAFÉ OWNER. 
- Use 'current_coffee_style' for what they currently serve NOW
- Use 'coffee_preference' ONLY if they're discussing exploring NEW/DIFFERENT styles
- Do NOT extract 'coffee_preference' unless they're explicitly talking about trying new coffee options"""
        else:
            context = ""
        
        # Build context from recent conversation for better extraction
        context_str = ""
        if conversation_history:
            recent_messages = []
            for msg in conversation_history[-2:]:  # Last 2 messages for context
                if 'user' in msg:
                    recent_messages.append(f"User: {msg['user']}")
                elif 'bot' in msg:
                    recent_messages.append(f"Bot: {msg['bot']}")
            
            if recent_messages:
                context_str = "\n\nRecent conversation:\n" + "\n".join(recent_messages)
        
        extraction_prompt = f"""Extract SPECIFIC information from this user message. Be strict - only extract clear, actionable data.

Current message: "{user_message}"{context_str}

Customer type: {customer_type}
{context}

EXTRACTION RULES:

✅ EXTRACT if SPECIFIC:
- timeline: "asap", "in_3_months", "in_6_months", "depends_on_funding", "june_2025", "soon", "immediately" (Extract ANY timeframe mentioned. ONLY use "unclear" if user says "not sure" or "don't know" without any timeframe)
- coffee_style: "dark_and_strong", "french_roast", "single_origin_ethiopian" (preserve exact terms)
- equipment: "no_equipment", "have_2_espresso_machines", "starting_from_scratch" (preserve exact terms. If user says "need to sort out equipment" or "don't have any", use "starting_from_scratch")
- volume: "200_cups_daily", "100_to_150_per_day" (NOT "busy" → use "unclear")
- current_pain_points: "late_deliveries", "no_supplier_issues", "inconsistent_quality" (ONLY extract if user EXPLICITLY mentions the problem. "want to switch" → use "unclear")
- cafe_count: "three_locations", "one_cafe", "two_cafes_expanding_to_four" (NOT "few" → use "unclear")
- support_needs: "barista_training", "no_additional_services", "equipment_service_and_menu_design" (ONLY extract if user EXPLICITLY mentions services. Do NOT infer from silence)
- current_coffee_style: "dark_roast_and_colombian", "variety_of_specialty_blends" (what they serve NOW)
- coffee_preference: "satisfied_current", "interested_ethiopian_single_origin" (ONLY if discussing exploring NEW styles)
- name: "Sarah", "John Smith" (NOT "i'm", "me")
- phone: actual phone number
- email: actual email address

❌ USE "unclear" for VAGUE responses:
- "unclear" triggers smart clarification questions that reference user's words
- Use "null" ONLY if the topic is not mentioned at all
- Always preserve exact customer terminology with underscore formatting
- Handle "no issues" and "no services" as valid specific responses
- System will ask contextual follow-up questions for unclear responses

Use "null" for fields not mentioned OR if response is too vague to be useful.
Only extract information that is SPECIFIC and ACTIONABLE."""

        try:
            response = await self.llm_service.generate_response(
                messages=[{"role": "user", "content": extraction_prompt}],
                tools=self.extraction_function_def,
                tool_choice={"type": "function", "function": {"name": "extract_customer_data"}},
                temperature=0.0,
                max_tokens=300
            )
            
            # Check if function was called
            if response.get("type") == "function_call":
                function_args = json.loads(response["function_args"])
                
                # Filter out null values
                extracted = {k: v for k, v in function_args.items() if v and v != "null"}
                
                # BUG-002 FIX: Capitalize name if present
                if "name" in extracted and extracted["name"]:
                    extracted["name"] = extracted["name"].title()
                
                # BUG-FIX: Restrict extraction to contact info only if customer type is unclear (exploration mode)
                if customer_type == "unclear":
                    allowed_fields = ["name", "phone", "email"]
                    filtered = {k: v for k, v in extracted.items() if k in allowed_fields}
                    if len(filtered) < len(extracted):
                        logger.info(f"🛡️ Exploration Mode: Filtered out fields {list(set(extracted) - set(filtered))} (keeping only contact info)")
                    extracted = filtered
                
                # BUG-001 FIX: Validate contact fields to prevent preference words being stored
                if "email" in extracted:
                    email_value = extracted["email"]
                    if not self.validators.is_actual_email(email_value):
                        logger.info(f"⚠️ BUG-001 FIX: Rejected invalid email (preference word): '{email_value}'")
                        extracted.pop("email")
                        # Set flag in state if available
                        if state:
                            state.email_preference_indicated = True
                
                if "phone" in extracted:
                    phone_value = extracted["phone"]
                    # BUG-001 FIX: Don't pre-validate phone here. Let extraction_pipeline handle it 
                    # so we can give proper error messages for invalid numbers like "636737".
                    # Only filter if it's clearly NOT a phone number (like a word)
                    if any(c.isalpha() for c in phone_value) and not any(c.isdigit() for c in phone_value):
                         logger.info(f"⚠️ Rejected non-phone value: '{phone_value}'")
                         extracted.pop("phone")
                         if state:
                             state.phone_preference_indicated = True
                
                # Context-aware filtering for existing_cafe
                if customer_type == "existing_cafe" and "coffee_preference" in extracted:
                    # Only keep coffee_preference if current_coffee_style is already collected in state
                    # This prevents extracting coffee_preference before we know their current style
                    if state and not state.current_coffee_style:
                        logger.info("Skipping coffee_preference - will ask after current_coffee_style is collected")
                        extracted.pop("coffee_preference")
                    elif not state and "current_coffee_style" not in extracted:
                        # Fallback: if no state provided, check current extraction (backward compatibility)
                        logger.info("Skipping coffee_preference - no state provided and current_coffee_style not in extraction")
                        extracted.pop("coffee_preference")
                
                logger.info(f"LLM extracted fields: {list(extracted.keys())}")
                return extracted
            else:
                logger.warning("LLM did not call extraction function")
                return {}
                
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return {}


# Singleton instance
llm_extractor = LLMExtractor()
