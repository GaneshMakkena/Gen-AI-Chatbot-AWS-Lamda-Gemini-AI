"""
Unit tests for audit_logging.py - Audit event logging.
Tests event logging, helper functions, and event types.
"""

from unittest.mock import patch, MagicMock
import time


class TestLogEvent:
    """Tests for log_event function."""

    def test_log_event_creates_event_id(self):
        """Test that event ID is generated correctly."""
        import audit_logging

        mock_table = MagicMock()

        with patch.object(audit_logging, "get_table") as mock_get_table:
            mock_get_table.return_value = mock_table

            result = audit_logging.log_event(
                event_type=audit_logging.AuditEvent.CHAT_CREATE,
                user_id="user-123"
            )

            assert result is not None
            assert result.startswith("evt_")
            mock_table.put_item.assert_called_once()

    def test_log_event_includes_required_fields(self):
        """Test that event includes all required fields."""
        import audit_logging

        mock_table = MagicMock()

        with patch.object(audit_logging, "get_table") as mock_get_table:
            mock_get_table.return_value = mock_table

            audit_logging.log_event(
                event_type=audit_logging.AuditEvent.PROFILE_READ,
                user_id="user-123",
                resource_id="profile-123",
                ip_address="192.168.1.1"
            )

            call_args = mock_table.put_item.call_args
            item = call_args[1]["Item"]

            assert "event_id" in item
            assert "timestamp" in item
            assert "ttl" in item
            assert item["event_type"] == audit_logging.AuditEvent.PROFILE_READ
            assert item["user_id"] == "user-123"
            assert item["resource_id"] == "profile-123"
            assert item["ip_address"] == "192.168.1.1"

    def test_log_event_sets_ttl(self):
        """Test that TTL is set based on retention policy."""
        import audit_logging

        mock_table = MagicMock()

        with patch.object(audit_logging, "get_table") as mock_get_table:
            mock_get_table.return_value = mock_table

            before = int(time.time())
            audit_logging.log_event(event_type=audit_logging.AuditEvent.CHAT_READ)

            call_args = mock_table.put_item.call_args
            item = call_args[1]["Item"]

            # TTL should be ~90 days in the future
            expected_ttl_min = before + (89 * 24 * 60 * 60)
            expected_ttl_max = before + (91 * 24 * 60 * 60)

            assert expected_ttl_min < item["ttl"] < expected_ttl_max

    def test_log_event_truncates_long_user_agent(self):
        """Test that long user agent is truncated."""
        import audit_logging

        mock_table = MagicMock()
        long_ua = "A" * 1000

        with patch.object(audit_logging, "get_table") as mock_get_table:
            mock_get_table.return_value = mock_table

            audit_logging.log_event(
                event_type=audit_logging.AuditEvent.LOGIN_SUCCESS,
                user_agent=long_ua
            )

            call_args = mock_table.put_item.call_args
            item = call_args[1]["Item"]

            assert len(item["user_agent"]) == 500

    def test_log_event_handles_error(self):
        """Test that errors return None without raising."""
        import audit_logging

        mock_table = MagicMock()
        mock_table.put_item.side_effect = Exception("DynamoDB error")

        with patch.object(audit_logging, "get_table") as mock_get_table:
            mock_get_table.return_value = mock_table

            result = audit_logging.log_event(event_type=audit_logging.AuditEvent.CHAT_READ)

            assert result is None


class TestLogChatAccess:
    """Tests for log_chat_access helper."""

    def test_log_chat_access_maps_actions(self):
        """Test that action strings map to correct event types."""
        import audit_logging

        with patch.object(audit_logging, "log_event") as mock_log:
            mock_log.return_value = "evt_123"

            audit_logging.log_chat_access("user-1", "chat-1", action="read")
            mock_log.assert_called_with(
                event_type=audit_logging.AuditEvent.CHAT_READ,
                user_id="user-1",
                resource_id="chat-1",
                resource_type="chat",
                ip_address=None
            )


class TestLogProfileAccess:
    """Tests for log_profile_access helper."""

    def test_log_profile_access_includes_changes(self):
        """Test that profile changes are included in details."""
        import audit_logging

        changes = {"conditions": ["added Diabetes"]}

        with patch.object(audit_logging, "log_event") as mock_log:
            mock_log.return_value = "evt_123"

            audit_logging.log_profile_access(
                "user-1",
                action="update",
                changes=changes
            )

            call_args = mock_log.call_args
            assert call_args[1]["details"] == {"changes": changes}


class TestLogGuestEvent:
    """Tests for log_guest_event helper."""

    def test_log_guest_event_prefixes_user_id(self):
        """Test that guest ID is prefixed in user_id field."""
        import audit_logging

        with patch.object(audit_logging, "log_event") as mock_log:
            mock_log.return_value = "evt_123"

            audit_logging.log_guest_event(
                guest_id="abc123",
                ip_address="192.168.1.1",
                action="chat"
            )

            call_args = mock_log.call_args
            assert call_args[1]["user_id"] == "guest:abc123"


class TestLogSecurityEvent:
    """Tests for log_security_event helper."""

    def test_log_security_event_defaults_to_warning(self):
        """Test that security events default to warning severity."""
        import audit_logging

        with patch.object(audit_logging, "log_event") as mock_log:
            mock_log.return_value = "evt_123"

            audit_logging.log_security_event(
                event_type=audit_logging.AuditEvent.RATE_LIMIT_HIT,
                ip_address="192.168.1.1"
            )

            call_args = mock_log.call_args
            assert call_args[1]["severity"] == "warning"


class TestAuditEventTypes:
    """Tests for AuditEvent constant class."""

    def test_audit_event_types_exist(self):
        """Test that required event types are defined."""
        import audit_logging

        assert hasattr(audit_logging.AuditEvent, "LOGIN_SUCCESS")
        assert hasattr(audit_logging.AuditEvent, "CHAT_CREATE")
        assert hasattr(audit_logging.AuditEvent, "PROFILE_UPDATE")
        assert hasattr(audit_logging.AuditEvent, "GUEST_LIMIT_REACHED")
        assert hasattr(audit_logging.AuditEvent, "RATE_LIMIT_HIT")

    def test_audit_event_types_are_strings(self):
        """Test that event types are string constants."""
        import audit_logging

        assert isinstance(audit_logging.AuditEvent.LOGIN_SUCCESS, str)
        assert "." in audit_logging.AuditEvent.LOGIN_SUCCESS  # Dotted notation
