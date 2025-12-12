"""
Medical Chatbot API Server
FastAPI backend with conversational AI and step-by-step visual instructions.
"""

import os
import base64
import hashlib
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules
from bedrock_client import (
    invoke_llm,
    generate_image,
    generate_all_step_images,
    extract_treatment_steps,
    should_generate_images,
    detect_medical_topic,
    upload_image_to_s3,
    IMAGES_BUCKET
)
from translation import (
    translate_to_english,
    translate_from_english,
    detect_language,
    SUPPORTED_LANGUAGES
)

# Initialize FastAPI app
app = FastAPI(
    title="MediBot API",
    description="AI-powered medical assistant with step-by-step visual instructions",
    version="3.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class ChatRequest(BaseModel):
    query: str
    language: str = "English"
    generate_images: bool = True
    conversation_history: Optional[List[Dict[str, str]]] = None  # For multi-turn chat


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
    from bedrock_client import LLM_MODEL_ID
    return HealthResponse(
        status="healthy", 
        version="3.0.0",
        model=LLM_MODEL_ID
    )


@app.get("/languages")
async def get_languages():
    """Get supported languages."""
    return {"languages": list(SUPPORTED_LANGUAGES.keys())}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a medical question with in-depth research and step-by-step visual instructions.
    
    Features:
    - Thorough medical research using Mistral Large 3
    - Extracts treatment steps from the response
    - Generates an image for EACH step (no limit)
    - All images are 512x512 resolution
    - Conversational, helpful responses
    """
    query = request.query.strip()
    language = request.language
    
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
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
    
    # Get LLM response with in-depth research
    print(f"Processing query: {english_query[:100]}...")
    response = invoke_llm(english_query, context=context)
    
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
            
            # Limit removed - Mistral Small is fast enough (~5-7s) to allow 
            # standard parallel image generation for all steps within 30s timeout.
            # Typical step count is 5-8. Max duration ~15s total.
            
            print(f"Generating images for all {len(steps)} steps")
            
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


# Run with: uvicorn api_server:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
