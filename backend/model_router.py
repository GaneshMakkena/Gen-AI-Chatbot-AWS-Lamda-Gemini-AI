"""
Intelligent Model Router — Use the Right Model for the Right Task.

Routes simple queries (greetings, basic FAQ) to gemini-2.5-flash (fast, cheap)
and complex medical queries to gemini-2.5-pro (thorough, accurate).
"""

import os
import re
from typing import Literal

from aws_lambda_powertools import Logger

logger = Logger(service="medibot")

# Model IDs
FAST_MODEL = os.getenv("GEMINI_FAST_MODEL", "gemini-2.5-flash")
PRO_MODEL = os.getenv("GEMINI_LLM_MODEL", "gemini-2.5-pro")

# Greeting / chitchat patterns
_GREETING_PATTERNS = re.compile(
    r"^(hi|hello|hey|good\s*(morning|afternoon|evening)|"
    r"thanks|thank\s*you|bye|goodbye|ok|okay|what can you do|"
    r"who are you|help me|start)[\s!?.]*$",
    re.IGNORECASE,
)

# Complex medical keywords that warrant the Pro model
_COMPLEX_KEYWORDS = [
    "treatment plan", "differential diagnosis", "drug interaction",
    "contraindication", "chronic", "surgery", "anesthesia",
    "emergency", "overdose", "cardiac arrest", "stroke",
    "pregnancy complication", "pediatric", "cancer",
    "multiple symptoms", "blood test", "mri", "ct scan",
    "report", "analyze", "interpret", "prescription",
]

# Simple FAQ keywords — can be answered concisely
_SIMPLE_KEYWORDS = [
    "headache", "cold", "cough", "fever", "sore throat",
    "hello", "hi", "thank", "what is", "define",
]


def classify_query_complexity(query: str, has_attachments: bool = False) -> Literal["simple", "complex"]:
    """
    Classify a query as 'simple' or 'complex' to choose the right model.

    Args:
        query: The user's query text
        has_attachments: Whether the request includes file attachments

    Returns:
        "simple" or "complex"
    """
    # Attachments always require deeper analysis
    if has_attachments:
        return "complex"

    query_stripped = query.strip()

    # Very short queries or greetings → simple
    if len(query_stripped) < 15 or _GREETING_PATTERNS.match(query_stripped):
        return "simple"

    query_lower = query_stripped.lower()

    # Check for complex keywords
    if any(kw in query_lower for kw in _COMPLEX_KEYWORDS):
        return "complex"

    # Long queries with multiple sentences tend to be complex
    sentence_count = len(re.split(r'[.!?]+', query_stripped))
    word_count = len(query_stripped.split())
    if sentence_count >= 3 or word_count >= 40:
        return "complex"

    # Default to simple for everything else
    return "simple"


def get_model_for_query(query: str, has_attachments: bool = False) -> str:
    """
    Select the optimal model for a given query.

    Returns:
        Model ID string (e.g., "gemini-2.0-flash" or "gemini-2.5-pro")
    """
    complexity = classify_query_complexity(query, has_attachments)

    if complexity == "simple":
        logger.info("Model router: FAST", model=FAST_MODEL, reason="simple_query")
        return FAST_MODEL
    else:
        logger.info("Model router: PRO", model=PRO_MODEL, reason="complex_query")
        return PRO_MODEL
