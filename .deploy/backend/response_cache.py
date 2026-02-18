"""
Response Cache — DynamoDB-backed cache to avoid re-generating known responses.

Caches LLM responses keyed by normalized query hash.
TTL ensures stale entries are auto-cleaned by DynamoDB.
"""

import os
import re
import time
import hashlib
from typing import Optional, Dict, Any

from aws_clients import get_dynamodb_table
from aws_lambda_powertools import Logger

logger = Logger(service="medibot")

CACHE_TABLE_NAME = os.getenv("RESPONSE_CACHE_TABLE", "medibot-response-cache-production")
CACHE_TTL_HOURS = int(os.getenv("CACHE_TTL_HOURS", "24"))


def normalize_query(query: str) -> str:
    """
    Normalize a query for cache key generation.
    Lowercase, strip whitespace, remove extra punctuation.
    """
    text = query.lower().strip()
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    # Remove trailing punctuation (but keep internal)
    text = text.rstrip("?!.,;:")
    return text


def get_cache_key(query: str) -> str:
    """Generate SHA-256 hash cache key from a normalized query."""
    normalized = normalize_query(query)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def get_cached_response(query: str) -> Optional[Dict[str, Any]]:
    """
    Look up a cached response for the given query.

    Returns:
        Dict with 'response', 'topic', 'timestamp' if cache hit, else None.
    """
    try:
        cache_key = get_cache_key(query)
        table = get_dynamodb_table(CACHE_TABLE_NAME)

        result = table.get_item(Key={"cache_key": cache_key})
        item = result.get("Item")

        if not item:
            logger.info("Cache MISS", cache_key=cache_key[:12])
            return None

        # Check if TTL has logically expired (DynamoDB TTL cleanup is async)
        if item.get("ttl", 0) < int(time.time()):
            logger.info("Cache EXPIRED", cache_key=cache_key[:12])
            return None

        logger.info("Cache HIT", cache_key=cache_key[:12])
        return {
            "response": item["response"],
            "topic": item.get("topic", ""),
            "timestamp": item.get("timestamp", 0),
        }

    except Exception as e:
        logger.warning("Cache lookup failed (non-fatal)", error=str(e))
        return None


def cache_response(
    query: str,
    response: str,
    topic: str = "",
    ttl_hours: Optional[int] = None,
) -> None:
    """
    Store an LLM response in the cache.

    Args:
        query: Original user query
        response: LLM response text
        topic: Detected medical topic
        ttl_hours: Cache TTL in hours (defaults to CACHE_TTL_HOURS env var)
    """
    try:
        cache_key = get_cache_key(query)
        ttl = int(time.time()) + (ttl_hours or CACHE_TTL_HOURS) * 3600

        table = get_dynamodb_table(CACHE_TABLE_NAME)
        table.put_item(
            Item={
                "cache_key": cache_key,
                "query_normalized": normalize_query(query),
                "response": response,
                "topic": topic or "",
                "timestamp": int(time.time()),
                "ttl": ttl,
            }
        )
        logger.info("Cached response", cache_key=cache_key[:12], ttl_hours=ttl_hours or CACHE_TTL_HOURS)

    except Exception as e:
        logger.warning("Cache write failed (non-fatal)", error=str(e))
