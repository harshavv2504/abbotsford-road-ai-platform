import re
import phonenumbers
from email_validator import validate_email as validate_email_lib, EmailNotValidError
from typing import Tuple, Optional, Dict


def validate_phone(phone_string: str, default_country: str = "US") -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate and format phone number for any country
    
    Args:
        phone_string: Phone number string
        default_country: Default country code (e.g., "US", "GB", "IN")
    
    Returns:
        Tuple of (is_valid, formatted_phone, country_code)
    """
    try:
        # Clean the input
        cleaned = re.sub(r'[^\d+]', '', phone_string)
        
        # If it's a 7-digit number, add default area code (555 for testing)
        if len(re.sub(r'[^\d]', '', cleaned)) == 7:
            phone_string = f"555{phone_string}"
        
        # Parse phone number with default country
        parsed = phonenumbers.parse(phone_string, default_country)
        
        # For US numbers without explicit country code, be more lenient
        # Accept any parseable 10-digit number for US
        if default_country == "US" and not phone_string.startswith("+"):
            digits_only = re.sub(r'[^\d]', '', phone_string)
            if len(digits_only) == 10:
                # Format as US number even if not strictly valid
                formatted = f"+1{digits_only}"
                return True, formatted, "US"
        
        # Strict validation - must be valid for the country
        if not phonenumbers.is_valid_number(parsed):
            return False, None, None
        
        # Format to E.164 standard (+1234567890)
        formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        
        # Get country code
        country_code = phonenumbers.region_code_for_number(parsed)
        
        return True, formatted, country_code
        
    except phonenumbers.NumberParseException as e:
        # No fallback - if it can't be parsed, it's invalid
        return False, None, None


def validate_email(email_string: str, check_deliverability: bool = False) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate email address with smart whitelist + selective DNS approach
    
    Args:
        email_string: Email address string
        check_deliverability: Check if domain exists (DNS lookup) - overridden by smart logic
    
    Returns:
        Tuple of (is_valid, normalized_email, error_message)
    """
    try:
        # First do basic syntax validation without DNS
        validation = validate_email_lib(
            email_string,
            check_deliverability=False
        )
        
        # Get normalized email and domain
        normalized = validation.normalized
        domain = normalized.split('@')[1].lower()
        
        # Check if domain is whitelisted (instant approval)
        if _is_whitelisted_domain(domain):
            return True, normalized, None
        
        # All non-whitelisted domains are suspicious - do DNS check
        try:
            validation_with_dns = validate_email_lib(
                email_string,
                check_deliverability=True
            )
            return True, validation_with_dns.normalized, None
        except EmailNotValidError as e:
            return False, None, str(e)
        
        # For non-whitelisted, non-suspicious domains, use original check_deliverability setting
        if check_deliverability:
            validation_with_dns = validate_email_lib(
                email_string,
                check_deliverability=True
            )
            return True, validation_with_dns.normalized, None
        
        # Default: accept if syntax is valid
        return True, normalized, None
        
    except EmailNotValidError as e:
        return False, None, str(e)


def _is_whitelisted_domain(domain: str) -> bool:
    """
    Check if domain is in the whitelist of trusted email providers
    
    Args:
        domain: Domain to check (e.g., 'gmail.com')
    
    Returns:
        True if domain is whitelisted
    """
    # Top email providers - instant approval
    whitelisted_domains = {
        # Google
        'gmail.com', 'googlemail.com',
        
        # Microsoft
        'outlook.com', 'hotmail.com', 'live.com', 'msn.com',
        
        # Yahoo
        'yahoo.com', 'yahoo.co.uk', 'yahoo.ca', 'yahoo.com.au',
        'ymail.com', 'rocketmail.com',
        
        # Apple
        'icloud.com', 'me.com', 'mac.com',
        
        # Other major providers
        'aol.com', 'protonmail.com', 'proton.me',
        'zoho.com', 'mail.com', 'gmx.com',
        
        # Business/Enterprise
        'office365.com', 'exchange.com',
        
        # Regional providers
        'mail.ru', 'yandex.com', 'qq.com', '163.com', '126.com',
        'naver.com', 'daum.net', 'hanmail.net',
        
        # Educational
        'edu', 'ac.uk', 'edu.au', 'edu.ca'
    }
    
    # Check exact match
    if domain in whitelisted_domains:
        return True
    
    # Check if it's an educational domain
    if domain.endswith('.edu') or domain.endswith('.ac.uk') or domain.endswith('.edu.au'):
        return True
    
    return False


def _is_suspicious_domain(domain: str) -> bool:
    """
    Check if domain has suspicious patterns that require DNS verification
    
    Args:
        domain: Domain to check (e.g., 'gmail.c')
    
    Returns:
        True if domain is suspicious and needs DNS check
    """
    # Split domain into parts
    parts = domain.split('.')
    if len(parts) < 2:
        return True  # Invalid domain structure
    
    tld = parts[-1]
    base_domain = '.'.join(parts[:-1])
    
    # Suspicious pattern 1: Single character TLD
    if len(tld) == 1:
        return True
    
    # Suspicious pattern 2: Major provider typos with wrong TLD
    # Only flag providers that definitely don't use certain TLDs
    if base_domain == 'gmail' and tld not in {'com', 'co.uk', 'ca', 'com.au', 'de', 'fr', 'es', 'it', 'co.jp', 'co.in'}:
        return True
    if base_domain == 'yahoo' and tld not in {'com', 'co.uk', 'ca', 'com.au', 'de', 'fr', 'es', 'it', 'co.jp', 'co.in'}:
        return True
    if base_domain == 'hotmail' and tld not in {'com', 'co.uk', 'ca', 'com.au', 'de', 'fr', 'es', 'it', 'co.jp', 'co.in'}:
        return True
    if base_domain == 'icloud' and tld not in {'com'}:
        return True
    # Note: outlook.co actually exists, so we don't flag it
    
    # Suspicious pattern 3: Common typo patterns for major providers
    suspicious_bases = {
        'gmial', 'gmai', 'gmil', 'gmal', 'gmaill',  # Gmail typos
        'yahooo', 'yaho', 'yhoo',  # Yahoo typos
        'outlok', 'outloo', 'hotmial', 'hotmai',  # Outlook/Hotmail typos
    }
    
    if base_domain in suspicious_bases:
        return True
    
    # Suspicious pattern 4: Typo TLDs that are common mistakes
    typo_tlds = {'con', 'cmo', 'cm', 'co.', '.com', 'comm', 'comn', 'ocm', 'vom'}
    if tld in typo_tlds:
        return True
    
    # Suspicious pattern 5: Very short unknown TLD (not in common list)
    common_short_tlds = {
        'co', 'uk', 'ca', 'au', 'de', 'fr', 'it', 'es', 'nl', 'be', 'ch', 'at', 
        'se', 'no', 'dk', 'fi', 'ie', 'pl', 'cz', 'hu', 'gr', 'pt', 'ru', 'jp', 
        'kr', 'cn', 'in', 'br', 'mx', 'ar', 'cl', 'za', 'ae', 'sg', 'hk', 'my', 
        'th', 'ph', 'id', 'vn', 'nz', 'il', 'us', 'tv', 'me', 'io', 'ly', 'to'
    }
    if len(tld) == 2 and tld not in common_short_tlds:
        return True
    
    # Suspicious pattern 6: Unusual characters or patterns
    if any(char in domain for char in ['--', '..', '_']):
        return True
    
    # Suspicious pattern 7: Very long TLD (likely typo)
    if len(tld) > 6:
        return True
    
    # Suspicious pattern 8: Domains that look like typos of common providers
    if _looks_like_provider_typo(domain):
        return True
    
    return False


def _looks_like_provider_typo(domain: str) -> bool:
    """
    Check if domain looks like a typo of a major email provider
    
    Args:
        domain: Full domain to check
    
    Returns:
        True if it looks like a typo
    """
    # Known typo domains that exist but are likely user mistakes
    known_typo_domains = {
        'gmial.com', 'gmai.com', 'gmil.com', 'gmal.com', 'gmaill.com',
        'yahooo.com', 'yaho.com', 'yhoo.com', 
        'outlok.com', 'outloo.com', 'hotmial.com', 'hotmai.com'
    }
    
    domain_lower = domain.lower()
    
    # Direct match with known typo domains
    if domain_lower in known_typo_domains:
        return True
    
    # Pattern matching for provider-like domains
    provider_patterns = [
        'gmail', 'yahoo', 'outlook', 'hotmail', 'icloud', 'aol', 'protonmail'
    ]
    
    for provider in provider_patterns:
        # Check if domain contains provider name but isn't the exact provider domain
        if provider in domain_lower and not domain_lower.startswith(f'{provider}.com'):
            # Calculate similarity - if very close but not exact, it's suspicious
            base_part = domain_lower.split('.')[0]
            if _is_similar_but_not_exact(base_part, provider):
                return True
    
    # Check for icloud with wrong TLD (icloud only uses .com officially)
    if domain_lower.startswith('icloud.') and not domain_lower == 'icloud.com':
        return True
    
    return False


def _is_similar_but_not_exact(text: str, target: str) -> bool:
    """
    Check if text is similar to target but not exactly the same
    Uses simple character difference counting
    """
    if text == target:
        return False
    
    # If lengths are very different, not a typo
    if abs(len(text) - len(target)) > 2:
        return False
    
    # Count character differences
    differences = 0
    min_len = min(len(text), len(target))
    
    for i in range(min_len):
        if text[i] != target[i]:
            differences += 1
    
    # Add length difference
    differences += abs(len(text) - len(target))
    
    # If 1-2 character differences, it's likely a typo
    return 1 <= differences <= 2


def detect_email_typo(email_string: str) -> Optional[str]:
    """
    Detect common email typos and suggest corrections
    
    Args:
        email_string: Email address string
    
    Returns:
        Suggested correction or None if no typo detected
    """
    email_lower = email_string.lower().strip()
    
    # Common domain typos - map incorrect to correct
    domain_typos = {
        # Gmail variations
        "gmailcom": "gmail.com",
        "gmai.com": "gmail.com",
        "gmial.com": "gmail.com",
        "gmaill.com": "gmail.com",
        "gmil.com": "gmail.com",
        "gmal.com": "gmail.com",
        
        # Yahoo variations
        "yahoocom": "yahoo.com",
        "yahooo.com": "yahoo.com",
        "yaho.com": "yahoo.com",
        "yhoo.com": "yahoo.com",
        
        # Outlook/Hotmail variations
        "outlookcom": "outlook.com",
        "outloo.com": "outlook.com",
        "outlok.com": "outlook.com",
        "hotmailcom": "hotmail.com",
        "hotmial.com": "hotmail.com",
        "hotmai.com": "hotmail.com",
        
        # Other common providers
        "icloudcom": "icloud.com",
        "aolcom": "aol.com",
        "protonmailcom": "protonmail.com",
    }
    
    # Check if email has @ symbol
    if "@" not in email_lower:
        return None
    
    # Split into local and domain parts
    try:
        local, domain = email_lower.rsplit("@", 1)
    except ValueError:
        return None
    
    # Check for exact domain typo match
    if domain in domain_typos:
        return f"{local}@{domain_typos[domain]}"
    
    # Check for missing dot before common TLDs
    for correct_domain, _ in domain_typos.items():
        if correct_domain.endswith(".com"):
            base = correct_domain.replace(".com", "")
            # Check if domain is missing the dot (e.g., "gmailcom")
            if domain == base + "com":
                return f"{local}@{correct_domain}"
    
    # Check for wrong TLD (.co instead of .com, .cm instead of .com)
    common_domains = ["gmail", "yahoo", "hotmail", "outlook", "icloud", "aol"]
    for base_domain in common_domains:
        if domain.startswith(base_domain):
            # Check for .co, .cm, .con, etc.
            if domain in [f"{base_domain}.co", f"{base_domain}.cm", f"{base_domain}.con", f"{base_domain}.cmo"]:
                return f"{local}@{base_domain}.com"
    
    # Check for double characters (@@, ..)
    if "@@" in email_string or ".." in email_string:
        cleaned = email_string.replace("@@", "@").replace("..", ".")
        return cleaned.lower()
    
    # Check for spaces
    if " " in email_string:
        cleaned = email_string.replace(" ", "")
        return cleaned.lower()
    
    return None


def format_phone_for_display(phone: str) -> str:
    """
    Format phone number for user-friendly display
    
    Args:
        phone: E.164 formatted phone number (e.g., +17777777777)
    
    Returns:
        Formatted phone string (e.g., +1 777 777 7777)
    """
    if not phone:
        return phone
    
    # US/Canada numbers (+1)
    if phone.startswith("+1") and len(phone) == 12:
        return f"+1 {phone[2:5]} {phone[5:8]} {phone[8:]}"
    
    # UK numbers (+44)
    elif phone.startswith("+44") and len(phone) >= 12:
        return f"+44 {phone[3:7]} {phone[7:]}"
    
    # Other international numbers - just return as-is
    elif phone.startswith("+"):
        return phone
    
    # No country code - return as-is
    return phone


def extract_country_from_text(text: str) -> Optional[str]:
    """
    Extract country name or code from text and return ISO country code
    
    Returns:
        ISO country code (e.g., "GB", "US", "AU") or None
    """
    text_lower = text.lower()
    
    # Country name to ISO code mapping
    country_mapping = {
        # English-speaking countries
        "uk": "GB",
        "united kingdom": "GB",
        "england": "GB",
        "britain": "GB",
        "great britain": "GB",
        "scotland": "GB",
        "wales": "GB",
        "northern ireland": "GB",
        
        "us": "US",
        "usa": "US",
        "united states": "US",
        "america": "US",
        "united states of america": "US",
        
        "australia": "AU",
        "aus": "AU",
        "oz": "AU",
        
        "canada": "CA",
        "can": "CA",
        
        "new zealand": "NZ",
        "nz": "NZ",
        
        "ireland": "IE",
        "eire": "IE",
        
        "south africa": "ZA",
        
        # European countries
        "france": "FR",
        "germany": "DE",
        "spain": "ES",
        "italy": "IT",
        "netherlands": "NL",
        "belgium": "BE",
        "switzerland": "CH",
        "austria": "AT",
        "portugal": "PT",
        "greece": "GR",
        "poland": "PL",
        "sweden": "SE",
        "norway": "NO",
        "denmark": "DK",
        "finland": "FI",
        
        # Asian countries
        "india": "IN",
        "china": "CN",
        "japan": "JP",
        "singapore": "SG",
        "hong kong": "HK",
        "malaysia": "MY",
        "thailand": "TH",
        "philippines": "PH",
        "indonesia": "ID",
        "vietnam": "VN",
        "south korea": "KR",
        "korea": "KR",
        
        # Middle East
        "uae": "AE",
        "dubai": "AE",
        "saudi arabia": "SA",
        "israel": "IL",
        
        # Latin America
        "mexico": "MX",
        "brazil": "BR",
        "argentina": "AR",
        "chile": "CL",
        "colombia": "CO",
    }
    
    # Check for country names in text
    for country_name, country_code in country_mapping.items():
        if country_name in text_lower:
            return country_code
    
    # Check for country code patterns (+44, +61, etc.)
    country_code_match = re.search(r'\+(\d{1,3})', text)
    if country_code_match:
        code = country_code_match.group(1)
        # Map common country codes
        code_to_country = {
            "1": "US",    # US/Canada
            "44": "GB",   # UK
            "61": "AU",   # Australia
            "64": "NZ",   # New Zealand
            "353": "IE",  # Ireland
            "27": "ZA",   # South Africa
            "33": "FR",   # France
            "49": "DE",   # Germany
            "34": "ES",   # Spain
            "39": "IT",   # Italy
            "31": "NL",   # Netherlands
            "91": "IN",   # India
            "86": "CN",   # China
            "81": "JP",   # Japan
            "65": "SG",   # Singapore
            "852": "HK",  # Hong Kong
            "971": "AE",  # UAE
        }
        return code_to_country.get(code)
    
    return None


def detect_country_from_phone(phone_string: str) -> Optional[str]:
    """
    Detect country code from phone number
    
    Returns:
        ISO country code (e.g., "GB", "US") or None
    """
    try:
        # Try to parse without default country
        parsed = phonenumbers.parse(phone_string, None)
        country_code = phonenumbers.region_code_for_number(parsed)
        return country_code
    except:
        # Check for explicit country code in string
        return extract_country_from_text(phone_string)


def extract_phone_from_text(text: str) -> Optional[str]:
    """Extract phone number from text using regex patterns"""
    # First, try to extract any sequence that looks like a phone number
    # Common phone patterns - more flexible
    patterns = [
        r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',  # International
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # US format (555-123-4567)
        r'\d{3}[-.\s]\d{4}',  # Simple 7 digit (555-1234)
        r'\d{10,}',  # 10+ digits together
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    
    # If no match, try extracting all digits and see if we have enough
    digits_only = re.sub(r'[^\d]', '', text)
    if len(digits_only) >= 7:
        return digits_only
    
    return None


def extract_email_from_text(text: str) -> Optional[str]:
    """Extract email from text using regex"""
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(pattern, text)
    
    if match:
        return match.group(0)
    
    return None


def extract_and_validate_contact(text: str, country_code: str = "US") -> Dict:
    """
    Extract and validate both phone and email from text
    
    Returns:
        Dict with phone and email validation results
    """
    result = {
        "phone": {
            "found": False,
            "raw": None,
            "valid": False,
            "formatted": None,
            "country": None
        },
        "email": {
            "found": False,
            "raw": None,
            "valid": False,
            "normalized": None,
            "error": None
        }
    }
    
    # Extract phone
    phone_raw = extract_phone_from_text(text)
    if phone_raw:
        result["phone"]["found"] = True
        result["phone"]["raw"] = phone_raw
        is_valid, formatted, country = validate_phone(phone_raw, country_code)
        result["phone"]["valid"] = is_valid
        result["phone"]["formatted"] = formatted
        result["phone"]["country"] = country
    
    # Extract email
    email_raw = extract_email_from_text(text)
    if email_raw:
        result["email"]["found"] = True
        result["email"]["raw"] = email_raw
        is_valid, normalized, error = validate_email(email_raw)
        result["email"]["valid"] = is_valid
        result["email"]["normalized"] = normalized
        result["email"]["error"] = error
    
    return result


def get_smart_validation_feedback(field: str, value: str, error: Optional[str] = None) -> str:
    """
    Generate smart, helpful validation feedback based on the field and error
    
    Args:
        field: Field name (phone, email, name, etc.)
        value: The invalid value provided
        error: Optional error message from validator
    
    Returns:
        Friendly, helpful error message
    """
    if field == "phone":
        # Analyze what's wrong with the phone number
        cleaned = re.sub(r'[^\d]', '', value)
        digit_count = len(cleaned)
        
        if digit_count == 0:
            return "I didn't catch a phone number there. Could you share it? Should be 10 digits like 555-123-4567"
        elif digit_count < 7:
            return f"That looks incomplete—phone numbers are usually 10 digits. You shared {digit_count}. Mind trying again?"
        elif digit_count == 7:
            return "Almost there! That's 7 digits—need the area code too. Like 555-123-4567"
        elif digit_count > 11:
            return f"That's a bit long—got {digit_count} digits. Phone numbers are usually 10 digits. Could you double-check?"
        else:
            return "Hmm, that phone number doesn't look quite right. Could you double-check and send it again?"
    
    elif field == "email":
        # Analyze what's wrong with the email
        value_lower = value.lower()
        
        # Common typos
        if "@" not in value:
            return "That doesn't look like an email—missing the @ symbol. Should be like name@example.com"
        elif value.count("@") > 1:
            return "Looks like there are multiple @ symbols. Email should be like name@example.com"
        elif "." not in value.split("@")[-1]:
            # No dot in domain
            domain = value.split("@")[-1]
            # Check for common typos
            if "gmailcom" in domain:
                suggestion = value.replace("gmailcom", "gmail.com")
                return f"Almost there! Did you mean {suggestion}?"
            elif "yahoocom" in domain:
                suggestion = value.replace("yahoocom", "yahoo.com")
                return f"Almost there! Did you mean {suggestion}?"
            else:
                return f"That email looks incomplete—missing a dot in the domain. Should be like name@example.com"
        elif value.endswith("."):
            return "Email can't end with a dot. Should be like name@example.com"
        elif value.startswith("@"):
            return "Email can't start with @. Should be like name@example.com"
        else:
            # Generic email error
            if error and "domain" in error.lower():
                return "That email domain doesn't look right. Mind double-checking? Should be like name@example.com"
            else:
                return "That email doesn't seem valid. Mind sharing it again? Should look like name@example.com"
    
    elif field == "name":
        if len(value) < 2:
            return "Could you share your full name? Just need at least 2 characters."
        else:
            return "That name doesn't look quite right. What should I call you?"
    
    else:
        return f"Hmm, the {field} doesn't look right. Could you provide that again?"
