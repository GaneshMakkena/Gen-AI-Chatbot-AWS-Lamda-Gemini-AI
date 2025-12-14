"""
Chat History module for MediBot - DynamoDB integration.
Handles storing and retrieving user chat history.
"""

import os
import time
import uuid
import boto3
from typing import Optional, Dict, Any, List
from datetime import datetime

# DynamoDB configuration from environment
CHAT_TABLE = os.getenv("CHAT_TABLE", "medibot-chats-production")
AWS_REGION = os.getenv("BEDROCK_REGION") or os.getenv("AWS_REGION", "us-east-1")

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
    return get_dynamodb().Table(CHAT_TABLE)


def generate_chat_id() -> str:
    """Generate a unique chat ID."""
    return f"chat_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"


def save_chat(
    user_id: str,
    query: str,
    response: str,
    images: Optional[List[str]] = None,
    topic: Optional[str] = None,
    language: str = "English",
    chat_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Save a chat message to DynamoDB.
    
    Args:
        user_id: The user's Cognito sub ID
        query: User's question
        response: AI's response
        images: List of image URLs
        topic: Detected medical topic
        language: Response language
        chat_id: Optional existing chat ID (for multi-turn)
        
    Returns:
        The saved chat item
    """
    if not chat_id:
        chat_id = generate_chat_id()
    
    timestamp = int(time.time() * 1000)
    
    # Calculate TTL (90 days from now)
    ttl = int(time.time()) + (90 * 24 * 60 * 60)
    
    item = {
        "user_id": user_id,
        "chat_id": chat_id,
        "timestamp": timestamp,
        "query": query,
        "response": response,
        "images": images or [],
        "topic": topic or "",
        "language": language,
        "ttl": ttl,
        "created_at": datetime.utcnow().isoformat()
    }
    
    try:
        table = get_table()
        table.put_item(Item=item)
        print(f"Saved chat {chat_id} for user {user_id[:8]}...")
        return item
    except Exception as e:
        print(f"Error saving chat: {e}")
        return item


def get_chat(user_id: str, chat_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific chat by ID."""
    try:
        table = get_table()
        response = table.get_item(
            Key={
                "user_id": user_id,
                "chat_id": chat_id
            }
        )
        return response.get("Item")
    except Exception as e:
        print(f"Error getting chat: {e}")
        return None


def get_user_chats(
    user_id: str,
    limit: int = 50,
    last_key: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Get all chats for a user, sorted by timestamp (newest first).
    
    Args:
        user_id: The user's Cognito sub ID
        limit: Maximum number of chats to return
        last_key: Pagination key for next page
        
    Returns:
        Dict with "items" and optional "last_key" for pagination
    """
    try:
        table = get_table()
        
        query_params = {
            "KeyConditionExpression": "user_id = :uid",
            "ExpressionAttributeValues": {
                ":uid": user_id
            },
            "ScanIndexForward": False,  # Newest first
            "Limit": limit
        }
        
        if last_key:
            query_params["ExclusiveStartKey"] = last_key
        
        response = table.query(**query_params)
        
        result = {
            "items": response.get("Items", []),
            "count": response.get("Count", 0)
        }
        
        if "LastEvaluatedKey" in response:
            result["last_key"] = response["LastEvaluatedKey"]
        
        return result
        
    except Exception as e:
        print(f"Error getting user chats: {e}")
        return {"items": [], "count": 0}


def get_recent_chats(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get the most recent chats for a user (for sidebar preview)."""
    result = get_user_chats(user_id, limit=limit)
    return result.get("items", [])


def delete_chat(user_id: str, chat_id: str) -> bool:
    """Delete a specific chat."""
    try:
        table = get_table()
        table.delete_item(
            Key={
                "user_id": user_id,
                "chat_id": chat_id
            }
        )
        print(f"Deleted chat {chat_id}")
        return True
    except Exception as e:
        print(f"Error deleting chat: {e}")
        return False


def delete_all_user_chats(user_id: str) -> int:
    """Delete all chats for a user. Returns count of deleted items."""
    try:
        table = get_table()
        deleted_count = 0
        
        # First, query all items for the user
        response = table.query(
            KeyConditionExpression="user_id = :uid",
            ExpressionAttributeValues={":uid": user_id},
            ProjectionExpression="user_id, chat_id"
        )
        
        # Delete each item
        with table.batch_writer() as batch:
            for item in response.get("Items", []):
                batch.delete_item(Key={
                    "user_id": item["user_id"],
                    "chat_id": item["chat_id"]
                })
                deleted_count += 1
        
        print(f"Deleted {deleted_count} chats for user {user_id[:8]}...")
        return deleted_count
        
    except Exception as e:
        print(f"Error deleting all chats: {e}")
        return 0


def get_chat_summary(chat: Dict[str, Any]) -> Dict[str, Any]:
    """Get a summary of a chat for list display."""
    return {
        "chat_id": chat.get("chat_id", ""),
        "query": chat.get("query", "")[:100],  # First 100 chars
        "topic": chat.get("topic", ""),
        "timestamp": chat.get("timestamp", 0),
        "created_at": chat.get("created_at", ""),
        "has_images": len(chat.get("images", [])) > 0
    }
