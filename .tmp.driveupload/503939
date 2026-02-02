"""
Unit tests for auth.py - Authentication module.
Tests JWT token verification with mocked Cognito JWKS.
"""

import pytest
import time
import json
from unittest.mock import patch, MagicMock
from jose import jwt


class TestGetJwks:
    """Tests for JWKS fetching and caching."""

    def test_get_jwks_fetches_from_url(self):
        """Test that JWKS is fetched from Cognito URL."""
        import auth
        auth._jwks_cache = {}  # Clear cache
        auth._jwks_cache_time = 0

        mock_jwks = {"keys": [{"kid": "test-key-id", "kty": "RSA"}]}

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps(mock_jwks).encode()
            mock_response.__enter__ = MagicMock(return_value=mock_response)
            mock_response.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_response

            result = auth.get_jwks()

            assert result == mock_jwks
            assert "keys" in result
            mock_urlopen.assert_called_once()

    def test_get_jwks_uses_cache_when_valid(self):
        """Test that cached JWKS is returned when not expired."""
        import auth
        mock_jwks = {"keys": [{"kid": "cached-key"}]}
        auth._jwks_cache = mock_jwks
        auth._jwks_cache_time = time.time()  # Fresh cache

        with patch("urllib.request.urlopen") as mock_urlopen:
            result = auth.get_jwks()

            assert result == mock_jwks
            mock_urlopen.assert_not_called()

    def test_get_jwks_refetches_when_cache_expired(self):
        """Test that JWKS is refetched when cache expires."""
        import auth
        auth._jwks_cache = {"keys": [{"kid": "old-key"}]}
        auth._jwks_cache_time = time.time() - 7200  # 2 hours ago (expired)

        new_jwks = {"keys": [{"kid": "new-key"}]}

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps(new_jwks).encode()
            mock_response.__enter__ = MagicMock(return_value=mock_response)
            mock_response.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_response

            result = auth.get_jwks()

            assert result == new_jwks
            mock_urlopen.assert_called_once()

    def test_get_jwks_returns_expired_cache_on_error(self):
        """Test that expired cache is returned when fetch fails."""
        import auth
        old_jwks = {"keys": [{"kid": "old-key"}]}
        auth._jwks_cache = old_jwks
        auth._jwks_cache_time = time.time() - 7200  # Expired

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = Exception("Network error")

            result = auth.get_jwks()

            assert result == old_jwks


class TestVerifyToken:
    """Tests for JWT token verification."""

    def test_verify_token_returns_none_for_empty_token(self):
        """Test that None is returned for empty token."""
        import auth
        result = auth.verify_token("")
        assert result is None

        result = auth.verify_token(None)
        assert result is None

    def test_verify_token_strips_bearer_prefix(self):
        """Test that Bearer prefix is correctly stripped."""
        import auth

        with patch.object(auth, "get_signing_key") as mock_get_key:
            mock_get_key.return_value = None

            # Call with Bearer prefix
            auth.verify_token("Bearer some-token")

            # Verify get_signing_key was called with token without prefix
            mock_get_key.assert_called_once_with("some-token")

    def test_verify_token_returns_none_when_no_signing_key(self):
        """Test that None is returned when signing key not found."""
        import auth

        with patch.object(auth, "get_signing_key") as mock_get_key:
            mock_get_key.return_value = None

            result = auth.verify_token("some-invalid-token")

            assert result is None

    def test_verify_token_returns_none_for_expired_token(self):
        """Test that None is returned for expired tokens."""
        import auth

        mock_key = {"kid": "test-key", "kty": "RSA", "n": "test", "e": "AQAB"}

        with patch.object(auth, "get_signing_key") as mock_get_key:
            mock_get_key.return_value = mock_key
            with patch("jose.jwt.decode") as mock_decode:
                mock_decode.side_effect = jwt.ExpiredSignatureError("Token expired")

                result = auth.verify_token("expired-token")

                assert result is None


class TestGetUserInfo:
    """Tests for user info extraction."""

    def test_get_user_info_returns_user_dict(self):
        """Test that user info is correctly extracted from claims."""
        import auth

        mock_claims = {
            "sub": "user-123",
            "email": "test@example.com",
            "name": "Test User"
        }

        with patch.object(auth, "verify_token") as mock_verify:
            mock_verify.return_value = mock_claims

            result = auth.get_user_info("valid-token")

            assert result == {
                "user_id": "user-123",
                "email": "test@example.com",
                "name": "Test User"
            }

    def test_get_user_info_uses_email_prefix_when_no_name(self):
        """Test that email prefix is used when name is missing."""
        import auth

        mock_claims = {
            "sub": "user-456",
            "email": "john.doe@example.com"
        }

        with patch.object(auth, "verify_token") as mock_verify:
            mock_verify.return_value = mock_claims

            result = auth.get_user_info("valid-token")

            assert result["name"] == "john.doe"

    def test_get_user_info_returns_none_for_invalid_token(self):
        """Test that None is returned for invalid tokens."""
        import auth

        with patch.object(auth, "verify_token") as mock_verify:
            mock_verify.return_value = None

            result = auth.get_user_info("invalid-token")

            assert result is None


class TestGetUserId:
    """Tests for user ID extraction."""

    def test_get_user_id_returns_sub_claim(self):
        """Test that user ID (sub) is correctly extracted."""
        import auth

        mock_claims = {"sub": "user-789", "email": "test@example.com"}

        with patch.object(auth, "verify_token") as mock_verify:
            mock_verify.return_value = mock_claims

            result = auth.get_user_id("valid-token")

            assert result == "user-789"

    def test_get_user_id_returns_none_for_invalid_token(self):
        """Test that None is returned for invalid tokens."""
        import auth

        with patch.object(auth, "verify_token") as mock_verify:
            mock_verify.return_value = None

            result = auth.get_user_id("invalid-token")

            assert result is None


class TestRequireAuth:
    """Tests for authentication requirement dependency."""

    def test_require_auth_raises_on_missing_authorization(self):
        """Test that 401 is raised when no authorization header."""
        import auth
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            auth.require_auth(None)

        assert exc_info.value.status_code == 401
        assert "Authorization required" in str(exc_info.value.detail)

    def test_require_auth_raises_on_invalid_token(self):
        """Test that 401 is raised for invalid token."""
        import auth
        from fastapi import HTTPException

        with patch.object(auth, "get_user_info") as mock_get_user:
            mock_get_user.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                auth.require_auth("invalid-token")

            assert exc_info.value.status_code == 401
            assert "Invalid or expired" in str(exc_info.value.detail)

    def test_require_auth_returns_user_for_valid_token(self):
        """Test that user info is returned for valid token."""
        import auth

        mock_user = {"user_id": "user-123", "email": "test@example.com", "name": "Test"}

        with patch.object(auth, "get_user_info") as mock_get_user:
            mock_get_user.return_value = mock_user

            result = auth.require_auth("valid-token")

            assert result == mock_user


class TestGetOptionalUser:
    """Tests for optional user extraction."""

    def test_get_optional_user_returns_none_for_no_auth(self):
        """Test that None is returned when no authorization."""
        import auth

        result = auth.get_optional_user(None)

        assert result is None

    def test_get_optional_user_returns_user_for_valid_auth(self):
        """Test that user info is returned for valid authorization."""
        import auth

        mock_user = {"user_id": "user-123", "email": "test@example.com", "name": "Test"}

        with patch.object(auth, "get_user_info") as mock_get_user:
            mock_get_user.return_value = mock_user

            result = auth.get_optional_user("Bearer valid-token")

            assert result == mock_user
