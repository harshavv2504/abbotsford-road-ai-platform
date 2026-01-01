from typing import Any, Dict, List, Literal, Optional, TypedDict

"""
Types (outbound)

What it does:
- Declares shared TypedDict contracts used across outbound modules for extraction, validation, and flow
  outcomes.

If you change it:
- You affect type contracts across modules. Bump versions or provide backward compatibility when removing
  keys to avoid runtime mismatches.
"""


class ExtractionResult(TypedDict, total=False):
	fields: Dict[str, Any]
	confidences: Dict[str, float]
	low_confidence: List[str]
	errors: Dict[str, str]


class ValidationResult(TypedDict, total=False):
	valid: bool
	normalized: Dict[str, Any]
	reasons: Dict[str, str]
	# Backward-compat with existing validators
	success: bool
	error: Optional[str]
	normalized_email: Optional[str]
	formatted_phone: Optional[str]
	country: Optional[str]
	typo_detected: Optional[bool]
	suggested_correction: Optional[str]


class FlowStepResult(TypedDict, total=False):
	outcome: Literal['continue', 'handoff', 'end', 'error']
	response: Optional[str]
	state_patch: Optional[Dict[str, Any]]
	metrics: Optional[Dict[str, Any]]


