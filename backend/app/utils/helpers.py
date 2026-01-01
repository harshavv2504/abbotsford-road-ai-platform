import uuid
from datetime import datetime


def generate_session_id() -> str:
    """Generate unique session ID"""
    return f"session_{int(datetime.utcnow().timestamp())}_{uuid.uuid4().hex[:8]}"


def generate_conversation_id() -> str:
    """Generate unique conversation ID"""
    return f"conv_{int(datetime.utcnow().timestamp())}_{uuid.uuid4().hex[:8]}"


def generate_lead_id() -> str:
    """Generate unique lead ID"""
    return f"lead_{int(datetime.utcnow().timestamp())}_{uuid.uuid4().hex[:8]}"


def mask_email(email: str) -> str:
    """Mask an email for logs (keep domain)."""
    try:
        local, domain = email.split("@", 1)
    except Exception:
        return "***"
    if len(local) <= 2:
        masked_local = "*" * len(local)
    else:
        masked_local = local[0] + ("*" * (len(local) - 2)) + local[-1]
    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    """Mask a phone for logs, keep last 2-4 digits."""
    digits = [c for c in phone if c.isdigit()]
    n = len(digits)
    if n == 0:
        return "***"
    show = 2 if n <= 6 else 4
    masked_digits = ("*" * (n - show)) + "".join(digits[-show:])
    # Re-add plus if present
    prefix = "+" if phone.strip().startswith("+") else ""
    return f"{prefix}{masked_digits}"