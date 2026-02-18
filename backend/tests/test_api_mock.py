import sys
import os
from fastapi.testclient import TestClient
from unittest.mock import patch

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_server import app  # noqa: E402

client = TestClient(app)

# Mock data
MOCK_LLM_RESPONSE = """
**Understanding Your Situation**
You have a minor cut.

**Step-by-Step Treatment Guide**

**Step 1: Clean the wound**
Wash with water.

**Step 2: Apply pressure**
Stop the bleeding.
"""

MOCK_STEPS = [
    {"step_number": "1", "title": "Clean the wound", "description": "Wash with water."},
    {"step_number": "2", "title": "Apply pressure", "description": "Stop the bleeding."}
]

MOCK_IMAGE_DATA = {
    "step_number": "1",
    "title": "Clean the wound",
    "description": "Wash with water.",
    "image": "base64_string",
    "image_url": "http://example.com/image.png"
}


@patch('routes.chat.detect_language')
@patch('routes.chat.translate_to_english')
@patch('routes.chat.translate_from_english')
@patch('routes.chat.check_output_safety')
@patch('routes.chat.increment_guest_message')
@patch('routes.chat.check_guest_limit')
@patch('routes.chat.log_guest_event')
@patch('routes.chat.invoke_llm')
@patch('routes.chat.extract_treatment_steps')
@patch('routes.chat.generate_all_step_images')
@patch('routes.chat.should_generate_images')
def test_chat_endpoint(
    mock_should,
    mock_gen_images,
    mock_extract,
    mock_invoke,
    mock_log_guest,
    mock_check_guest,
    mock_increment_guest,
    mock_output_safety,
    mock_trans_from,
    mock_trans_to,
    mock_detect
):
    # Setup mocks
    mock_detect.return_value = "en"
    mock_invoke.return_value = MOCK_LLM_RESPONSE
    mock_output_safety.return_value = (True, MOCK_LLM_RESPONSE, None)
    mock_should.return_value = True
    mock_extract.return_value = MOCK_STEPS
    mock_gen_images.return_value = [MOCK_IMAGE_DATA]
    mock_check_guest.return_value = {"allowed": True, "remaining": 2, "message_count": 0, "limit": 3, "guest_id": "guest_1"}
    mock_increment_guest.return_value = {"guest_id": "guest_1", "remaining": 2}

    # Test Request
    response = client.post("/chat", json={
        "query": "I have a cut",
        "language": "English",
        "generate_images": True
    })

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == MOCK_LLM_RESPONSE
    assert len(data["step_images"]) == 1
    assert data["step_images"][0]["title"] == "Clean the wound"
    assert data["original_query"] == "I have a cut"


@patch('routes.chat.invoke_llm')
@patch('routes.chat.check_output_safety')
@patch('routes.chat.increment_guest_message')
@patch('routes.chat.check_guest_limit')
@patch('routes.chat.log_guest_event')
def test_chat_endpoint_error(mock_log_guest, mock_check_guest, mock_increment_guest, mock_output_safety, mock_invoke):
    # Simulate LLM failure
    mock_invoke.return_value = None
    mock_output_safety.return_value = (True, "", None)
    mock_check_guest.return_value = {"allowed": True, "remaining": 2, "message_count": 0, "limit": 3, "guest_id": "guest_1"}
    mock_increment_guest.return_value = {"guest_id": "guest_1", "remaining": 2}

    response = client.post("/chat", json={
        "query": "Fail me"
    })

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to get response from AI"


def test_clean_llm_response():
    from gemini_client import clean_llm_response

    # Test standard cleaning
    raw = "<thinking>Thinking...</thinking>Here is the answer.<thinking>More thoughts</thinking>"
    cleaned = clean_llm_response(raw)
    assert cleaned == "Here is the answer."

    # Test with keep_thinking=True
    raw_thinking = "<thinking>My thought process</thinking>\nAnswer"
    cleaned_thinking = clean_llm_response(raw_thinking, keep_thinking=True)
    assert "**🧠 My Thinking Process:**" in cleaned_thinking
    assert "My thought process" in cleaned_thinking
