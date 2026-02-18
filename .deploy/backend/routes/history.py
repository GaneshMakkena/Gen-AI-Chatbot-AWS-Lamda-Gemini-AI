"""
History route module for MediBot.
Handles /history endpoints.
"""

from fastapi import APIRouter, Depends
from aws_lambda_powertools import Logger

from models.response_models import (
    ChatHistoryItem,
    ChatHistoryResponse,
    ChatDetailResponse,
)
from dependencies import require_auth
from chat_history import get_user_chats, get_chat, delete_chat, get_chat_summary

logger = Logger(service="medibot")
router = APIRouter()


@router.get("/history", response_model=ChatHistoryResponse)
async def list_chat_history(
    limit: int = 20,
    user: dict = Depends(require_auth),
):
    """Get user's chat history (requires auth)."""
    result = get_user_chats(user["user_id"], limit=limit)
    items = [get_chat_summary(chat) for chat in result.get("items", [])]

    return ChatHistoryResponse(
        items=[ChatHistoryItem(**item) for item in items],
        count=len(items),
        has_more="last_key" in result,
    )


@router.get("/history/{chat_id}", response_model=ChatDetailResponse)
async def get_chat_detail(
    chat_id: str,
    user: dict = Depends(require_auth),
):
    """Get a specific chat with full details."""
    chat = get_chat(user["user_id"], chat_id)
    if not chat:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Chat not found")

    return ChatDetailResponse(
        chat_id=chat.get("chat_id", ""),
        query=chat.get("query", ""),
        response=chat.get("response", ""),
        images=chat.get("images", []),
        step_images=chat.get("step_images", []),
        topic=chat.get("topic", ""),
        language=chat.get("language", "English"),
        timestamp=chat.get("timestamp", 0),
        created_at=chat.get("created_at", ""),
    )


@router.delete("/history/{chat_id}")
async def delete_chat_endpoint(
    chat_id: str,
    user: dict = Depends(require_auth),
):
    """Delete a specific chat."""
    success = delete_chat(user["user_id"], chat_id)
    if success:
        return {"message": "Chat deleted", "chat_id": chat_id}

    from fastapi import HTTPException
    raise HTTPException(status_code=500, detail="Failed to delete chat")
