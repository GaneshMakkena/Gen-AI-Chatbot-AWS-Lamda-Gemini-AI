"""
Response models for MediBot API.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class StepImage(BaseModel):
    step_number: str
    title: str
    description: str
    image_prompt: Optional[str] = None
    image: Optional[str] = None  # Base64 encoded (fallback for local dev)
    image_url: Optional[str] = None  # S3 URL (used in production)
    s3_key: Optional[str] = None  # S3 key for URL regeneration
    is_composite: bool = False
    panel_index: Optional[int] = None
    # Fallback handling for failed images
    image_failed: bool = False
    fallback_text: Optional[Dict[str, str]] = None  # {action, method, caution, result}


class ChatResponse(BaseModel):
    answer: str
    original_query: str
    detected_language: str
    topic: Optional[str] = None
    # Step-by-step images
    step_images: Optional[List[StepImage]] = None
    steps_count: int = 0
    # Backward compatibility
    image: Optional[str] = None
    images: Optional[List[str]] = None


class ImageResponse(BaseModel):
    image: str
    prompt: str


class HealthResponse(BaseModel):
    status: str
    version: str
    model: str


class PasswordCheckResponse(BaseModel):
    valid: bool
    message: str


class UserInfo(BaseModel):
    user_id: str
    email: str
    name: str


class ChatHistoryItem(BaseModel):
    chat_id: str
    query: str
    topic: str
    timestamp: int
    created_at: str
    has_images: bool


class ChatHistoryResponse(BaseModel):
    items: List[ChatHistoryItem]
    count: int
    has_more: bool = False


class ChatDetailResponse(BaseModel):
    chat_id: str
    query: str
    response: str
    images: List[str]
    step_images: Optional[List[Dict[str, Any]]] = None
    topic: str
    language: str
    timestamp: int
    created_at: str


class UploadUrlResponse(BaseModel):
    upload_url: str
    file_key: str
    expires_in: int = 3600


class HealthProfileResponse(BaseModel):
    user_id: str
    conditions: List[Dict[str, Any]]
    medications: List[Dict[str, Any]]
    allergies: List[Dict[str, Any]]
    blood_type: str
    age: Optional[int]
    gender: str
    key_facts: List[Dict[str, Any]]
    report_summaries: List[Dict[str, Any]]
    last_updated: str
