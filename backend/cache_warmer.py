"""
Cache Warmer — Pre-generate responses for common medical queries.

Run this script to populate the response cache with commonly asked medical questions.
Can be triggered via CLI or the /admin/warm-cache endpoint.
"""

import os
import sys
import time

# Add parent directory to path when running as script
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aws_lambda_powertools import Logger

logger = Logger(service="medibot")

# Top medical queries based on common first-aid scenarios
COMMON_QUERIES = [
    "How to perform CPR on an adult?",
    "How to treat a burn at home?",
    "What to do if someone is choking?",
    "How to stop a nosebleed?",
    "How to treat a sprained ankle?",
    "First aid for a bee sting",
    "How to treat a minor cut or wound?",
    "What to do for a fever?",
    "How to treat sunburn?",
    "First aid for heat stroke",
    "How to help someone who fainted?",
    "What to do for food poisoning?",
    "How to treat an allergic reaction?",
    "First aid for a fracture",
    "How to treat a headache naturally?",
]


def warm_cache(queries: list = None, skip_existing: bool = True) -> dict:
    """
    Pre-generate and cache responses for common queries.

    Args:
        queries: List of queries to warm (defaults to COMMON_QUERIES)
        skip_existing: If True, skip queries already in cache

    Returns:
        dict with 'warmed', 'skipped', 'failed' counts
    """
    from response_cache import get_cached_response, cache_response
    from gemini_client import invoke_llm, detect_medical_topic

    queries = queries or COMMON_QUERIES
    results = {"warmed": 0, "skipped": 0, "failed": 0, "total": len(queries)}

    for i, query in enumerate(queries, 1):
        logger.info(f"Warming [{i}/{len(queries)}]: {query[:50]}")

        # Check if already cached
        if skip_existing:
            existing = get_cached_response(query)
            if existing:
                logger.info("Already cached, skipping", query=query[:40])
                results["skipped"] += 1
                continue

        try:
            # Generate response
            response = invoke_llm(query, max_tokens=1536, temperature=0.5)
            if response:
                topic = detect_medical_topic(query)
                cache_response(query, response, topic=topic or "", ttl_hours=48)
                results["warmed"] += 1
                logger.info("Warmed successfully", query=query[:40])
            else:
                results["failed"] += 1
                logger.warning("LLM returned None", query=query[:40])
        except Exception as e:
            results["failed"] += 1
            logger.error("Warming failed", query=query[:40], error=str(e))

        # Small delay to avoid rate limiting
        time.sleep(1)

    logger.info("Cache warming complete", **results)
    return results


if __name__ == "__main__":
    print("🔥 MediBot Cache Warmer")
    print(f"   Warming {len(COMMON_QUERIES)} common queries...\n")
    results = warm_cache()
    print(f"\n✅ Done: {results['warmed']} warmed, {results['skipped']} skipped, {results['failed']} failed")
