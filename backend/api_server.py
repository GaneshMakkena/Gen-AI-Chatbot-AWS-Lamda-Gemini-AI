"""
Medical Chatbot API Server
FastAPI backend with conversational AI and step-by-step visual instructions.
"""

import os
import base64
import hashlib
import boto3
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules - Using Gemini instead of Bedrock
from gemini_client import (
    invoke_llm,
    generate_image,
    generate_all_step_images,
    extract_treatment_steps,
    should_generate_images,
    detect_medical_topic,
    upload_image_to_s3,
    IMAGES_BUCKET,
    LLM_MODEL_ID
)
from translation import (
    translate_to_english,
    translate_from_english,
    detect_language,
    SUPPORTED_LANGUAGES
)
# Phase 2: Auth and History
from auth import get_user_info, verify_token
from chat_history import (
    save_chat, get_user_chats, get_chat, delete_chat,
    get_chat_summary, generate_chat_id
)
# Phase 2.5: Health Memory RAG
from health_profile import (
    get_health_profile, get_context_summary, get_or_create_profile,
    add_condition, add_medication, add_allergy, update_basic_info,
    delete_health_profile, remove_condition
)
from report_analyzer import (
    analyze_report, confirm_and_save_analysis, extract_facts_from_chat
)

# Initialize FastAPI app
app = FastAPI(
    title="MediBot API",
    description="AI-powered medical assistant with step-by-step visual instructions",
    version="3.0.0"
)

# Configure CORS - Restrict to known origins
ALLOWED_ORIGINS = [
    "https://d17eixu2k5iihu.cloudfront.net",  # Production frontend
    "http://localhost:3000",  # Local development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)


# Request/Response Models
class ChatRequest(BaseModel):
    query: str
    language: str = "English"
    generate_images: bool = True
    conversation_history: Optional[List[Dict[str, str]]] = None  # For multi-turn chat
    thinking_mode: bool = False  # Show AI reasoning process


class StepImage(BaseModel):
    step_number: str
    title: str
    description: str
    image_prompt: Optional[str] = None
    image: Optional[str] = None  # Base64 encoded (fallback for local dev)
    image_url: Optional[str] = None  # S3 URL (used in production)


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


class ImageRequest(BaseModel):
    prompt: str
    width: int = 512
    height: int = 512


class ImageResponse(BaseModel):
    image: str
    prompt: str


class HealthResponse(BaseModel):
    status: str
    version: str
    model: str


# API Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy", 
        version="4.0.0-gemini",
        model=LLM_MODEL_ID
    )


@app.get("/languages")
async def get_languages():
    """Get supported languages."""
    return {"languages": list(SUPPORTED_LANGUAGES.keys())}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, authorization: Optional[str] = Header(None)):
    """
    Process a medical question with in-depth research and step-by-step visual instructions.
    
    Features:
    - Thorough medical research using Mistral Large 3
    - Extracts treatment steps from the response
    - Generates an image for EACH step (no limit)
    - All images are 512x512 resolution
    - Conversational, helpful responses
    - Saves chat to DynamoDB if authenticated
    """
    query = request.query.strip()
    language = request.language
    
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    # Check if user is authenticated (optional)
    user_info = None
    if authorization:
        user_info = get_user_info(authorization)
    
    # Detect input language and translate to English if needed
    detected_lang = detect_language(query)
    english_query = query
    
    if detected_lang != "en":
        english_query, _ = translate_to_english(query, detected_lang)
    
    # Build context from conversation history if provided
    context = ""
    if request.conversation_history:
        context = "\n".join([
            f"{'User' if msg.get('role') == 'user' else 'Assistant'}: {msg.get('content', '')}"
            for msg in request.conversation_history[-4:]  # Last 4 messages for context
        ])
    
    # Phase 2.5: Inject health context for personalized RAG
    health_context = ""
    if user_info:
        health_context = get_context_summary(user_info["user_id"])
        if health_context:
            print(f"Injecting health context for user {user_info['user_id'][:8]}...")
            # Prepend health context to conversation context
            context = health_context + "\n" + context
    
    # Get LLM response with in-depth research
    print(f"Processing query: {english_query[:100]}... (thinking_mode={request.thinking_mode})")
    response = invoke_llm(english_query, context=context, thinking_mode=request.thinking_mode)
    
    if not response:
        raise HTTPException(status_code=500, detail="Failed to get response from AI")
    
    # Translate response back if needed
    final_response = response
    target_lang = SUPPORTED_LANGUAGES.get(language, "en")
    
    if target_lang != "en":
        final_response = translate_from_english(response, target_lang)
    
    # Detect topic
    topic = detect_medical_topic(english_query)
    
    # Generate step-by-step images
    step_images_list = None
    all_images = []
    primary_image = None
    
    if request.generate_images and should_generate_images(english_query, response):
        # Extract treatment steps from the LLM response
        steps = extract_treatment_steps(response)
        print(f"Extracted {len(steps)} treatment steps")
        
        if steps:
            # Generate a unique hash for this query (for S3 path organization)
            query_hash = hashlib.md5(english_query.encode()).hexdigest()[:12]
            
            # LIMIT TO 5 IMAGES: API Gateway has a hard 29-second timeout
            # LLM takes ~20-25s, leaving only ~4-8s for images
            # Each image takes ~1.5s, so 5 images = ~7.5s
            steps = steps[:5]
            
            print(f"Generating images for {len(steps)} steps (max 5)")
            
            # Pass query_hash to enable internal parallel S3 upload
            step_images_data = generate_all_step_images(steps, english_query, query_hash=query_hash)
            
            # Convert to response format
            step_images_list = []
            for step_data in step_images_data:
                image_url = step_data.get('image_url')
                image_base64 = step_data.get('image')
                
                step_images_list.append(StepImage(
                    step_number=step_data['step_number'],
                    title=step_data['title'],
                    description=step_data['description'],
                    image_prompt=step_data.get('image_prompt'),
                    image=image_base64 if not image_url else None,  # Only include base64 if no S3 URL
                    image_url=image_url
                ))
                
                if image_url:
                    all_images.append(image_url)
                elif image_base64:
                    all_images.append(image_base64)
            
            if all_images:
                primary_image = all_images[0]
    
    # Save chat to DynamoDB if user is authenticated
    if user_info:
        try:
            save_chat(
                user_id=user_info["user_id"],
                query=query,
                response=final_response,
                images=all_images if all_images else [],
                topic=topic,
                language=language
            )
            print(f"Chat saved for user {user_info['user_id'][:8]}...")
        except Exception as e:
            print(f"Failed to save chat: {e}")
            # Don't fail the request if chat save fails
        
        # Phase 2.5: Extract health facts from user's message (background task)
        try:
            extracted = extract_facts_from_chat(user_info["user_id"], query, final_response)
            if extracted:
                print(f"Extracted facts: {extracted}")
        except Exception as e:
            print(f"Failed to extract facts: {e}")
    
    return ChatResponse(
        answer=final_response,
        original_query=query,
        detected_language=detected_lang,
        topic=topic,
        step_images=step_images_list,
        steps_count=len(step_images_list) if step_images_list else 0,
        image=primary_image,
        images=all_images if all_images else None
    )


@app.post("/generate-image", response_model=ImageResponse)
async def create_image(request: ImageRequest):
    """Generate a single medical illustration."""
    image_b64 = generate_image(
        request.prompt,
        width=request.width,
        height=request.height
    )
    
    if not image_b64:
        raise HTTPException(status_code=500, detail="Failed to generate image")
    
    return ImageResponse(image=image_b64, prompt=request.prompt)


# ============================================
# Phase 2: Authentication & User Features
# ============================================

# Environment variables for Phase 2
REPORTS_BUCKET = os.getenv("REPORTS_BUCKET", "")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID", "")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID", "")


# Request/Response Models for Phase 2
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
    topic: str
    language: str
    timestamp: int
    created_at: str


class UploadUrlRequest(BaseModel):
    filename: str
    content_type: str = "application/pdf"


class UploadUrlResponse(BaseModel):
    upload_url: str
    file_key: str
    expires_in: int = 3600


# Auth Endpoints
@app.get("/auth/verify")
async def verify_auth(authorization: Optional[str] = Header(None)):
    """Verify if the user's token is valid."""
    if not authorization:
        return {"authenticated": False, "message": "No token provided"}
    
    user = get_user_info(authorization)
    if user:
        return {"authenticated": True, "user": user}
    return {"authenticated": False, "message": "Invalid or expired token"}


@app.get("/auth/me", response_model=UserInfo)
async def get_current_user(authorization: Optional[str] = Header(None)):
    """Get current user information."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")
    
    user = get_user_info(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return UserInfo(
        user_id=user.get("user_id", ""),
        email=user.get("email", ""),
        name=user.get("name", "")
    )


@app.get("/auth/config")
async def get_auth_config():
    """Get Cognito configuration for frontend."""
    return {
        "userPoolId": COGNITO_USER_POOL_ID,
        "clientId": COGNITO_CLIENT_ID,
        "region": os.getenv("BEDROCK_REGION", "us-east-1")
    }


# Chat History Endpoints
@app.get("/history", response_model=ChatHistoryResponse)
async def list_chat_history(
    authorization: Optional[str] = Header(None),
    limit: int = 20
):
    """Get user's chat history (requires auth)."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")
    
    user = get_user_info(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    result = get_user_chats(user["user_id"], limit=limit)
    items = [get_chat_summary(chat) for chat in result.get("items", [])]
    
    return ChatHistoryResponse(
        items=[ChatHistoryItem(**item) for item in items],
        count=len(items),
        has_more="last_key" in result
    )


@app.get("/history/{chat_id}", response_model=ChatDetailResponse)
async def get_chat_detail(
    chat_id: str,
    authorization: Optional[str] = Header(None)
):
    """Get a specific chat with full details."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")
    
    user = get_user_info(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    chat = get_chat(user["user_id"], chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    return ChatDetailResponse(
        chat_id=chat.get("chat_id", ""),
        query=chat.get("query", ""),
        response=chat.get("response", ""),
        images=chat.get("images", []),
        topic=chat.get("topic", ""),
        language=chat.get("language", "English"),
        timestamp=chat.get("timestamp", 0),
        created_at=chat.get("created_at", "")
    )


@app.delete("/history/{chat_id}")
async def delete_chat_endpoint(
    chat_id: str,
    authorization: Optional[str] = Header(None)
):
    """Delete a specific chat."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")
    
    user = get_user_info(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    success = delete_chat(user["user_id"], chat_id)
    if success:
        return {"message": "Chat deleted", "chat_id": chat_id}
    raise HTTPException(status_code=500, detail="Failed to delete chat")


# Report Upload Endpoints
@app.post("/upload-report", response_model=UploadUrlResponse)
async def get_upload_url(
    request: UploadUrlRequest,
    authorization: Optional[str] = Header(None)
):
    """Get a presigned URL to upload a medical report."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")
    
    user = get_user_info(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    if not REPORTS_BUCKET:
        raise HTTPException(status_code=500, detail="Reports bucket not configured")
    
    # Validate content type
    allowed_types = ["application/pdf", "image/jpeg", "image/png", "image/jpg"]
    if request.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid content type. Allowed: {allowed_types}"
        )
    
    # Generate unique file key
    import uuid
    import time
    file_ext = request.filename.split(".")[-1] if "." in request.filename else "pdf"
    file_key = f"reports/{user['user_id']}/{int(time.time())}_{uuid.uuid4().hex[:8]}.{file_ext}"
    
    # Generate presigned URL
    s3 = boto3.client('s3', region_name=os.getenv("BEDROCK_REGION", "us-east-1"))
    try:
        upload_url = s3.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': REPORTS_BUCKET,
                'Key': file_key,
                'ContentType': request.content_type
            },
            ExpiresIn=3600  # 1 hour
        )
        
        return UploadUrlResponse(
            upload_url=upload_url,
            file_key=file_key,
            expires_in=3600
        )
    except Exception as e:
        print(f"Error generating presigned URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate upload URL")


# ============================================
# Phase 2.5: Health Profile & RAG Endpoints
# ============================================

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


@app.get("/profile")
async def get_profile(authorization: Optional[str] = Header(None)):
    """Get user's health profile."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")
    
    user = get_user_info(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    profile = get_or_create_profile(user["user_id"])
    
    return {
        "user_id": profile.get("user_id", ""),
        "conditions": profile.get("conditions", []),
        "medications": profile.get("medications", []),
        "allergies": profile.get("allergies", []),
        "blood_type": profile.get("blood_type", ""),
        "age": profile.get("age"),
        "gender": profile.get("gender", ""),
        "key_facts": profile.get("key_facts", []),
        "report_summaries": profile.get("report_summaries", []),
        "last_updated": profile.get("last_updated", "")
    }


@app.put("/profile")
async def update_profile(
    request: ProfileUpdateRequest,
    authorization: Optional[str] = Header(None)
):
    """Update user's health profile manually."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")
    
    user = get_user_info(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = user["user_id"]
    
    # Add conditions
    if request.conditions:
        for condition in request.conditions:
            add_condition(user_id, condition, source="manual")
    
    # Add medications
    if request.medications:
        for med in request.medications:
            add_medication(user_id, med.get("name", ""), med.get("dosage", ""), source="manual")
    
    # Add allergies
    if request.allergies:
        for allergy in request.allergies:
            add_allergy(user_id, allergy, source="manual")
    
    # Update basic info
    if any([request.age, request.gender, request.blood_type]):
        update_basic_info(user_id, age=request.age, gender=request.gender, blood_type=request.blood_type)
    
    return {"message": "Profile updated", "user_id": user_id}


@app.delete("/profile")
async def delete_profile(authorization: Optional[str] = Header(None)):
    """Delete user's entire health profile."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")
    
    user = get_user_info(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    success = delete_health_profile(user["user_id"])
    if success:
        return {"message": "Profile deleted"}
    raise HTTPException(status_code=500, detail="Failed to delete profile")


@app.delete("/profile/condition/{condition_name}")
async def remove_profile_condition(
    condition_name: str,
    authorization: Optional[str] = Header(None)
):
    """Remove a specific condition from user's profile."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")
    
    user = get_user_info(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    success = remove_condition(user["user_id"], condition_name)
    if success:
        return {"message": f"Condition '{condition_name}' removed"}
    raise HTTPException(status_code=404, detail="Condition not found")


@app.post("/analyze-report")
async def analyze_uploaded_report(
    request: AnalyzeReportRequest,
    authorization: Optional[str] = Header(None)
):
    """Analyze an uploaded medical report using Gemini multimodal."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")
    
    user = get_user_info(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    result = analyze_report(request.file_key, user["user_id"])
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Analysis failed"))
    
    return result


@app.post("/confirm-analysis")
async def confirm_report_analysis(
    request: ConfirmAnalysisRequest,
    authorization: Optional[str] = Header(None)
):
    """Confirm and save extracted health information from a report."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")
    
    user = get_user_info(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    result = confirm_and_save_analysis(user["user_id"], request.extracted, request.file_key)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Save failed"))
    
    return result


# Run with: uvicorn api_server:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

