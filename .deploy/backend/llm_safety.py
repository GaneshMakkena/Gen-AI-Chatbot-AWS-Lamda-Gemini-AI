"""
LLM Safety Module for MediBot
Implements prompt injection detection, output validation, and content safety checks.

Key Features:
- Prompt injection pattern detection
- Medical misinformation risk checks
- Output sanitization
- Fallback response generation
"""

import re
from typing import Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum


# ============================================
# Safety Configuration
# ============================================

class SafetyLevel(Enum):
    """Safety check severity levels."""
    SAFE = "safe"
    WARNING = "warning"
    BLOCKED = "blocked"


@dataclass
class SafetyCheckResult:
    """Result of a safety check."""
    level: SafetyLevel
    passed: bool
    issues: List[str]
    sanitized_input: Optional[str] = None
    fallback_response: Optional[str] = None


# ============================================
# Prompt Injection Detection
# ============================================

# Known prompt injection patterns
INJECTION_PATTERNS = [
    # System prompt overrides
    r"ignore\s+(previous|all|above)\s+(instructions?|prompts?|rules?)",
    r"disregard\s+(your|the)\s+(instructions?|prompts?|guidelines?)",
    r"forget\s+(everything|your|previous)\s+(instructions?|training)?",
    r"override\s+(your|the)\s+(system|instructions?)",
    r"new\s+(instructions?|rules?)\s*:",

    # Role manipulation
    r"you\s+are\s+now\s+a?\s*(different|new|evil|unrestricted)",
    r"pretend\s+you\s+are\s+(?!a\s+doctor|a\s+nurse|a\s+medical)",
    r"act\s+as\s+(?!a\s+medical|a\s+health|a\s+doctor)",
    r"roleplay\s+as\s+(?!a\s+medical|a\s+healthcare)",
    r"switch\s+to\s+(dan|developer|unrestricted)\s+mode",

    # Data extraction attempts
    r"reveal\s+(your|the)\s+(system|hidden|secret)\s+(prompt|instructions?)",
    r"show\s+(me\s+)?(your|the)\s+(system|hidden)\s+(prompt|config)",
    r"what\s+is\s+(your|the)\s+(system|initial)\s+(prompt|instructions?)",
    r"print\s+(your|the)\s+(system|hidden)\s+(prompt|config)",
    r"output\s+(your|the)\s+(system|internal)\s+(prompt|state)",

    # Jailbreak attempts
    r"(dai|dan|dev|developer)\s*mode",
    r"bypass\s+(your|the|any)\s+(restrictions?|filters?|safety)",
    r"disable\s+(your|the)\s+(safety|content|moderation)",
    r"remove\s+(all\s+)?(restrictions?|filters?|limits?)",

    # Markdown/format injection
    r"\[system\]",
    r"\[assistant\]",
    r"<\|.*?\|>",
    r"```system",
    r"<system>",
]

# Compile patterns for efficiency
COMPILED_INJECTION_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in INJECTION_PATTERNS
]


def detect_prompt_injection(text: str) -> SafetyCheckResult:
    """
    Detect potential prompt injection attempts in user input.

    Returns:
        SafetyCheckResult with detection details
    """
    issues = []

    for pattern in COMPILED_INJECTION_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            issues.append(f"Pattern detected: {pattern.pattern[:50]}...")

    # Check for excessive special characters/delimiters
    if text.count('```') > 4:
        issues.append("Excessive code block delimiters")

    if text.count('[') > 10 or text.count(']') > 10:
        issues.append("Excessive bracket usage")

    # Check for suspiciously long inputs
    if len(text) > 10000:
        issues.append("Input exceeds maximum length")

    # Determine safety level
    if len(issues) >= 2:
        return SafetyCheckResult(
            level=SafetyLevel.BLOCKED,
            passed=False,
            issues=issues,
            fallback_response="I'm sorry, but I can't process that request. Please rephrase your medical question."
        )
    elif len(issues) == 1:
        return SafetyCheckResult(
            level=SafetyLevel.WARNING,
            passed=True,
            issues=issues
        )
    else:
        return SafetyCheckResult(
            level=SafetyLevel.SAFE,
            passed=True,
            issues=[]
        )


# ============================================
# Output Validation
# ============================================

# Dangerous medical advice patterns
DANGEROUS_ADVICE_PATTERNS = [
    # Overdose/harm suggestions
    r"take\s+extra\s+doses?",
    r"double\s+your\s+(dose|dosage|medication)",
    r"increase\s+dosage\s+significantly",
    r"stop\s+taking\s+(all\s+)?your\s+medications?\s+(immediately|at\s+once)",
    r"stop\s+your\s+(insulin|heart\s+medication|blood\s+thinner)",

    # Dangerous substance recommendations
    r"drink\s+(bleach|hydrogen\s+peroxide|chlorine)",
    r"inject\s+(bleach|disinfectant)",
    r"consume\s+(cleaning\s+products?|poison)",

    # Avoiding medical care
    r"don't\s+(need\s+to\s+)?see\s+a\s+doctor",
    r"avoid\s+(hospitals?|doctors?|medical\s+care)",
    r"(cancer|tumor|diabetes|heart\s+disease)\s+can\s+be\s+cured\s+(with|by)\s+(diet|herbs?|supplements?)",

    # False cure claims
    r"(cure|heal)\s+(cancer|aids|hiv|diabetes)\s+(naturally|with\s+herbs?)",
    r"guaranteed\s+to\s+(cure|heal|treat)",
    r"100%\s+(cure|healing|treatment)\s+rate",
]

COMPILED_DANGEROUS_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in DANGEROUS_ADVICE_PATTERNS
]


def validate_output(response: str) -> SafetyCheckResult:
    """
    Validate LLM output for dangerous or inappropriate content.

    Returns:
        SafetyCheckResult with validation details
    """
    issues = []

    # Check for dangerous advice patterns
    for pattern in COMPILED_DANGEROUS_PATTERNS:
        if pattern.search(response):
            issues.append(f"Dangerous advice pattern: {pattern.pattern[:40]}...")

    # Check for missing disclaimer indicators
    disclaimer_phrases = [
        "consult a doctor",
        "seek medical attention",
        "healthcare provider",
        "professional medical advice",
        "see a healthcare",
        "medical professional"
    ]

    has_disclaimer = any(
        phrase.lower() in response.lower()
        for phrase in disclaimer_phrases
    )

    # For longer responses, check if disclaimer is present
    if len(response) > 500 and not has_disclaimer:
        issues.append("Missing medical disclaimer")

    # Determine safety level
    if len(issues) >= 1 and any("Dangerous" in i for i in issues):
        return SafetyCheckResult(
            level=SafetyLevel.BLOCKED,
            passed=False,
            issues=issues,
            fallback_response=get_fallback_response("safety")
        )
    elif len(issues) > 0:
        return SafetyCheckResult(
            level=SafetyLevel.WARNING,
            passed=True,
            issues=issues
        )
    else:
        return SafetyCheckResult(
            level=SafetyLevel.SAFE,
            passed=True,
            issues=[]
        )


# ============================================
# Content Sanitization
# ============================================

def sanitize_input(text: str) -> str:
    """
    Sanitize user input to reduce injection risk.
    Removes or escapes potentially dangerous patterns.
    """
    sanitized = text

    # Remove system-like markers
    sanitized = re.sub(r'\[system\]', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'\[assistant\]', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'<system>', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'</system>', '', sanitized, flags=re.IGNORECASE)

    # Limit excessive code blocks
    sanitized = re.sub(r'```{3,}', '```', sanitized)

    # Trim excessive length
    if len(sanitized) > 8000:
        sanitized = sanitized[:8000] + "..."

    return sanitized.strip()


def sanitize_output(response: str) -> str:
    """
    Sanitize LLM output before returning to user.
    """
    sanitized = response

    # Remove any leaked system prompts
    sanitized = re.sub(r'<\|.*?\|>', '', sanitized)
    sanitized = re.sub(r'\[SYSTEM\].*?\[/SYSTEM\]', '', sanitized, flags=re.DOTALL)

    return sanitized.strip()


# ============================================
# Fallback Responses
# ============================================

FALLBACK_RESPONSES = {
    "safety": """
I apologize, but I'm unable to provide a response to that query.

For your safety, please consult a qualified healthcare professional for medical advice.

**If this is an emergency, please call emergency services immediately.**
""".strip(),

    "injection": """
I'm sorry, but I detected something unusual in your request.

Could you please rephrase your medical question? I'm here to help with health-related queries.
""".strip(),

    "error": """
I apologize, but I encountered an issue processing your request.

Please try again, or rephrase your question. If the problem persists, the system may be experiencing temporary issues.

**For urgent medical concerns, please contact a healthcare provider directly.**
""".strip(),

    "ambiguous": """
I'd like to help, but I need more information to provide useful guidance.

Could you please provide more details about:
- What symptoms you're experiencing
- When this started
- Any relevant medical history

**Note: This is for informational purposes only. Always consult a healthcare professional for medical advice.**
""".strip(),
}


def get_fallback_response(reason: str = "error") -> str:
    """Get an appropriate fallback response."""
    return FALLBACK_RESPONSES.get(reason, FALLBACK_RESPONSES["error"])


# ============================================
# Combined Safety Check
# ============================================

def check_input_safety(user_input: str) -> Tuple[bool, str, Optional[str]]:
    """
    Perform comprehensive input safety check.

    Returns:
        Tuple of (is_safe, sanitized_input, fallback_response_if_blocked)
    """
    # Sanitize first
    sanitized = sanitize_input(user_input)

    # Check for injection
    injection_result = detect_prompt_injection(sanitized)

    if injection_result.level == SafetyLevel.BLOCKED:
        return False, sanitized, injection_result.fallback_response

    return True, sanitized, None


def check_output_safety(llm_response: str) -> Tuple[bool, str, Optional[str]]:
    """
    Perform comprehensive output safety check.

    Returns:
        Tuple of (is_safe, sanitized_output, fallback_response_if_blocked)
    """
    # Validate output
    validation_result = validate_output(llm_response)

    if validation_result.level == SafetyLevel.BLOCKED:
        return False, "", validation_result.fallback_response

    # Sanitize output
    sanitized = sanitize_output(llm_response)

    return True, sanitized, None


# ============================================
# Medical Context Validation
# ============================================

def is_medical_query(query: str) -> bool:
    """
    Check if a query is related to medical/health topics.
    Used to ensure responses stay on-topic.
    """
    medical_keywords = [
        "symptom", "pain", "treatment", "medication", "medicine",
        "doctor", "hospital", "health", "disease", "condition",
        "injury", "wound", "fever", "headache", "cough", "cold",
        "infection", "diagnosis", "therapy", "surgery", "prescription",
        "vitamin", "diet", "exercise", "sleep", "mental", "anxiety",
        "depression", "blood", "heart", "lung", "kidney", "liver",
        "cancer", "diabetes", "allergy", "vaccine", "immunization"
    ]

    query_lower = query.lower()
    return any(keyword in query_lower for keyword in medical_keywords)
