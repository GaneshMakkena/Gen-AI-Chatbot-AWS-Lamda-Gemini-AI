"""
Pytest fixtures and configuration for MediBot backend tests.
Provides mocked AWS services and test data.
"""

import os
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

# Set test environment before importing app
os.environ.setdefault("GOOGLE_API_KEY", "test-api-key")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("COGNITO_USER_POOL_ID", "us-east-1_test123")
os.environ.setdefault("COGNITO_CLIENT_ID", "test-client-id")
os.environ.setdefault("COGNITO_REGION", "us-east-1")
os.environ.setdefault("CHAT_TABLE", "medibot-chats-test")
os.environ.setdefault("HEALTH_PROFILE_TABLE", "medibot-health-profiles-test")
os.environ.setdefault("IMAGES_BUCKET", "medibot-images-test")
os.environ.setdefault("REPORTS_BUCKET", "medibot-reports-test")


# --- Mock AWS Services ---

@pytest.fixture
def mock_dynamodb():
    """Mock boto3 DynamoDB client."""
    with patch("boto3.resource") as mock_resource:
        mock_table = MagicMock()
        mock_resource.return_value.Table.return_value = mock_table
        yield mock_table


@pytest.fixture
def mock_s3():
    """Mock boto3 S3 client."""
    with patch("boto3.client") as mock_client:
        mock_s3_client = MagicMock()
        mock_client.return_value = mock_s3_client
        yield mock_s3_client


@pytest.fixture
def mock_cognito():
    """Mock Cognito client for token verification."""
    with patch("boto3.client") as mock_client:
        mock_cognito_client = MagicMock()
        mock_client.return_value = mock_cognito_client
        yield mock_cognito_client


# --- Test Data Fixtures ---

@pytest.fixture
def sample_user_token():
    """Sample JWT token for authenticated requests."""
    return "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXItaWQiLCJlbWFpbCI6InRlc3RAdGVzdC5jb20iLCJuYW1lIjoiVGVzdCBVc2VyIn0.test"


@pytest.fixture
def sample_user_info():
    """Sample user info returned from token verification."""
    return {
        "user_id": "test-user-id",
        "email": "test@test.com",
        "name": "Test User"
    }


@pytest.fixture
def sample_chat_request():
    """Sample chat request payload."""
    return {
        "query": "How do I treat a headache?",
        "language": "English",
        "generate_images": False,
        "thinking_mode": False
    }


@pytest.fixture
def sample_health_profile():
    """Sample health profile data."""
    return {
        "user_id": "test-user-id",
        "conditions": [
            {"name": "Diabetes Type 2", "diagnosed": "2020-01-01", "status": "active"}
        ],
        "medications": [
            {"name": "Metformin", "dosage": "500mg", "frequency": "twice daily"}
        ],
        "allergies": [
            {"name": "Penicillin", "severity": "severe"}
        ],
        "blood_type": "O+",
        "age": 45,
        "gender": "Male",
        "key_facts": [],
        "report_summaries": [],
        "last_updated": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_chat_history_item():
    """Sample chat history item."""
    return {
        "user_id": "test-user-id",
        "chat_id": "chat-123",
        "query": "How do I treat a headache?",
        "response": "Here are some steps to help with headaches...",
        "topic": "Headache Treatment",
        "language": "English",
        "images": [],
        "step_images": [],
        "timestamp": 1703980800,
        "ttl": 1706659200
    }


# --- Mock Gemini Client ---

@pytest.fixture
def mock_gemini_response():
    """Sample response from Gemini API."""
    return {
        "answer": "Here are steps to treat a headache:\n\n**Step 1: Rest in a quiet, dark room**\nFind a comfortable place to lie down.\n\n**Step 2: Apply a cold compress**\nPlace a cold pack on your forehead.\n\n**Step 3: Stay hydrated**\nDrink plenty of water.",
        "steps": [
            {"step_number": "1", "title": "Rest in a quiet, dark room", "description": "Find a comfortable place to lie down."},
            {"step_number": "2", "title": "Apply a cold compress", "description": "Place a cold pack on your forehead."},
            {"step_number": "3", "title": "Stay hydrated", "description": "Drink plenty of water."}
        ]
    }


@pytest.fixture
def mock_gemini_client(mock_gemini_response):
    """Mock the Gemini client module."""
    with patch("gemini_client.get_medical_response") as mock_get_response:
        mock_get_response.return_value = (
            mock_gemini_response["answer"],
            mock_gemini_response["steps"],
            "Headache Treatment"
        )
        yield mock_get_response


# --- FastAPI Test Client ---

@pytest.fixture
def client():
    """FastAPI TestClient for endpoint testing."""
    # Import here to avoid circular imports with mocked env vars
    from api_server import app
    return TestClient(app)


@pytest.fixture
def authenticated_client(client, sample_user_info):
    """TestClient with mocked authentication."""
    with patch("api_server.get_user_info") as mock_auth:
        mock_auth.return_value = sample_user_info
        yield client


# --- Helper Functions ---

@pytest.fixture
def create_mock_dynamodb_response():
    """Factory fixture for creating DynamoDB responses."""
    def _create_response(items=None, count=0):
        return {
            "Items": items or [],
            "Count": count,
            "ScannedCount": count
        }
    return _create_response
