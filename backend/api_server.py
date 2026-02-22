"""
Medical Chatbot API Server
FastAPI backend with conversational AI and step-by-step visual instructions.

This is the main application entry point. Route handlers are organized
into modules under the routes/ package.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from aws_lambda_powertools import Logger

# Load environment variables
load_dotenv()

logger = Logger(service="medibot")

# Initialize FastAPI app
app = FastAPI(
    title="MediBot API",
    description="AI-powered medical assistant with step-by-step visual instructions",
    version="4.0.0",
)

# Configure CORS - Use env var or fallback to known origins
# Improvement 2.2: Parameterize CloudFront domain via FRONTEND_DOMAIN env var
FRONTEND_DOMAIN = os.getenv("FRONTEND_DOMAIN", "")
ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Local development (CRA)
    "http://localhost:5173",  # Local development (Vite)
]
if FRONTEND_DOMAIN:
    ALLOWED_ORIGINS.append(f"https://{FRONTEND_DOMAIN}")
else:
    # Fallback to hardcoded domains for backward compatibility
    ALLOWED_ORIGINS.extend([
        "https://d17eixu2k5iihu.cloudfront.net",  # Production frontend (us-east-1)
        "https://d2g86is4qt16os.cloudfront.net",  # Production frontend (ap-south-2)
    ])

# Always enable CORS middleware so FastAPI handles OPTIONS requests correctly
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)

# Import route modules and include routers
from routes.chat import router as chat_router  # noqa: E402
from routes.auth_routes import router as auth_router  # noqa: E402
from routes.history import router as history_router  # noqa: E402
from routes.profile import router as profile_router  # noqa: E402
from routes.upload import router as upload_router  # noqa: E402

app.include_router(chat_router)
app.include_router(auth_router)
app.include_router(history_router)
app.include_router(profile_router)
app.include_router(upload_router)

# Import models for backward compatibility with tests
from models.response_models import HealthResponse  # noqa: E402, F401
from gemini_client import LLM_MODEL_ID  # noqa: E402
from translation import SUPPORTED_LANGUAGES  # noqa: E402


# Core endpoints that stay in the main app
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="4.0.0-gemini",
        model=LLM_MODEL_ID,
    )


@app.get("/languages")
async def get_languages():
    """Get supported languages."""
    return {"languages": list(SUPPORTED_LANGUAGES.keys())}


# Run with: uvicorn api_server:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
