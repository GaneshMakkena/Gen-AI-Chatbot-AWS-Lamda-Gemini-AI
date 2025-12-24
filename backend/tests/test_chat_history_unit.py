"""
Unit tests for chat_history.py - DynamoDB chat operations.
Tests CRUD operations with mocked DynamoDB.
"""

import pytest
import time
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError


class TestGenerateChatId:
    """Tests for chat ID generation."""

    def test_generate_chat_id_has_prefix(self):
        """Test that generated chat ID has correct prefix."""
        import chat_history

        chat_id = chat_history.generate_chat_id()

        assert chat_id.startswith("chat_")

    def test_generate_chat_id_is_unique(self):
        """Test that generated chat IDs are unique."""
        import chat_history

        ids = [chat_history.generate_chat_id() for _ in range(100)]

        assert len(ids) == len(set(ids))

    def test_generate_chat_id_contains_timestamp(self):
        """Test that chat ID contains timestamp component."""
        import chat_history

        before = int(time.time() * 1000)
        chat_id = chat_history.generate_chat_id()
        after = int(time.time() * 1000)

        # Extract timestamp from chat_1234567890123_abcd1234 format
        parts = chat_id.split("_")
        timestamp = int(parts[1])

        assert before <= timestamp <= after


class TestSaveChat:
    """Tests for save_chat function."""

    def test_save_chat_creates_item_with_required_fields(self):
        """Test that save_chat creates an item with all required fields."""
        import chat_history

        mock_table = MagicMock()

        with patch.object(chat_history, "get_table") as mock_get_table:
            mock_get_table.return_value = mock_table

            result = chat_history.save_chat(
                user_id="user-123",
                query="How to treat headache?",
                response="Here are some steps..."
            )

            mock_table.put_item.assert_called_once()
            item = mock_table.put_item.call_args[1]["Item"]

            assert item["user_id"] == "user-123"
            assert item["query"] == "How to treat headache?"
            assert item["response"] == "Here are some steps..."
            assert "chat_id" in item
            assert "timestamp" in item
            assert "ttl" in item
            assert "created_at" in item

    def test_save_chat_uses_provided_chat_id(self):
        """Test that save_chat uses provided chat_id if given."""
        import chat_history

        mock_table = MagicMock()

        with patch.object(chat_history, "get_table") as mock_get_table:
            mock_get_table.return_value = mock_table

            result = chat_history.save_chat(
                user_id="user-123",
                query="Test query",
                response="Test response",
                chat_id="custom-chat-id"
            )

            item = mock_table.put_item.call_args[1]["Item"]
            assert item["chat_id"] == "custom-chat-id"

    def test_save_chat_includes_optional_fields(self):
        """Test that save_chat includes optional fields when provided."""
        import chat_history

        mock_table = MagicMock()
        step_images = [{"step_number": "1", "title": "Step 1", "description": "Desc"}]
        attachments = [{"filename": "report.pdf", "s3_key": "key"}]

        with patch.object(chat_history, "get_table") as mock_get_table:
            mock_get_table.return_value = mock_table

            result = chat_history.save_chat(
                user_id="user-123",
                query="Test query",
                response="Test response",
                images=["http://image.url"],
                topic="Headache Treatment",
                language="Spanish",
                step_images=step_images,
                attachments=attachments
            )

            item = mock_table.put_item.call_args[1]["Item"]
            assert item["images"] == ["http://image.url"]
            assert item["topic"] == "Headache Treatment"
            assert item["language"] == "Spanish"
            assert item["step_images"] == step_images
            assert item["attachments"] == attachments

    def test_save_chat_sets_90_day_ttl(self):
        """Test that TTL is set to 90 days from now."""
        import chat_history

        mock_table = MagicMock()

        with patch.object(chat_history, "get_table") as mock_get_table:
            mock_get_table.return_value = mock_table

            before = int(time.time()) + (90 * 24 * 60 * 60) - 10
            result = chat_history.save_chat(
                user_id="user-123",
                query="Test",
                response="Test"
            )
            after = int(time.time()) + (90 * 24 * 60 * 60) + 10

            item = mock_table.put_item.call_args[1]["Item"]
            assert before <= item["ttl"] <= after

    def test_save_chat_handles_dynamodb_error(self):
        """Test that save_chat handles DynamoDB errors gracefully."""
        import chat_history

        mock_table = MagicMock()
        mock_table.put_item.side_effect = Exception("DynamoDB error")

        with patch.object(chat_history, "get_table") as mock_get_table:
            mock_get_table.return_value = mock_table

            # Should not raise, but return the item
            result = chat_history.save_chat(
                user_id="user-123",
                query="Test",
                response="Test"
            )

            assert result is not None
            assert result["query"] == "Test"


class TestGetChat:
    """Tests for get_chat function."""

    def test_get_chat_returns_item_when_found(self):
        """Test that get_chat returns the item when found."""
        import chat_history

        mock_item = {
            "user_id": "user-123",
            "chat_id": "chat-456",
            "query": "Test query",
            "response": "Test response"
        }
        mock_table = MagicMock()
        mock_table.get_item.return_value = {"Item": mock_item}

        with patch.object(chat_history, "get_table") as mock_get_table:
            mock_get_table.return_value = mock_table

            result = chat_history.get_chat("user-123", "chat-456")

            assert result == mock_item
            mock_table.get_item.assert_called_once_with(
                Key={"user_id": "user-123", "chat_id": "chat-456"}
            )

    def test_get_chat_returns_none_when_not_found(self):
        """Test that get_chat returns None when item not found."""
        import chat_history

        mock_table = MagicMock()
        mock_table.get_item.return_value = {}  # No Item key

        with patch.object(chat_history, "get_table") as mock_get_table:
            mock_get_table.return_value = mock_table

            result = chat_history.get_chat("user-123", "nonexistent")

            assert result is None

    def test_get_chat_handles_dynamodb_error(self):
        """Test that get_chat handles errors gracefully."""
        import chat_history

        mock_table = MagicMock()
        mock_table.get_item.side_effect = Exception("DynamoDB error")

        with patch.object(chat_history, "get_table") as mock_get_table:
            mock_get_table.return_value = mock_table

            result = chat_history.get_chat("user-123", "chat-456")

            assert result is None


class TestGetUserChats:
    """Tests for get_user_chats function."""

    def test_get_user_chats_returns_items(self):
        """Test that get_user_chats returns user's chat items."""
        import chat_history

        mock_items = [
            {"chat_id": "chat-1", "query": "Query 1"},
            {"chat_id": "chat-2", "query": "Query 2"}
        ]
        mock_table = MagicMock()
        mock_table.query.return_value = {"Items": mock_items, "Count": 2}

        with patch.object(chat_history, "get_table") as mock_get_table:
            mock_get_table.return_value = mock_table

            result = chat_history.get_user_chats("user-123")

            assert result["items"] == mock_items
            assert result["count"] == 2

    def test_get_user_chats_sorts_newest_first(self):
        """Test that chats are sorted newest first."""
        import chat_history

        mock_table = MagicMock()
        mock_table.query.return_value = {"Items": [], "Count": 0}

        with patch.object(chat_history, "get_table") as mock_get_table:
            mock_get_table.return_value = mock_table

            chat_history.get_user_chats("user-123")

            query_params = mock_table.query.call_args[1]
            assert query_params["ScanIndexForward"] is False

    def test_get_user_chats_respects_limit(self):
        """Test that get_user_chats respects the limit parameter."""
        import chat_history

        mock_table = MagicMock()
        mock_table.query.return_value = {"Items": [], "Count": 0}

        with patch.object(chat_history, "get_table") as mock_get_table:
            mock_get_table.return_value = mock_table

            chat_history.get_user_chats("user-123", limit=10)

            query_params = mock_table.query.call_args[1]
            assert query_params["Limit"] == 10

    def test_get_user_chats_includes_pagination_key(self):
        """Test that pagination key is included when present."""
        import chat_history

        mock_table = MagicMock()
        mock_table.query.return_value = {
            "Items": [],
            "Count": 0,
            "LastEvaluatedKey": {"user_id": "user-123", "chat_id": "chat-50"}
        }

        with patch.object(chat_history, "get_table") as mock_get_table:
            mock_get_table.return_value = mock_table

            result = chat_history.get_user_chats("user-123")

            assert "last_key" in result

    def test_get_user_chats_uses_pagination_key(self):
        """Test that pagination key is used when provided."""
        import chat_history

        mock_table = MagicMock()
        mock_table.query.return_value = {"Items": [], "Count": 0}
        last_key = {"user_id": "user-123", "chat_id": "chat-50"}

        with patch.object(chat_history, "get_table") as mock_get_table:
            mock_get_table.return_value = mock_table

            chat_history.get_user_chats("user-123", last_key=last_key)

            query_params = mock_table.query.call_args[1]
            assert query_params["ExclusiveStartKey"] == last_key


class TestDeleteChat:
    """Tests for delete_chat function."""

    def test_delete_chat_deletes_from_dynamodb(self):
        """Test that delete_chat removes item from DynamoDB."""
        import chat_history

        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            "Item": {"user_id": "user-123", "chat_id": "chat-456", "images": []}
        }

        with patch.object(chat_history, "get_table") as mock_get_table:
            mock_get_table.return_value = mock_table

            result = chat_history.delete_chat("user-123", "chat-456")

            assert result is True
            mock_table.delete_item.assert_called_once_with(
                Key={"user_id": "user-123", "chat_id": "chat-456"}
            )

    def test_delete_chat_deletes_s3_images(self):
        """Test that delete_chat also deletes associated S3 images."""
        import chat_history

        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            "Item": {
                "user_id": "user-123",
                "chat_id": "chat-456",
                "images": ["https://bucket.s3.amazonaws.com/image1.png"]
            }
        }

        with patch.object(chat_history, "get_table") as mock_get_table:
            mock_get_table.return_value = mock_table
            with patch.object(chat_history, "_delete_s3_images") as mock_delete_s3:
                mock_delete_s3.return_value = 1

                result = chat_history.delete_chat("user-123", "chat-456")

                assert result is True
                mock_delete_s3.assert_called_once_with(
                    ["https://bucket.s3.amazonaws.com/image1.png"]
                )

    def test_delete_chat_handles_error(self):
        """Test that delete_chat handles errors gracefully."""
        import chat_history

        mock_table = MagicMock()
        mock_table.get_item.side_effect = Exception("DynamoDB error")

        with patch.object(chat_history, "get_table") as mock_get_table:
            mock_get_table.return_value = mock_table

            result = chat_history.delete_chat("user-123", "chat-456")

            assert result is False


class TestGetChatSummary:
    """Tests for get_chat_summary function."""

    def test_get_chat_summary_returns_expected_fields(self):
        """Test that get_chat_summary returns expected fields."""
        import chat_history

        chat = {
            "chat_id": "chat-123",
            "query": "How do I treat a headache?",
            "topic": "Headache Treatment",
            "timestamp": 1703980800,
            "created_at": "2024-01-01T00:00:00Z",
            "images": ["http://image.url"]
        }

        result = chat_history.get_chat_summary(chat)

        assert result["chat_id"] == "chat-123"
        assert "How do I treat" in result["query"]
        assert result["topic"] == "Headache Treatment"
        assert result["timestamp"] == 1703980800
        assert result["has_images"] is True

    def test_get_chat_summary_truncates_long_query(self):
        """Test that long queries are truncated to 100 chars."""
        import chat_history

        long_query = "A" * 200
        chat = {
            "chat_id": "chat-123",
            "query": long_query,
            "topic": "",
            "timestamp": 0,
            "created_at": "",
            "images": []
        }

        result = chat_history.get_chat_summary(chat)

        assert len(result["query"]) == 100

    def test_get_chat_summary_handles_missing_fields(self):
        """Test that missing fields are handled with defaults."""
        import chat_history

        chat = {}

        result = chat_history.get_chat_summary(chat)

        assert result["chat_id"] == ""
        assert result["query"] == ""
        assert result["topic"] == ""
        assert result["has_images"] is False


class TestDeleteS3Images:
    """Tests for _delete_s3_images helper function."""

    def test_delete_s3_images_returns_zero_for_empty_list(self):
        """Test that 0 is returned for empty image list."""
        import chat_history

        result = chat_history._delete_s3_images([])

        assert result == 0

    def test_delete_s3_images_extracts_key_and_deletes(self):
        """Test that S3 keys are extracted and deleted."""
        import os
        import chat_history

        # Set dummy creds
        with patch.dict(os.environ, {
            "AWS_ACCESS_KEY_ID": "testing",
            "AWS_REGION": "us-east-1"
        }):
            mock_s3 = MagicMock()
            # Use s3:// format which has simpler parsing logic
            images = ["s3://medibot-images-test/images/test.png"]

            # Patch the boto3 module imported in chat_history
            with patch("chat_history.boto3") as mock_boto3:
                mock_boto3.client.return_value = mock_s3

                result = chat_history._delete_s3_images(images)

                # Verify client was created
                mock_boto3.client.assert_called()

                # Verify delete was called
                mock_s3.delete_object.assert_called_once()

                # Verify result
                assert result == 1

                # Verify result
                assert result == 1
