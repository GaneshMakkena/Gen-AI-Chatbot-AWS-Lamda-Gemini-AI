"""
Tests for model_router.py — Intelligent Model Routing.
"""

import pytest
from model_router import classify_query_complexity, get_model_for_query, FAST_MODEL, PRO_MODEL


class TestClassifyQueryComplexity:
    """Test query complexity classification."""

    @pytest.mark.parametrize("query", [
        "Hi",
        "Hello!",
        "Hey",
        "Good morning",
        "Thanks",
        "Bye",
        "What can you do?",
        "Ok",
    ])
    def test_greetings_are_simple(self, query):
        assert classify_query_complexity(query) == "simple"

    @pytest.mark.parametrize("query", [
        "x",
        "help",
        "cough?",
    ])
    def test_short_queries_are_simple(self, query):
        assert classify_query_complexity(query) == "simple"

    @pytest.mark.parametrize("query", [
        "I have multiple symptoms: headache, fever, and nausea. What could be the differential diagnosis?",
        "What are the contraindications for taking ibuprofen during pregnancy complication?",
        "Analyze this blood test report and tell me if there are any concerns.",
        "I need a treatment plan for chronic back pain with drug interaction checks.",
    ])
    def test_complex_queries(self, query):
        assert classify_query_complexity(query) == "complex"

    def test_attachments_always_complex(self):
        assert classify_query_complexity("What is this?", has_attachments=True) == "complex"

    def test_long_multi_sentence_query_is_complex(self):
        query = "I have been having headaches for the past 3 days. " \
                "They get worse in the morning. " \
                "I also feel dizzy sometimes. " \
                "What could be causing this?"
        assert classify_query_complexity(query) == "complex"


class TestGetModelForQuery:
    """Test model selection logic."""

    def test_simple_query_routes_to_fast_model(self):
        model = get_model_for_query("Hello!")
        assert model == FAST_MODEL

    def test_complex_query_routes_to_pro_model(self):
        model = get_model_for_query("What is the treatment plan for chronic diabetes with drug interaction risks?")
        assert model == PRO_MODEL

    def test_attachment_query_routes_to_pro_model(self):
        model = get_model_for_query("What is this?", has_attachments=True)
        assert model == PRO_MODEL
