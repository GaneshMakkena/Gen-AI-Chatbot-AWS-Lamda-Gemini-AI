"""
Tests for SSE streaming endpoint and invoke_llm_streaming.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient


class TestInvokeLlmStreaming:
    """Test the streaming LLM generator."""

    @patch("gemini_client.client")
    def test_yields_text_chunks(self, mock_client):
        """Test that streaming yields chunks of text."""
        from gemini_client import invoke_llm_streaming

        # Mock the streaming response
        chunk1 = MagicMock()
        chunk1.text = "Hello "
        chunk2 = MagicMock()
        chunk2.text = "world!"
        mock_client.models.generate_content_stream.return_value = [chunk1, chunk2]

        chunks = list(invoke_llm_streaming("test query"))
        assert chunks == ["Hello ", "world!"]

    @patch("gemini_client.client", None)
    def test_returns_empty_when_no_client(self):
        """Test that streaming returns nothing when client is not initialized."""
        from gemini_client import invoke_llm_streaming
        chunks = list(invoke_llm_streaming("test query"))
        assert chunks == []

    @patch("gemini_client.client")
    def test_handles_exception_gracefully(self, mock_client):
        """Test that streaming handles errors without crashing."""
        from gemini_client import invoke_llm_streaming
        mock_client.models.generate_content_stream.side_effect = Exception("API error")

        chunks = list(invoke_llm_streaming("test query"))
        assert chunks == []


class TestStreamingEndpoint:
    """Test the /chat/stream SSE endpoint."""

    @patch("routes.chat.invoke_llm_streaming")
    @patch("routes.chat.check_input_safety")
    @patch("routes.chat.detect_language")
    @patch("routes.chat.get_model_for_query")
    @patch("routes.chat.get_cached_response")
    @patch("routes.chat.check_output_safety")
    @patch("routes.chat.detect_medical_topic")
    @patch("routes.chat.should_generate_images")
    def test_stream_returns_event_stream(
        self, mock_should_gen, mock_topic, mock_output_safe,
        mock_cache, mock_model, mock_lang, mock_input_safe, mock_streaming
    ):
        """Test that /chat/stream returns text/event-stream content type."""
        from api_server import app
        client = TestClient(app)

        mock_input_safe.return_value = (True, "test query", None)
        mock_lang.return_value = "en"
        mock_model.return_value = "gemini-2.0-flash"
        mock_cache.return_value = None

        chunk = MagicMock()
        chunk.text = "Hello"
        mock_streaming.return_value = iter(["Hello ", "world!"])
        mock_output_safe.return_value = (True, "Hello world!", None)
        mock_topic.return_value = "General"
        mock_should_gen.return_value = False

        response = client.post(
            "/chat/stream",
            json={"query": "test query", "generate_images": False}
        )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

    @patch("routes.chat.check_input_safety")
    def test_stream_rejects_unsafe_input(self, mock_input_safe):
        """Test that unsafe input gets blocked."""
        from api_server import app
        client = TestClient(app)

        mock_input_safe.return_value = (False, "test", "Input blocked")

        response = client.post(
            "/chat/stream",
            json={"query": "unsafe input", "generate_images": False}
        )
        assert response.status_code == 200
        body = response.text
        assert "error" in body

    def test_stream_rejects_empty_query(self):
        """Test that empty queries return 400."""
        from api_server import app
        client = TestClient(app)

        response = client.post(
            "/chat/stream",
            json={"query": "", "generate_images": False}
        )
        assert response.status_code == 400


class TestImageBudgeting:
    """Test dynamic image budget calculation."""

    def test_full_budget_with_no_elapsed_time(self):
        from gemini_client import calculate_image_budget
        budget = calculate_image_budget(total_steps=5, elapsed_seconds=0)
        assert budget >= 5

    def test_reduced_budget_with_elapsed_time(self):
        from gemini_client import calculate_image_budget
        # 250s elapsed → 300-250-60 = -10 remaining → budget = 0
        budget = calculate_image_budget(total_steps=10, elapsed_seconds=250)
        assert budget < 10

    def test_zero_budget_when_no_time_left(self):
        from gemini_client import calculate_image_budget
        budget = calculate_image_budget(total_steps=5, elapsed_seconds=280)
        assert budget == 0

    def test_cap_at_10(self):
        from gemini_client import calculate_image_budget
        budget = calculate_image_budget(total_steps=20, elapsed_seconds=0)
        assert budget <= 10


class TestPrioritizeSteps:
    """Test step prioritization logic."""

    def test_returns_all_when_budget_sufficient(self):
        from gemini_client import prioritize_steps
        steps = [{"title": f"Step {i}", "description": ""} for i in range(3)]
        result = prioritize_steps(steps, budget=5)
        assert len(result) == 3

    def test_includes_first_and_last(self):
        from gemini_client import prioritize_steps
        steps = [{"title": f"Step {i}", "description": ""} for i in range(5)]
        result = prioritize_steps(steps, budget=2)
        assert len(result) == 2
        assert result[0]["title"] == "Step 0"
        assert result[-1]["title"] == "Step 4"

    def test_prioritizes_safety_keywords(self):
        from gemini_client import prioritize_steps
        steps = [
            {"title": "Step 0", "description": "Start here"},
            {"title": "Step 1", "description": "This is dangerous, avoid this"},
            {"title": "Step 2", "description": "Normal step"},
            {"title": "Step 3", "description": "Warning: be careful"},
            {"title": "Step 4", "description": "End here"},
        ]
        result = prioritize_steps(steps, budget=3)
        titles = [s["title"] for s in result]
        # First and last always included
        assert "Step 0" in titles
        assert "Step 4" in titles
        # Safety-keyword step should be preferred
        assert "Step 1" in titles or "Step 3" in titles

    def test_empty_budget_returns_empty(self):
        from gemini_client import prioritize_steps
        steps = [{"title": "Step", "description": ""}]
        assert prioritize_steps(steps, budget=0) == []
