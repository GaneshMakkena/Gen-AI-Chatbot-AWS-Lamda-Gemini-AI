"""
Request models for MediBot API.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class Attachment(BaseModel):
    filename: str
    content_type: str
    data: Optional[str] = None  # Base64 encoded file data (optional if s3_key provided)
    s3_key: Optional[str] = None  # S3 Key for large files
    type: str  # "pdf" or "image"


class ChatRequest(BaseModel):
    query: str
    language: str = "English"
    generate_images: bool = True
    conversation_history: Optional[List[Dict[str, str]]] = None  # For multi-turn chat
    thinking_mode: bool = False  # Show AI reasoning process
    attachments: Optional[List[Attachment]] = None  # File attachments


class ImageRequest(BaseModel):
    prompt: str
    width: int = 512
    height: int = 512


class PasswordCheckRequest(BaseModel):
    email: str
    password: str


class UploadUrlRequest(BaseModel):
    filename: str
    content_type: str = "application/pdf"


class PresignedUrlRequest(BaseModel):
    filename: str
    content_type: str


class ProfileUpdateRequest(BaseModel):
    conditions: Optional[List[str]] = None
    medications: Optional[List[Dict[str, str]]] = None
    allergies: Optional[List[str]] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    blood_type: Optional[str] = None


class AnalyzeReportRequest(BaseModel):
    file_key: str


class ConfirmAnalysisRequest(BaseModel):
    file_key: str
    extracted: Dict[str, Any]


class GuestTrialStatus(BaseModel):
    allowed: bool
    remaining: int
    message_count: int
    limit: int
