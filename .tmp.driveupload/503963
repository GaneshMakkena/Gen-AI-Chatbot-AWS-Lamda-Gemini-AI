"""
Authentication module for MediBot - AWS Cognito integration.
Provides JWT token verification with cryptographic signature validation.

SECURITY: Uses python-jose to verify JWT signatures against Cognito JWKS.
"""

import os
import json
import time
import urllib.request
from typing import Optional, Dict, Any

# JWT verification library
from jose import jwt, JWTError

# Cognito configuration from environment
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID", "")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID", "")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# JWKS URL for Cognito
JWKS_URL = f"https://cognito-idp.{AWS_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json"
COGNITO_ISSUER = f"https://cognito-idp.{AWS_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"

# Cache for JWKS keys
_jwks_cache: Dict = {}
_jwks_cache_time: float = 0
JWKS_CACHE_TTL = 3600  # 1 hour


def get_jwks() -> Dict:
    """
    Fetch and cache JWKS from Cognito.
    Caches for 1 hour to reduce API calls while allowing key rotation.
    """
    global _jwks_cache, _jwks_cache_time

    # Check cache
    if _jwks_cache and (time.time() - _jwks_cache_time) < JWKS_CACHE_TTL:
        return _jwks_cache

    try:
        with urllib.request.urlopen(JWKS_URL, timeout=5) as response:
            _jwks_cache = json.loads(response.read().decode())
            _jwks_cache_time = time.time()
            return _jwks_cache
    except Exception as e:
        print(f"Error fetching JWKS: {e}")
        # Return cached version if available, even if expired
        if _jwks_cache:
            return _jwks_cache
        return {"keys": []}


def get_signing_key(token: str) -> Optional[Dict]:
    """
    Get the signing key from JWKS for the given token.

    Args:
        token: JWT token to find the signing key for

    Returns:
        JWK dict for the signing key, or None if not found
    """
    try:
        # Get the key ID from the token header
        headers = jwt.get_unverified_header(token)
        kid = headers.get("kid")

        if not kid:
            print("Token missing kid header")
            return None

        # Find the matching key in JWKS
        jwks = get_jwks()
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return key

        print(f"Key {kid} not found in JWKS")
        return None

    except Exception as e:
        print(f"Error getting signing key: {e}")
        return None


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify a Cognito JWT token with CRYPTOGRAPHIC SIGNATURE validation.

    This function:
    1. Fetches the public key from Cognito JWKS
    2. Verifies the token signature using RSA
    3. Validates expiration, issuer, and audience claims

    Args:
        token: JWT token from Authorization header

    Returns:
        User claims dict if valid, None if invalid
    """
    if not token:
        return None

    # Remove "Bearer " prefix if present
    if token.startswith("Bearer "):
        token = token[7:]

    try:
        # Get the signing key from JWKS
        signing_key = get_signing_key(token)
        if not signing_key:
            return None

        # Decode and verify the token with signature validation
        # python-jose handles signature verification automatically
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            issuer=COGNITO_ISSUER,
            options={
                "verify_aud": False,  # We'll check aud/client_id manually
                "verify_exp": True,
                "verify_iss": True,
            }
        )

        # Verify audience/client_id based on token type
        token_use = payload.get("token_use", "")
        if token_use == "id":
            if payload.get("aud") != COGNITO_CLIENT_ID:
                print("Invalid audience for id token")
                return None
        elif token_use == "access":
            if payload.get("client_id") != COGNITO_CLIENT_ID:
                print("Invalid client_id for access token")
                return None

        return payload

    except jwt.ExpiredSignatureError:
        print("Token expired")
        return None
    except jwt.JWTClaimsError as e:
        print(f"Token claims error: {e}")
        return None
    except JWTError as e:
        print(f"JWT verification error: {e}")
        return None
    except Exception as e:
        print(f"Token verification error: {e}")
        return None


def get_user_id(token: str) -> Optional[str]:
    """Extract user ID (sub) from token."""
    claims = verify_token(token)
    if claims:
        return claims.get("sub")
    return None


def get_user_email(token: str) -> Optional[str]:
    """Extract user email from token."""
    claims = verify_token(token)
    if claims:
        return claims.get("email")
    return None


def get_user_info(token: str) -> Optional[Dict[str, str]]:
    """Get user info from token."""
    claims = verify_token(token)
    if claims:
        return {
            "user_id": claims.get("sub", ""),
            "email": claims.get("email", ""),
            "name": claims.get("name", claims.get("email", "").split("@")[0]),
        }
    return None


# FastAPI dependency for auth
def get_optional_user(authorization: Optional[str] = None) -> Optional[Dict[str, str]]:
    """
    FastAPI dependency that extracts user info if authenticated.
    Returns None if not authenticated (allows anonymous access).
    """
    if not authorization:
        return None
    return get_user_info(authorization)


def require_auth(authorization: Optional[str] = None) -> Dict[str, str]:
    """
    FastAPI dependency that requires authentication.
    Raises HTTPException if not authenticated.
    """
    from fastapi import HTTPException

    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")

    user = get_user_info(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return user
