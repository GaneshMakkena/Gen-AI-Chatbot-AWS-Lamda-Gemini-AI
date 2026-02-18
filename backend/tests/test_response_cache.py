"""
Tests for response_cache.py — DynamoDB-backed Response Cache.
"""

import pytest
from unittest.mock import patch, MagicMock
from response_cache import normalize_query, get_cache_key, get_cached_response, cache_response


class TestNormalizeQuery:
    """Test query normalization for consistent cache keys."""

    def test_lowercase(self):
        assert normalize_query("How To Treat A HEADACHE?") == "how to treat a headache"

    def test_strip_whitespace(self):
        assert normalize_query("  headache  ") == "headache"

    def test_collapse_whitespace(self):
        assert normalize_query("how  to   treat") == "how to treat"

    def test_strip_trailing_punctuation(self):
        assert normalize_query("headache???") == "headache"
        assert normalize_query("headache!!!") == "headache"
        assert normalize_query("headache...") == "headache"

    def test_same_query_different_format(self):
        """Same semantic query with different formatting should normalize identically."""
        q1 = normalize_query("How to treat a headache?")
        q2 = normalize_query("how to treat a headache")
        q3 = normalize_query("  How  to  treat  a  headache???  ")
        assert q1 == q2 == q3


class TestGetCacheKey:
    """Test cache key generation."""

    def test_consistent_keys(self):
        """Same query should always produce the same key."""
        key1 = get_cache_key("How to treat a headache?")
        key2 = get_cache_key("how to treat a headache")
        assert key1 == key2

    def test_different_queries_different_keys(self):
        key1 = get_cache_key("How to treat a headache?")
        key2 = get_cache_key("How to treat a burn?")
        assert key1 != key2

    def test_key_is_sha256_hex(self):
        key = get_cache_key("test query")
        assert len(key) == 64  # SHA-256 hex length
        assert all(c in "0123456789abcdef" for c in key)


class TestGetCachedResponse:
    """Test cache lookup."""

    @patch("response_cache.get_dynamodb_table")
    def test_cache_hit(self, mock_table_fn):
        import time
        mock_table = MagicMock()
        mock_table_fn.return_value = mock_table
        mock_table.get_item.return_value = {
            "Item": {
                "cache_key": "abc",
                "response": "Test response",
                "topic": "Headache",
                "timestamp": 1000,
                "ttl": int(time.time()) + 3600,
            }
        }
        result = get_cached_response("test query")
        assert result is not None
        assert result["response"] == "Test response"
        assert result["topic"] == "Headache"

    @patch("response_cache.get_dynamodb_table")
    def test_cache_miss(self, mock_table_fn):
        mock_table = MagicMock()
        mock_table_fn.return_value = mock_table
        mock_table.get_item.return_value = {}
        result = get_cached_response("unknown query")
        assert result is None

    @patch("response_cache.get_dynamodb_table")
    def test_expired_entry(self, mock_table_fn):
        mock_table = MagicMock()
        mock_table_fn.return_value = mock_table
        mock_table.get_item.return_value = {
            "Item": {
                "cache_key": "abc",
                "response": "Old response",
                "ttl": 1,  # Expired (epoch time = 1)
            }
        }
        result = get_cached_response("test query")
        assert result is None

    @patch("response_cache.get_dynamodb_table")
    def test_dynamo_error_returns_none(self, mock_table_fn):
        mock_table_fn.side_effect = Exception("DynamoDB error")
        result = get_cached_response("test query")
        assert result is None


class TestCacheResponse:
    """Test cache write."""

    @patch("response_cache.get_dynamodb_table")
    def test_stores_response(self, mock_table_fn):
        mock_table = MagicMock()
        mock_table_fn.return_value = mock_table

        cache_response("test query", "test response", topic="Test Topic")

        mock_table.put_item.assert_called_once()
        call_args = mock_table.put_item.call_args
        item = call_args[1]["Item"] if "Item" in call_args[1] else call_args[0][0]
        assert item["response"] == "test response"
        assert item["topic"] == "Test Topic"

    @patch("response_cache.get_dynamodb_table")
    def test_dynamo_error_does_not_raise(self, mock_table_fn):
        mock_table_fn.side_effect = Exception("Write error")
        # Should not raise
        cache_response("test query", "test response")
