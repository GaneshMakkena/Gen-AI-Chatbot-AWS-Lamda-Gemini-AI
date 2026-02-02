"""
Password History module for MediBot.
Stores password hashes to prevent reuse on password reset.

SECURITY: Uses Argon2id for password hashing (resistant to rainbow tables and GPU attacks).
"""

import os
import secrets
import hashlib
import boto3
from typing import List, Dict, Any
from datetime import datetime

# Imports for password hashing
# Try to import argon2, fall back to bcrypt, then SHA-256
bcrypt = None
try:
    import bcrypt as _bcrypt
    bcrypt = _bcrypt
except ImportError:
    bcrypt = None

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError
    HASH_METHOD = "argon2"
    ph = PasswordHasher(
        time_cost=3,      # Number of iterations
        memory_cost=65536,  # 64MB memory
        parallelism=4,    # Number of threads
        hash_len=32,
        salt_len=16
    )
except ImportError:
    if bcrypt:
        HASH_METHOD = "bcrypt"
        ph = None
    else:
        HASH_METHOD = "sha256_strong"
        ph = None

print(f"Password hashing using: {HASH_METHOD}")

# DynamoDB configuration
HEALTH_PROFILE_TABLE = os.getenv("HEALTH_PROFILE_TABLE", "medibot-health-profiles-production")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# How many previous passwords to prevent reuse
PASSWORD_HISTORY_COUNT = 3

# DynamoDB client (initialized lazily)
_dynamodb = None


def get_dynamodb():
    """Get or create DynamoDB resource."""
    global _dynamodb
    if _dynamodb is None:
        _dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    return _dynamodb


def get_table():
    """Get DynamoDB table."""
    return get_dynamodb().Table(HEALTH_PROFILE_TABLE)


def _hash_password(password: str) -> str:
    """
    Hash a password using Argon2id (preferred), bcrypt (fallback), or SHA-256 with strong salt.

    Returns a hash string that includes algorithm identifier for future compatibility.
    """
    if HASH_METHOD == "argon2":
        # Argon2id - most secure, recommended by OWASP
        # The hash includes salt, parameters, and version info
        return ph.hash(password)

    elif HASH_METHOD == "bcrypt":
        # bcrypt - industry standard
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    # Fallback to SHA-256 (Not recommended but better than plain text)
    else:
        salt = secrets.token_hex(16)  # 64-char random salt
        hash_value = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt.encode(),
            iterations=100000  # NIST recommended minimum
        ).hex()
        return f"pbkdf2_sha256${salt}${hash_value}"


def _normalize_identifier(identifier: str) -> str:
    return identifier.strip().lower()


def _hashed_identifier(identifier: str) -> str:
    normalized = _normalize_identifier(identifier)
    return hashlib.sha256(normalized.encode()).hexdigest()


def _history_key(identifier: str) -> str:
    if "@" in identifier:
        return f"pwd_history_email_{_hashed_identifier(identifier)}"
    return f"pwd_history_{identifier}"


def _legacy_history_key(identifier: str) -> str:
    return f"pwd_history_{identifier}"


def _verify_password(password: str, stored_hash: str) -> bool:
    """
    Verify a password against a stored hash.

    Handles multiple hash formats for backward compatibility.
    """
    try:
        if stored_hash.startswith("$argon2"):
            # Argon2 format
            if not ph:
                return False
            try:
                ph.verify(stored_hash, password)
                return True
            except VerifyMismatchError:
                return False

        # Fallback to bcrypt
        # Check if bcrypt is available and the hash format matches
        if bcrypt and (stored_hash.startswith('$2b$') or stored_hash.startswith('$2a$')):
            return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))

        # Fallback to PBKDF2 SHA-256 (our custom format)
        if stored_hash.startswith("pbkdf2_sha256$"):
            parts = stored_hash.split("$")
            if len(parts) != 3:
                return False
            salt = parts[1]
            stored_value = parts[2]
            computed = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode(),
                salt.encode(),
                iterations=100000
            ).hex()
            return secrets.compare_digest(computed, stored_value)

        else:
            # Legacy SHA-256 with fixed salt (backward compatibility)
            legacy_salt = "medibot_pwd_salt_2024"
            legacy_hash = hashlib.sha256(f"{legacy_salt}{password}".encode()).hexdigest()
            return secrets.compare_digest(legacy_hash, stored_hash)

    except Exception as e:
        print(f"Password verification error: {e}")
        return False


def store_password_hash(user_id: str, password: str) -> bool:
    """
    Store a password hash in the user's history.
    Keeps only the last PASSWORD_HISTORY_COUNT hashes.
    """
    try:
        table = get_table()
        password_hash = _hash_password(password)

        # Get existing history (hashed email key if applicable)
        history_key = _history_key(user_id)
        response = table.get_item(
            Key={"user_id": history_key}
        )

        existing = response.get("Item", {})
        history: List[Dict[str, str]] = existing.get("password_hashes", [])

        # Backward compatibility: migrate legacy email-based key if present
        if not history and "@" in user_id:
            legacy_key = _legacy_history_key(user_id)
            legacy = table.get_item(Key={"user_id": legacy_key}).get("Item", {})
            history = legacy.get("password_hashes", [])

        # Add new hash with algorithm info
        history.append({
            "hash": password_hash,
            "algorithm": HASH_METHOD,
            "created_at": datetime.utcnow().isoformat()
        })

        # Keep only last N
        history = history[-PASSWORD_HISTORY_COUNT:]

        # Store back
        table.put_item(Item={
            "user_id": history_key,
            "password_hashes": history,
            "updated_at": datetime.utcnow().isoformat()
        })

        print(f"Stored password hash ({HASH_METHOD}) for user {user_id[:8]}... (history count: {len(history)})")
        return True
    except Exception as e:
        print(f"Error storing password hash: {e}")
        return False


def is_password_previously_used(user_id: str, password: str) -> bool:
    """
    Check if a password was previously used by this user.
    Returns True if the password was used before.
    """
    try:
        table = get_table()

        history_key = _history_key(user_id)
        response = table.get_item(
            Key={"user_id": history_key}
        )

        existing = response.get("Item", {})
        history: List[Dict[str, str]] = existing.get("password_hashes", [])

        # Backward compatibility for legacy email keys
        if not history and "@" in user_id:
            legacy_key = _legacy_history_key(user_id)
            legacy = table.get_item(Key={"user_id": legacy_key}).get("Item", {})
            history = legacy.get("password_hashes", [])

        # Check if this password matches any stored hash
        for entry in history:
            stored_hash = entry.get("hash", "")
            if _verify_password(password, stored_hash):
                print(f"Password was previously used for user {user_id[:8]}...")
                return True

        return False
    except Exception as e:
        print(f"Error checking password history: {e}")
        # On error, allow the password (fail open to not block user)
        return False


def get_password_history_count(user_id: str) -> int:
    """Get the number of stored password hashes for a user."""
    try:
        table = get_table()
        history_key = _history_key(user_id)
        response = table.get_item(
            Key={"user_id": history_key}
        )
        existing = response.get("Item", {})
        history = existing.get("password_hashes", [])

        if not history and "@" in user_id:
            legacy_key = _legacy_history_key(user_id)
            legacy = table.get_item(Key={"user_id": legacy_key}).get("Item", {})
            history = legacy.get("password_hashes", [])

        return len(history)
    except Exception as e:
        print(f"Error getting password history count: {e}")
        return 0
