"""
FastAPI Dependencies for MediBot API.
Reusable dependency injection for auth, client info, etc.
"""

from typing import Optional
from fastapi import Header, HTTPException
from auth import get_user_info


async def get_optional_user(
    authorization: Optional[str] = Header(None),
) -> Optional[dict]:
    """
    Optional auth dependency.
    Returns user info dict if valid token is provided, None otherwise.
    """
    if not authorization:
        return None
    return get_user_info(authorization)


async def require_auth(
    authorization: Optional[str] = Header(None),
) -> dict:
    """
    Required auth dependency.
    Raises 401 if no valid token is provided.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")

    user = get_user_info(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return user


async def get_client_info(
    x_forwarded_for: Optional[str] = Header(None),
    user_agent: Optional[str] = Header(None),
    x_fingerprint: Optional[str] = Header(None),
) -> dict:
    """
    Extract client information from request headers.
    """
    ip_address = x_forwarded_for.split(",")[0].strip() if x_forwarded_for else "unknown"
    return {
        "ip_address": ip_address,
        "user_agent": user_agent or "",
        "fingerprint": x_fingerprint or "",
    }
