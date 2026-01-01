"""
Extraction Function Definitions

What it does:
- Defines OpenAI function calling schemas for data extraction
- Provides structured extraction templates for LLM
"""

# Large function definition for customer data extraction
EXTRACTION_FUNCTION_DEF = [
    {
        "type": "function",
        "function": {
            "name": "extract_customer_data",
            "description": """Intelligently extract customer information from their message. Focus on capturing their exact words and specific details:

EXTRACTION PRINCIPLES:
- Preserve their exact terminology - don't translate or categorize
- Format consistently: lowercase with underscores for spaces
- Extract specific details, reject vague responses
- Capture multiple items when mentioned
- Only extract what they actually said, don't infer

QUALITY STANDARDS:
- SPECIFIC: "in 3 months", "french roast", "2 espresso machines" 
- REJECT VAGUE: "soon", "good coffee", "some equipment"
- PRESERVE EXACT: "dark and strong" → "dark_and_strong" (not "bold")
- MULTIPLE: "ethiopian and colombian" → "ethiopian_and_colombian"

CONTEXT AWARENESS:
- Consider conversation flow and what was just asked
- Extract relevant information even if phrased differently
- Handle follow-up responses and clarifications

Call this for EVERY user message to extract any customer data they provide.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "timeline": {
                        "type": "string",
                        "description": """Extract their timeline for opening the café. Be specific about timeframes:

SPECIFIC TIMELINES (extract exactly):
- Absolute dates: "tomorrow", "this week", "next month", "in 3 months", "June 2024", "Q1 2025"
- Relative timeframes: "next year", "sometime next year", "early 2025", "late next year", "end of year"
- Seasonal: "spring 2025", "summer next year", "fall 2025", "winter 2026"
- Event-based: "within 6 weeks", "by Christmas", "after permits approved"

CONDITIONAL TIMELINES:
- "depends_on_funding" for "depends on funding", "when we get investment", "once funding comes through"
- "waiting_for_permits" for "waiting for permits", "once approvals come through", "after permits"
- "depends_on_location" for "when we find the right spot", "location dependent", "once we find a place"

VAGUE RESPONSES (use "unclear"):
- "soon", "later", "eventually", "not sure", "sometime" (WITHOUT a timeframe)
- "when ready", "in the future", "one day"

EXAMPLES:
- "in 3 months" → "in_3_months"
- "sometime next year" → "sometime_next_year"
- "early 2025" → "early_2025"
- "depends on getting the loan" → "depends_on_funding"
- "soon" → "unclear"
- "sometime" (alone) → "unclear"
- "June next year" → "june_2025"

Use null if not mentioned."""
                    },
                    "coffee_style": {
                        "type": "string",
                        "description": """Extract their coffee style preference for the new café. Capture their exact words, formatted neatly:

PRESERVE EXACT TERMS:
- "dark_and_strong" for "dark and strong"
- "medium_roast" for "medium roast"
- "single_origin" for "single origin"
- "french_roast" for "French roast"
- "ethiopian_coffee" for "Ethiopian coffee"
- "cold_brew_blends" for "cold brew blends"
- "fair_trade_organic" for "fair trade organic"

FORMATTING RULES:
- Replace spaces with underscores: "dark roast" → "dark_roast"
- Lowercase everything: "French Roast" → "french_roast"
- Keep their exact terminology, don't translate to categories

MULTIPLE PREFERENCES:
- "dark_roast_and_specialty" for "dark roast and specialty"
- "ethiopian_and_colombian" for "Ethiopian and Colombian"

EXAMPLES:
- "dark and strong" → "dark_and_strong"
- "French roast" → "french_roast"
- "single origin Ethiopian" → "single_origin_ethiopian"
- "balanced medium roast" → "balanced_medium_roast"
- "bold espresso blends" → "bold_espresso_blends"

Use null if not mentioned or unclear."""
                    },
                    "equipment": {
                        "type": "string",
                        "description": "SPECIFIC equipment situation (e.g., 'no equipment', 'have 2 espresso machines', 'starting from scratch'). Use null if vague (e.g., 'some', 'a bit') or not mentioned."
                    },
                    "volume": {
                        "type": "string",
                        "description": """Extract their expected daily coffee volume. Only extract clear numbers:

CLEAR NUMBERS (extract exactly):
- "200_cups_daily" for "200 cups daily", "200 per day"
- "100_to_150_cups" for "100-150 cups", "between 100 and 150"
- "50_cups_per_day" for "50 cups per day"
- "300_customers_daily" for "300 customers daily"
- "1000_cups_weekly" for "1000 cups weekly"
- "maybe_100_could_be_more" for "maybe 100, could be more"
- "probably_150_daily" for "probably 150 daily"
- "roughly_200_cups" for "roughly 200 cups"

ANYTHING UNCLEAR:
- "unclear" for ANY non-specific response:
  * "busy", "a lot", "many", "not sure"
  * "small volume", "medium sized", "high volume"
  * "very busy", "decent amount", "good traffic"
  * "depends", "varies", "not certain"

EXAMPLES:
- "around 200 cups daily" → "around_200_cups_daily"
- "100-150 per day" → "100_to_150_per_day"
- "busy place" → "unclear"
- "medium volume" → "unclear"
- "a lot of customers" → "unclear"
- "not sure yet" → "unclear"

Use null if not mentioned."""
                    },
                    "current_pain_points": {
                        "type": "string",
                        "description": """Extract their supplier situation - issues OR satisfaction:

NO SUPPLIER ISSUES:
- "no_supplier_issues" for "no problems", "no issues", "happy with current supplier"
- "satisfied_with_supplier" for "satisfied with current", "supplier is fine", "no complaints"

SPECIFIC ISSUES (extract exactly):
- "late_deliveries" for "late deliveries", "always late", "delivery issues"
- "inconsistent_quality" for "inconsistent quality", "quality varies", "coffee not consistent"
- "poor_customer_service" for "poor service", "bad support", "unresponsive team"
- "high_prices" for "too expensive", "high prices", "overpriced"
- "wrong_orders" for "wrong orders", "order mistakes", "delivery errors"

MULTIPLE ISSUES:
- "late_deliveries_and_poor_quality" for multiple specific problems
- "high_prices_and_bad_service" for combination issues

VAGUE/OPENING STATEMENTS (use null, NOT "unclear"):
- "looking for new supplier", "need new supplier", "want to switch"
- "few problems", "some issues", "not happy"
- "not satisfied", "could be better", "having trouble"
- "problems", "issues", "not good"
→ These are opening statements, not specific pain points. Use null and let the bot ask naturally later.

EXAMPLES:
- "no problems with supplier" → "no_supplier_issues"
- "supplier is fine, just need training" → "satisfied_with_supplier"
- "always late with deliveries" → "late_deliveries"
- "quality is inconsistent and prices too high" → "inconsistent_quality_and_high_prices"
- "looking for new supplier" → null (opening statement, not specific)
- "having some issues" → null (too vague, ask later)
- "not happy with them" → null (too vague, ask later)

Use null if not mentioned OR if too vague to be actionable."""
                    },
                    "cafe_count": {
                        "type": "string",
                        "description": """Extract the number of cafés they operate. Only extract clear numbers:

CLEAR NUMBERS (extract exactly):
- "one_cafe" for "one café", "1 location", "single location"
- "two_cafes" for "two cafés", "2 locations", "couple locations"
- "three_locations" for "3 locations", "three cafés"
- "five_cafes" for "5 cafés", "five locations"
- "ten_locations" for "10 locations", "ten cafés"

EXPANSION PLANS:
- "two_cafes_expanding_to_four" for "2 now, expanding to 4"
- "one_cafe_opening_second" for "one café, opening second location"

ANYTHING UNCLEAR:
- "unclear" for ANY non-specific response:
  * "few", "some", "multiple", "several"
  * "a couple", "many", "various locations"
  * "not sure", "depends", "growing"

EXAMPLES:
- "3 locations" → "three_locations"
- "one café" → "one_cafe"
- "few locations" → "unclear"
- "multiple cafés" → "unclear"
- "2 now, planning 3rd" → "two_cafes_expanding_to_three"

Use null if not mentioned."""
                    },
                    "support_needs": {
                        "type": "string",
                        "description": """Extract what additional services they need beyond coffee supply:

NO ADDITIONAL SERVICES:
- "no_additional_services" for "no", "just coffee", "coffee only", "nothing else"
- "only_coffee_supply" for "just need coffee", "only coffee supply needed"

SPECIFIC SERVICES (extract exactly):
- "barista_training" for "barista training", "staff training", "training programs"
- "equipment_service" for "equipment service", "machine maintenance", "technical support"
- "menu_design" for "menu design", "menu development", "help with menu"
- "marketing_support" for "marketing support", "marketing help", "promotional assistance"
- "business_consulting" for "business consulting", "operational guidance", "business advice"

MULTIPLE SERVICES:
- "barista_training_and_equipment_service" for multiple specific needs
- "menu_design_and_marketing_support" for combination requests

ANYTHING UNCLEAR:
- "unclear" for ANY vague responses:
  * "help", "support", "assistance"
  * "whatever you offer", "not sure", "depends"
  * "some help", "any support"

EXAMPLES:
- "barista training and equipment service" → "barista_training_and_equipment_service"
- "no, just coffee supply" → "no_additional_services"
- "some help with marketing" → "marketing_support"
- "not sure what we need" → "unclear"
- "whatever support you provide" → "unclear"

Use null if not mentioned."""
                    },
                    "current_coffee_style": {
                        "type": "string",
                        "description": """Extract the coffee styles they currently serve. Preserve their exact descriptions:

SINGLE STYLES (formatted):
- "dark_roast" for "dark roast", "dark coffee"
- "medium_roast" for "medium roast", "medium blend"
- "light_roast" for "light roast", "light coffee"
- "espresso_blends" for "espresso blends", "espresso coffee"
- "single_origin" for "single origin coffee"
- "house_blend" for "house blend", "our signature blend"
- "french_roast" for "French roast"
- "colombian_coffee" for "Colombian coffee"

MULTIPLE STYLES (very common):
- "dark_and_medium_roast" for "dark and medium roast"
- "espresso_and_single_origin" for "espresso and single origin"
- "house_blend_and_french_roast" for multiple specific styles
- "dark_medium_and_light_roast" for "we serve dark, medium, and light"
- "variety_of_blends" for "variety of blends", "different blends"

GENERAL CATEGORIES:
- "bold_coffee" for "bold", "strong coffee"
- "classic_coffee" for "classic", "traditional"
- "specialty_coffee" for "specialty", "artisan"

EXAMPLES:
- "French roast and Colombian single origin" → "french_roast_and_colombian_single_origin"
- "we serve dark, medium, and light roast" → "dark_medium_and_light_roast"
- "variety of specialty blends" → "variety_of_specialty_blends"
- "bold coffee" → "bold_coffee"

Use null if not mentioned."""
                    },
                    "coffee_preference": {
                        "type": "string",
                        "description": """Extract their response about exploring other coffee styles. Capture exactly what they mean:

SATISFIED WITH CURRENT:
- "no", "happy with current", "stick with what we have" → "satisfied_current"

INTERESTED WITH SPECIFICS:  
- "yes, want Ethiopian single origin" → "interested_ethiopian_single_origin"
- "interested in light roast" → "interested_light_roast"
- "want to try specialty blends" → "interested_specialty_blends"

INTERESTED GENERAL:
- "yes", "interested", "open to it" → "interested_general"

MAYBE/DEPENDS:
- "maybe", "depends", "not sure" → "maybe_interested"

EXAMPLES:
- "yes, interested in Ethiopian" → "interested_ethiopian"
- "no, happy with what we have" → "satisfied_current"
- "maybe, depends on price" → "maybe_interested"
- "yes" → "interested_general"

Use null if not mentioned."""
                    },
                    "name": {
                        "type": "string",
                        "description": "Extract their name (e.g., 'Sarah', 'John Smith'). Reject pronouns like 'I', 'me'. Use null if not mentioned."
                    },
                    "phone": {
                        "type": "string",
                        "description": "Extract phone number if provided. Use null if not mentioned or if they only express preference (e.g., 'yes', 'phone')."
                    },
                    "email": {
                        "type": "string",
                        "description": "Extract email address if provided. Use null if not mentioned or if they only express preference (e.g., 'yes', 'email')."
                    }
                },
                "required": []
            }
        }
    }
]
