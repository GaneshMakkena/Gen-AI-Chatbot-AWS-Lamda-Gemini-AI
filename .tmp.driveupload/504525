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
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

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


# S3 client for URL regeneration
_s3_client = None
IMAGES_BUCKET = os.getenv("IMAGES_BUCKET", "")

def _get_s3_client():
    """Get or create S3 client."""
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client('s3', region_name=AWS_REGION)
    return _s3_client


def regenerate_image_urls(step_images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Regenerate pre-signed URLs for step images from stored S3 keys.
    This allows old chats to display images even after URLs expire.
    """
    if not step_images or not IMAGES_BUCKET:
        return step_images

    s3 = _get_s3_client()
    updated_images = []

    for img in step_images:
        img_copy = dict(img)
        s3_key = img.get('s3_key')

        if s3_key:
            try:
                # Regenerate presigned URL valid for 7 days
                new_url = s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': IMAGES_BUCKET, 'Key': s3_key},
                    ExpiresIn=604800  # 7 days
                )
                img_copy['image_url'] = new_url
            except Exception as e:
                print(f"Error regenerating URL for {s3_key}: {e}")

        updated_images.append(img_copy)

    return updated_images


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
    chat_id: Optional[str] = None,
    step_images: Optional[List[Dict[str, Any]]] = None,
    attachments: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Save a chat message to DynamoDB.

    Args:
        user_id: The user's Cognito sub ID
        query: User's question
        response: AI's response
        images: List of image URLs (legacy format)
        topic: Detected medical topic
        language: Response language
        chat_id: Optional existing chat ID (for multi-turn)
        step_images: Full step image objects with titles/descriptions
        attachments: User-attached files metadata

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
        "created_at": datetime.utcnow().isoformat(),
        # New fields for full conversation support
        "step_images": step_images or [],
        "attachments": attachments or []
    }

    try:
        table = get_table()
        table.put_item(Item=item)
        print(f"Saved chat {chat_id} for user {user_id[:8]}... (with {len(step_images or [])} images, {len(attachments or [])} attachments)")
        return item
    except Exception as e:
        print(f"Error saving chat: {e}")
        return item


def get_chat(user_id: str, chat_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific chat by ID with fresh image URLs."""
    try:
        table = get_table()
        response = table.get_item(
            Key={
                "user_id": user_id,
                "chat_id": chat_id
            }
        )
        chat = response.get("Item")

        if chat and chat.get("step_images"):
            # Regenerate URLs for old images
            chat["step_images"] = regenerate_image_urls(chat["step_images"])

        return chat
    except Exception as e:
        print(f"Error getting chat: {e}")
        return None


def get_user_chats(
    user_id: str,
    limit: int = 100,  # Increased from 50
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
    """Delete a specific chat and its associated S3 images."""
    try:
        table = get_table()

        # First, get the chat to find image URLs
        response = table.get_item(
            Key={"user_id": user_id, "chat_id": chat_id}
        )
        chat = response.get("Item")

        if chat:
            # Delete images from S3
            images = chat.get("images", [])
            if images:
                _delete_s3_images(images)

        # Delete from DynamoDB
        table.delete_item(
            Key={
                "user_id": user_id,
                "chat_id": chat_id
            }
        )
        print(f"Deleted chat {chat_id} (with {len(images) if chat else 0} images)")
        return True
    except Exception as e:
        print(f"Error deleting chat: {e}")
        return False


def _delete_s3_images(image_urls: List[str]) -> int:
    """Delete images from S3 given their URLs. Returns count of deleted images."""
    if not image_urls:
        return 0

    deleted_count = 0
    images_bucket = os.getenv("IMAGES_BUCKET", "medibot-images-748325220003-us-east-1-production")

    try:
        s3 = boto3.client('s3', region_name=AWS_REGION)

        for url in image_urls:
            try:
                # Extract object key from S3 URL
                # URL format: https://bucket-name.s3.region.amazonaws.com/key
                # or s3://bucket/key
                if "s3.amazonaws.com" in url or "s3-" in url:
                    # Parse the key from URL
                    parts = url.split("/")
                    key = "/".join(parts[3:]) if len(parts) > 3 else None
                elif url.startswith("s3://"):
                    key = url.split("/", 3)[3] if len(url.split("/")) > 3 else None
                else:
                    # It might be just the key or a different format
                    continue

                if key:
                    s3.delete_object(Bucket=images_bucket, Key=key)
                    deleted_count += 1
                    print(f"Deleted S3 image: {key}")
            except Exception as e:
                print(f"Failed to delete image {url}: {e}")
                continue

        return deleted_count
    except Exception as e:
        print(f"Error connecting to S3: {e}")
        return 0


def delete_all_user_chats(user_id: str) -> int:
    """Delete all chats for a user and their S3 images. Returns count of deleted items."""
    try:
        table = get_table()
        deleted_count = 0
        images_deleted = 0

        # First, query all items for the user (including images for S3 cleanup)
        response = table.query(
            KeyConditionExpression="user_id = :uid",
            ExpressionAttributeValues={":uid": user_id},
            ProjectionExpression="user_id, chat_id, images"
        )

        # Delete S3 images first, then DynamoDB records
        items = response.get("Items", [])

        for item in items:
            images = item.get("images", [])
            if images:
                images_deleted += _delete_s3_images(images)

        # Batch delete from DynamoDB
        with table.batch_writer() as batch:
            for item in items:
                batch.delete_item(Key={
                    "user_id": item["user_id"],
                    "chat_id": item["chat_id"]
                })
                deleted_count += 1

        print(f"Deleted {deleted_count} chats and {images_deleted} images for user {user_id[:8]}...")
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
