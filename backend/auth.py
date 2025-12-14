"""
Authentication module for MediBot - AWS Cognito integration.
Provides JWT token verification and user extraction.
"""

import os
import json
import time
import urllib.request
from typing import Optional, Dict, Any
from functools import lru_cache

# Cognito configuration from environment
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID", "")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID", "")
AWS_REGION = os.getenv("BEDROCK_REGION") or os.getenv("AWS_REGION", "us-east-1")

# JWKS URL for Cognito
JWKS_URL = f"https://cognito-idp.{AWS_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json"


@lru_cache(maxsize=1)
def get_jwks() -> Dict:
    """Fetch and cache JWKS from Cognito."""
    try:
        with urllib.request.urlopen(JWKS_URL, timeout=5) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching JWKS: {e}")
        return {"keys": []}


def decode_jwt_header(token: str) -> Dict:
    """Decode JWT header without verification."""
    import base64
    try:
        header_segment = token.split('.')[0]
        # Add padding if needed
        padding = 4 - len(header_segment) % 4
        if padding != 4:
            header_segment += '=' * padding
        header = base64.urlsafe_b64decode(header_segment)
        return json.loads(header)
    except Exception:
        return {}


def decode_jwt_payload(token: str) -> Dict:
    """Decode JWT payload without verification (for basic claims)."""
    import base64
    try:
        payload_segment = token.split('.')[1]
        # Add padding if needed
        padding = 4 - len(payload_segment) % 4
        if padding != 4:
            payload_segment += '=' * padding
        payload = base64.urlsafe_b64decode(payload_segment)
        return json.loads(payload)
    except Exception:
        return {}


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify a Cognito JWT token and return the user claims.
    
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
        # Decode payload (basic verification)
        payload = decode_jwt_payload(token)
        
        if not payload:
            return None
        
        # Check expiration
        exp = payload.get("exp", 0)
        if exp < time.time():
            print("Token expired")
            return None
        
        # Check issuer
        expected_issuer = f"https://cognito-idp.{AWS_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"
        if payload.get("iss") != expected_issuer:
            print("Invalid issuer")
            return None
        
        # Check audience (for id tokens) or client_id (for access tokens)
        token_use = payload.get("token_use", "")
        if token_use == "id":
            if payload.get("aud") != COGNITO_CLIENT_ID:
                print("Invalid audience")
                return None
        elif token_use == "access":
            if payload.get("client_id") != COGNITO_CLIENT_ID:
                print("Invalid client_id")
                return None
        
        return payload
        
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
