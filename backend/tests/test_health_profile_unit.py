"""
Unit tests for health_profile.py - Health profile management.
Tests CRUD operations with mocked DynamoDB.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


class TestGetHealthProfile:
    """Tests for get_health_profile function."""

    def test_get_health_profile_returns_item_when_found(self):
        """Test that profile is returned when found."""
        import health_profile

        mock_item = {
            "user_id": "user-123",
            "conditions": [{"name": "Diabetes"}],
            "medications": [],
            "allergies": []
        }
        mock_table = MagicMock()
        mock_table.get_item.return_value = {"Item": mock_item}

        with patch.object(health_profile, "get_table") as mock_get_table:
            mock_get_table.return_value = mock_table

            result = health_profile.get_health_profile("user-123")

            assert result == mock_item

    def test_get_health_profile_returns_none_when_not_found(self):
        """Test that None is returned when profile doesn't exist."""
        import health_profile

        mock_table = MagicMock()
        mock_table.get_item.return_value = {}

        with patch.object(health_profile, "get_table") as mock_get_table:
            mock_get_table.return_value = mock_table

            result = health_profile.get_health_profile("user-123")

            assert result is None

    def test_get_health_profile_handles_error(self):
        """Test that errors are handled gracefully."""
        import health_profile

        mock_table = MagicMock()
        mock_table.get_item.side_effect = Exception("DynamoDB error")

        with patch.object(health_profile, "get_table") as mock_get_table:
            mock_get_table.return_value = mock_table

            result = health_profile.get_health_profile("user-123")

            assert result is None


class TestCreateHealthProfile:
    """Tests for create_health_profile function."""

    def test_create_health_profile_creates_with_required_fields(self):
        """Test that profile is created with all required fields."""
        import health_profile

        mock_table = MagicMock()

        with patch.object(health_profile, "get_table") as mock_get_table:
            mock_get_table.return_value = mock_table

            result = health_profile.create_health_profile("user-123")

            mock_table.put_item.assert_called_once()
            item = mock_table.put_item.call_args[1]["Item"]

            assert item["user_id"] == "user-123"
            assert item["conditions"] == []
            assert item["medications"] == []
            assert item["allergies"] == []
            assert "created_at" in item
            assert "last_updated" in item

    def test_create_health_profile_returns_profile_on_error(self):
        """Test that profile is returned even on DynamoDB error."""
        import health_profile

        mock_table = MagicMock()
        mock_table.put_item.side_effect = Exception("DynamoDB error")

        with patch.object(health_profile, "get_table") as mock_get_table:
            mock_get_table.return_value = mock_table

            result = health_profile.create_health_profile("user-123")

            assert result is not None
            assert result["user_id"] == "user-123"


class TestGetOrCreateProfile:
    """Tests for get_or_create_profile function."""

    def test_get_or_create_profile_returns_existing(self):
        """Test that existing profile is returned."""
        import health_profile

        existing_profile = {"user_id": "user-123", "conditions": [{"name": "Diabetes"}]}

        with patch.object(health_profile, "get_health_profile") as mock_get:
            mock_get.return_value = existing_profile

            result = health_profile.get_or_create_profile("user-123")

            assert result == existing_profile

    def test_get_or_create_profile_creates_when_missing(self):
        """Test that new profile is created when not found."""
        import health_profile

        with patch.object(health_profile, "get_health_profile") as mock_get:
            mock_get.return_value = None
            with patch.object(health_profile, "create_health_profile") as mock_create:
                mock_create.return_value = {"user_id": "user-123", "conditions": []}

                result = health_profile.get_or_create_profile("user-123")

                mock_create.assert_called_once_with("user-123")


class TestAddCondition:
    """Tests for add_condition function."""

    def test_add_condition_adds_new_condition(self):
        """Test that new condition is added."""
        import health_profile

        mock_table = MagicMock()

        with patch.object(health_profile, "get_or_create_profile") as mock_get:
            mock_get.return_value = {"user_id": "user-123", "conditions": []}
            with patch.object(health_profile, "get_table") as mock_get_table:
                mock_get_table.return_value = mock_table

                result = health_profile.add_condition("user-123", "Diabetes")

                assert result is True
                mock_table.update_item.assert_called_once()

    def test_add_condition_skips_duplicate(self):
        """Test that duplicate conditions are not added."""
        import health_profile

        with patch.object(health_profile, "get_or_create_profile") as mock_get:
            mock_get.return_value = {
                "user_id": "user-123",
                "conditions": [{"name": "Diabetes"}]
            }

            result = health_profile.add_condition("user-123", "diabetes")  # Case-insensitive

            assert result is True

    def test_add_condition_handles_error(self):
        """Test that errors return False."""
        import health_profile

        mock_table = MagicMock()
        mock_table.update_item.side_effect = Exception("DynamoDB error")

        with patch.object(health_profile, "get_or_create_profile") as mock_get:
            mock_get.return_value = {"user_id": "user-123", "conditions": []}
            with patch.object(health_profile, "get_table") as mock_get_table:
                mock_get_table.return_value = mock_table

                result = health_profile.add_condition("user-123", "Diabetes")

                assert result is False


class TestAddMedication:
    """Tests for add_medication function."""

    def test_add_medication_adds_with_dosage(self):
        """Test that medication with dosage is added."""
        import health_profile

        mock_table = MagicMock()

        with patch.object(health_profile, "get_or_create_profile") as mock_get:
            mock_get.return_value = {"user_id": "user-123", "medications": []}
            with patch.object(health_profile, "get_table") as mock_get_table:
                mock_get_table.return_value = mock_table

                result = health_profile.add_medication("user-123", "Metformin", "500mg")

                assert result is True
                call_args = mock_table.update_item.call_args[1]
                new_med = call_args["ExpressionAttributeValues"][":new"][0]
                assert new_med["name"] == "Metformin"
                assert new_med["dosage"] == "500mg"

    def test_add_medication_skips_duplicate(self):
        """Test that duplicate medications are not added."""
        import health_profile

        with patch.object(health_profile, "get_or_create_profile") as mock_get:
            mock_get.return_value = {
                "user_id": "user-123",
                "medications": [{"name": "Metformin", "dosage": "500mg"}]
            }

            result = health_profile.add_medication("user-123", "METFORMIN")

            assert result is True


class TestAddAllergy:
    """Tests for add_allergy function."""

    def test_add_allergy_adds_new_allergy(self):
        """Test that new allergy is added."""
        import health_profile

        mock_table = MagicMock()

        with patch.object(health_profile, "get_or_create_profile") as mock_get:
            mock_get.return_value = {"user_id": "user-123", "allergies": []}
            with patch.object(health_profile, "get_table") as mock_get_table:
                mock_get_table.return_value = mock_table

                result = health_profile.add_allergy("user-123", "Penicillin")

                assert result is True

    def test_add_allergy_skips_duplicate(self):
        """Test that duplicate allergies are not added."""
        import health_profile

        with patch.object(health_profile, "get_or_create_profile") as mock_get:
            mock_get.return_value = {
                "user_id": "user-123",
                "allergies": [{"name": "Penicillin"}]
            }

            result = health_profile.add_allergy("user-123", "penicillin")

            assert result is True


class TestGetContextSummary:
    """Tests for get_context_summary function."""

    def test_get_context_summary_returns_empty_for_no_profile(self):
        """Test that empty string is returned when no profile exists."""
        import health_profile

        with patch.object(health_profile, "get_health_profile") as mock_get:
            mock_get.return_value = None

            result = health_profile.get_context_summary("user-123")

            assert result == ""

    def test_get_context_summary_includes_conditions(self):
        """Test that conditions are included in summary."""
        import health_profile

        with patch.object(health_profile, "get_health_profile") as mock_get:
            mock_get.return_value = {
                "user_id": "user-123",
                "conditions": [{"name": "Diabetes"}, {"name": "Hypertension"}],
                "medications": [],
                "allergies": []
            }

            result = health_profile.get_context_summary("user-123")

            assert "Diabetes" in result
            assert "Hypertension" in result
            assert "Medical conditions" in result

    def test_get_context_summary_includes_medications(self):
        """Test that medications are included in summary."""
        import health_profile

        with patch.object(health_profile, "get_health_profile") as mock_get:
            mock_get.return_value = {
                "user_id": "user-123",
                "conditions": [],
                "medications": [{"name": "Metformin", "dosage": "500mg"}],
                "allergies": []
            }

            result = health_profile.get_context_summary("user-123")

            assert "Metformin" in result
            assert "500mg" in result

    def test_get_context_summary_includes_allergies(self):
        """Test that allergies are included in summary."""
        import health_profile

        with patch.object(health_profile, "get_health_profile") as mock_get:
            mock_get.return_value = {
                "user_id": "user-123",
                "conditions": [],
                "medications": [],
                "allergies": [{"name": "Penicillin"}]
            }

            result = health_profile.get_context_summary("user-123")

            assert "Penicillin" in result
            assert "allergies" in result

    def test_get_context_summary_returns_empty_for_empty_profile(self):
        """Test that empty string is returned for profile with no data."""
        import health_profile

        with patch.object(health_profile, "get_health_profile") as mock_get:
            mock_get.return_value = {
                "user_id": "user-123",
                "conditions": [],
                "medications": [],
                "allergies": []
            }

            result = health_profile.get_context_summary("user-123")

            assert result == ""


class TestDeleteHealthProfile:
    """Tests for delete_health_profile function."""

    def test_delete_health_profile_deletes_item(self):
        """Test that profile is deleted."""
        import health_profile

        mock_table = MagicMock()

        with patch.object(health_profile, "get_table") as mock_get_table:
            mock_get_table.return_value = mock_table

            result = health_profile.delete_health_profile("user-123")

            assert result is True
            mock_table.delete_item.assert_called_once_with(Key={"user_id": "user-123"})

    def test_delete_health_profile_handles_error(self):
        """Test that errors return False."""
        import health_profile

        mock_table = MagicMock()
        mock_table.delete_item.side_effect = Exception("DynamoDB error")

        with patch.object(health_profile, "get_table") as mock_get_table:
            mock_get_table.return_value = mock_table

            result = health_profile.delete_health_profile("user-123")

            assert result is False


class TestRemoveCondition:
    """Tests for remove_condition function."""

    def test_remove_condition_removes_existing(self):
        """Test that existing condition is removed."""
        import health_profile

        mock_table = MagicMock()

        with patch.object(health_profile, "get_health_profile") as mock_get:
            mock_get.return_value = {
                "user_id": "user-123",
                "conditions": [{"name": "Diabetes"}, {"name": "Hypertension"}]
            }
            with patch.object(health_profile, "get_table") as mock_get_table:
                mock_get_table.return_value = mock_table

                result = health_profile.remove_condition("user-123", "Diabetes")

                assert result is True
                call_args = mock_table.update_item.call_args[1]
                updated_conditions = call_args["ExpressionAttributeValues"][":conditions"]
                assert len(updated_conditions) == 1
                assert updated_conditions[0]["name"] == "Hypertension"

    def test_remove_condition_returns_false_when_not_found(self):
        """Test that False is returned when condition not found."""
        import health_profile

        with patch.object(health_profile, "get_health_profile") as mock_get:
            mock_get.return_value = {
                "user_id": "user-123",
                "conditions": [{"name": "Diabetes"}]
            }

            result = health_profile.remove_condition("user-123", "NonexistentCondition")

            assert result is False

    def test_remove_condition_returns_false_when_no_profile(self):
        """Test that False is returned when profile doesn't exist."""
        import health_profile

        with patch.object(health_profile, "get_health_profile") as mock_get:
            mock_get.return_value = None

            result = health_profile.remove_condition("user-123", "Diabetes")

            assert result is False
