"""
Unit tests for guest_tracking.py - Guest session management.
Tests session creation, limit checking, and increment operations.
"""


from unittest.mock import patch, MagicMock
import time


class TestGenerateGuestId:
    """Tests for generate_guest_id function."""

    def test_generate_guest_id_has_prefix(self):
        """Test that guest ID has correct prefix."""
        import guest_tracking

        guest_id = guest_tracking.generate_guest_id("192.168.1.1")

        assert guest_id.startswith("guest_")

    def test_generate_guest_id_is_deterministic(self):
        """Test that same inputs produce same guest ID."""
        import guest_tracking

        id1 = guest_tracking.generate_guest_id("192.168.1.1", "Mozilla/5.0", "fp123")
        id2 = guest_tracking.generate_guest_id("192.168.1.1", "Mozilla/5.0", "fp123")

        assert id1 == id2

    def test_generate_guest_id_differs_for_different_ips(self):
        """Test that different IPs produce different guest IDs."""
        import guest_tracking

        id1 = guest_tracking.generate_guest_id("192.168.1.1")
        id2 = guest_tracking.generate_guest_id("192.168.1.2")

        assert id1 != id2


class TestGetGuestSession:
    """Tests for get_guest_session function."""

    def test_get_guest_session_returns_session(self):
        """Test that existing session is returned."""
        import guest_tracking

        mock_session = {
            "guest_id": "guest_abc123",
            "message_count": 2,
            "ttl": int(time.time()) + 3600
        }
        mock_table = MagicMock()
        mock_table.get_item.return_value = {"Item": mock_session}

        with patch.object(guest_tracking, "get_table") as mock_get_table:
            mock_get_table.return_value = mock_table

            result = guest_tracking.get_guest_session("guest_abc123")

            assert result == mock_session

    def test_get_guest_session_returns_none_for_missing(self):
        """Test that None is returned for non-existent session."""
        import guest_tracking

        mock_table = MagicMock()
        mock_table.get_item.return_value = {}

        with patch.object(guest_tracking, "get_table") as mock_get_table:
            mock_get_table.return_value = mock_table

            result = guest_tracking.get_guest_session("guest_nonexistent")

            assert result is None

    def test_get_guest_session_returns_none_for_expired(self):
        """Test that None is returned for expired session."""
        import guest_tracking

        mock_session = {
            "guest_id": "guest_expired",
            "ttl": int(time.time()) - 3600  # Expired 1 hour ago
        }
        mock_table = MagicMock()
        mock_table.get_item.return_value = {"Item": mock_session}

        with patch.object(guest_tracking, "get_table") as mock_get_table:
            mock_get_table.return_value = mock_table

            result = guest_tracking.get_guest_session("guest_expired")

            assert result is None


class TestCheckGuestLimit:
    """Tests for check_guest_limit function."""

    def test_check_guest_limit_allows_under_limit(self):
        """Test that guest under limit is allowed."""
        import guest_tracking

        mock_session = {
            "guest_id": "guest_abc",
            "message_count": 1,
            "ttl": int(time.time()) + 3600
        }

        with patch.object(guest_tracking, "get_or_create_session") as mock_get:
            mock_get.return_value = mock_session

            result = guest_tracking.check_guest_limit("192.168.1.1")

            assert result["allowed"] is True
            assert result["remaining"] == 2  # 3 - 1 = 2
            assert result["message_count"] == 1

    def test_check_guest_limit_blocks_at_limit(self):
        """Test that guest at limit is blocked."""
        import guest_tracking

        mock_session = {
            "guest_id": "guest_abc",
            "message_count": 3,  # At limit
            "ttl": int(time.time()) + 3600
        }

        with patch.object(guest_tracking, "get_or_create_session") as mock_get:
            mock_get.return_value = mock_session

            result = guest_tracking.check_guest_limit("192.168.1.1")

            assert result["allowed"] is False
            assert result["remaining"] == 0


class TestIncrementGuestMessage:
    """Tests for increment_guest_message function."""

    def test_increment_guest_message_increments_count(self):
        """Test that message count is incremented."""
        import guest_tracking

        mock_table = MagicMock()
        mock_table.update_item.return_value = {
            "Attributes": {
                "message_count": 2
            }
        }

        with patch.object(guest_tracking, "get_or_create_session"):
            with patch.object(guest_tracking, "get_table") as mock_get_table:
                mock_get_table.return_value = mock_table

                result = guest_tracking.increment_guest_message("192.168.1.1")

                assert result["message_count"] == 2
                assert result["remaining"] == 1  # 3 - 2 = 1
                mock_table.update_item.assert_called_once()

    def test_increment_guest_message_stores_query(self):
        """Test that truncated query is stored in message log."""
        import guest_tracking

        mock_table = MagicMock()
        mock_table.update_item.return_value = {"Attributes": {"message_count": 1}}

        long_query = "A" * 500

        with patch.object(guest_tracking, "get_or_create_session"):
            with patch.object(guest_tracking, "get_table") as mock_get_table:
                mock_get_table.return_value = mock_table

                guest_tracking.increment_guest_message("192.168.1.1", query=long_query)

                # Check that query was truncated to 200 chars
                call_args = mock_table.update_item.call_args
                msg_list = call_args[1]["ExpressionAttributeValues"][":msg"]
                assert len(msg_list[0]["query"]) == 200


class TestResetGuestSession:
    """Tests for reset_guest_session function."""

    def test_reset_guest_session_deletes_record(self):
        """Test that session is deleted."""
        import guest_tracking

        mock_table = MagicMock()

        with patch.object(guest_tracking, "get_table") as mock_get_table:
            mock_get_table.return_value = mock_table

            result = guest_tracking.reset_guest_session("guest_abc123")

            assert result is True
            mock_table.delete_item.assert_called_once_with(Key={"guest_id": "guest_abc123"})
