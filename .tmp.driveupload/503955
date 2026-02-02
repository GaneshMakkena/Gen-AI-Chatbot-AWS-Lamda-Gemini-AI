"""
Guest Tracking Module for MediBot
Server-side guest session management to prevent trial abuse.

Tracks guest usage by IP/fingerprint and enforces message limits.
"""

import os
import time
import hashlib
import boto3
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

# Environment variables
GUEST_TABLE = os.getenv("GUEST_TABLE", "medibot-guest-sessions")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
GUEST_MESSAGE_LIMIT = int(os.getenv("GUEST_MESSAGE_LIMIT", "3"))
GUEST_SESSION_TTL_HOURS = int(os.getenv("GUEST_SESSION_TTL_HOURS", "24"))

# DynamoDB client (lazy init)
_dynamodb = None


def get_dynamodb():
    """Get or create DynamoDB resource."""
    global _dynamodb
    if _dynamodb is None:
        _dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    return _dynamodb


def get_table():
    """Get DynamoDB table."""
    return get_dynamodb().Table(GUEST_TABLE)


def generate_guest_id(ip_address: str, user_agent: str = "", fingerprint: str = "") -> str:
    """
    Generate a consistent guest ID from identifying information.

    Uses a hash of IP + user agent + fingerprint to create a stable identifier
    that persists across sessions from the same device/browser.
    """
    # Combine identifiers
    identifier = f"{ip_address}:{user_agent}:{fingerprint}"

    # Create SHA256 hash (first 16 chars for readability)
    hash_bytes = hashlib.sha256(identifier.encode()).hexdigest()[:16]

    return f"guest_{hash_bytes}"


def get_guest_session(guest_id: str) -> Optional[Dict[str, Any]]:
    """
    Get existing guest session from DynamoDB.

    Returns None if session doesn't exist or has expired.
    """
    try:
        table = get_table()
        response = table.get_item(Key={"guest_id": guest_id})

        item = response.get("Item")
        if not item:
            return None

        # Check if session has expired (TTL might not have cleaned it up yet)
        ttl = item.get("ttl", 0)
        if ttl and ttl < int(time.time()):
            return None

        return item
    except Exception as e:
        print(f"Error getting guest session: {e}")
        return None


def create_guest_session(
    guest_id: str,
    ip_address: str,
    user_agent: str = "",
    fingerprint: str = ""
) -> Dict[str, Any]:
    """
    Create a new guest session with zero messages.
    """
    now = datetime.utcnow()
    ttl = int((now + timedelta(hours=GUEST_SESSION_TTL_HOURS)).timestamp())

    session = {
        "guest_id": guest_id,
        "ip_address": ip_address,
        "user_agent": user_agent[:500] if user_agent else "",  # Limit UA length
        "fingerprint": fingerprint,
        "message_count": 0,
        "messages": [],
        "created_at": now.isoformat(),
        "last_activity": now.isoformat(),
        "ttl": ttl
    }

    try:
        table = get_table()
        table.put_item(Item=session)
        print(f"Created guest session: {guest_id}")
        return session
    except Exception as e:
        print(f"Error creating guest session: {e}")
        return session


def get_or_create_session(
    ip_address: str,
    user_agent: str = "",
    fingerprint: str = ""
) -> Dict[str, Any]:
    """
    Get existing session or create a new one.
    """
    guest_id = generate_guest_id(ip_address, user_agent, fingerprint)

    session = get_guest_session(guest_id)
    if session:
        return session

    return create_guest_session(guest_id, ip_address, user_agent, fingerprint)


def check_guest_limit(
    ip_address: str,
    user_agent: str = "",
    fingerprint: str = ""
) -> Dict[str, Any]:
    """
    Check if guest has exceeded their message limit.

    Returns:
        {
            "allowed": bool,
            "remaining": int,
            "message_count": int,
            "limit": int,
            "guest_id": str
        }
    """
    session = get_or_create_session(ip_address, user_agent, fingerprint)

    message_count = session.get("message_count", 0)
    remaining = max(0, GUEST_MESSAGE_LIMIT - message_count)
    allowed = message_count < GUEST_MESSAGE_LIMIT

    return {
        "allowed": allowed,
        "remaining": remaining,
        "message_count": message_count,
        "limit": GUEST_MESSAGE_LIMIT,
        "guest_id": session["guest_id"]
    }


def increment_guest_message(
    ip_address: str,
    user_agent: str = "",
    fingerprint: str = "",
    query: str = ""
) -> Dict[str, Any]:
    """
    Increment guest message count and record the message.

    Returns updated limit status.
    """
    guest_id = generate_guest_id(ip_address, user_agent, fingerprint)
    now = datetime.utcnow()

    # Ensure session exists
    get_or_create_session(ip_address, user_agent, fingerprint)

    try:
        table = get_table()

        # Atomically increment counter and add message
        response = table.update_item(
            Key={"guest_id": guest_id},
            UpdateExpression="""
                SET message_count = if_not_exists(message_count, :zero) + :inc,
                    last_activity = :now,
                    messages = list_append(if_not_exists(messages, :empty), :msg)
            """,
            ExpressionAttributeValues={
                ":inc": 1,
                ":zero": 0,
                ":now": now.isoformat(),
                ":empty": [],
                ":msg": [{
                    "query": query[:200] if query else "",  # Limit stored query length
                    "timestamp": now.isoformat()
                }]
            },
            ReturnValues="ALL_NEW"
        )

        new_count = response["Attributes"].get("message_count", 0)
        remaining = max(0, GUEST_MESSAGE_LIMIT - new_count)

        print(f"Guest {guest_id} message #{new_count} (remaining: {remaining})")

        return {
            "allowed": new_count <= GUEST_MESSAGE_LIMIT,
            "remaining": remaining,
            "message_count": new_count,
            "limit": GUEST_MESSAGE_LIMIT,
            "guest_id": guest_id
        }
    except Exception as e:
        print(f"Error incrementing guest message: {e}")
        return {
            "allowed": True,  # Fail open on error
            "remaining": 0,
            "message_count": 0,
            "limit": GUEST_MESSAGE_LIMIT,
            "guest_id": guest_id,
            "error": str(e)
        }


def reset_guest_session(guest_id: str) -> bool:
    """
    Reset a guest session (admin function).
    """
    try:
        table = get_table()
        table.delete_item(Key={"guest_id": guest_id})
        print(f"Reset guest session: {guest_id}")
        return True
    except Exception as e:
        print(f"Error resetting guest session: {e}")
        return False


def get_guest_stats() -> Dict[str, Any]:
    """
    Get aggregate guest usage statistics (admin function).
    """
    try:
        table = get_table()
        response = table.scan(
            Select='COUNT'
        )

        return {
            "total_sessions": response.get("Count", 0),
            "scanned_count": response.get("ScannedCount", 0)
        }
    except Exception as e:
        print(f"Error getting guest stats: {e}")
        return {"error": str(e)}
