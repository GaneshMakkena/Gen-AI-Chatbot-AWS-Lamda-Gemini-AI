"""
Auth route module for MediBot.
Handles /auth/* and /guest/* endpoints.
"""

import os
from typing import Optional

from fastapi import APIRouter, Depends, Header
from aws_lambda_powertools import Logger

from models.request_models import PasswordCheckRequest
from models.response_models import PasswordCheckResponse, UserInfo
from dependencies import get_optional_user, require_auth, get_client_info
# Improvement 2.4: Import password_history at module level
from password_history import is_password_previously_used, store_password_hash
from auth import get_user_info
from guest_tracking import check_guest_limit

logger = Logger(service="medibot")
router = APIRouter()

# Environment variables
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID", "")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID", "")


@router.post("/auth/check-password", response_model=PasswordCheckResponse)
async def check_password(request: PasswordCheckRequest):
    """
    Check if a password was previously used by this user.
    Called before password reset to prevent reuse.
    """
    try:
        is_used = is_password_previously_used(request.email, request.password)

        if is_used:
            return PasswordCheckResponse(
                valid=False,
                message="This password was used recently. Please choose a different password.",
            )

        return PasswordCheckResponse(valid=True, message="Password is valid.")
    except Exception as e:
        logger.error("Password check error", error=str(e))
        return PasswordCheckResponse(valid=True, message="Password check skipped.")


@router.post("/auth/store-password")
async def store_password(request: PasswordCheckRequest):
    """
    Store a password hash after successful password reset.
    Called after Cognito password reset completes.
    """
    try:
        success = store_password_hash(request.email, request.password)
        return {"success": success}
    except Exception as e:
        logger.error("Password store error", error=str(e))
        return {"success": False, "error": str(e)}


@router.get("/guest/status")
async def get_guest_trial_status(
    client_info: dict = Depends(get_client_info),
):
    """
    Check guest trial status.
    Returns remaining messages and whether guest can continue.
    """
    status = check_guest_limit(
        ip_address=client_info["ip_address"],
        user_agent=client_info["user_agent"],
        fingerprint=client_info["fingerprint"],
    )

    return {
        "allowed": status["allowed"],
        "remaining": status["remaining"],
        "message_count": status["message_count"],
        "limit": status["limit"],
    }


@router.get("/auth/verify")
async def verify_auth(authorization: Optional[str] = Header(None)):
    """Verify if the user's token is valid."""
    if not authorization:
        return {"authenticated": False, "message": "No token provided"}

    user = get_user_info(authorization)
    if user:
        return {"authenticated": True, "user": user}
    return {"authenticated": False, "message": "Invalid or expired token"}


@router.get("/auth/me", response_model=UserInfo)
async def get_current_user(user: dict = Depends(require_auth)):
    """Get current user information."""
    return UserInfo(
        user_id=user.get("user_id", ""),
        email=user.get("email", ""),
        name=user.get("name", ""),
    )


@router.get("/auth/config")
async def get_auth_config():
    """Get Cognito configuration for frontend."""
    return {
        "userPoolId": COGNITO_USER_POOL_ID,
        "clientId": COGNITO_CLIENT_ID,
        "region": os.getenv("AWS_REGION", "us-east-1"),
    }
