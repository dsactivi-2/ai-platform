"""Unit tests for auth utility module."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from lyzr_kit.utils.auth import (
    ENV_MEMBERSTACK_TOKEN,
    ENV_USER_ID,
    ENV_VAR_NAME,
    AuthConfig,
    AuthError,
    get_api_headers,
    load_auth,
    require_auth,
    validate_auth,
)


class TestAuthConfig:
    """Tests for AuthConfig dataclass."""

    def test_auth_config_with_defaults(self):
        """AuthConfig should have default base_url."""
        config = AuthConfig(api_key="test-key")
        assert config.api_key == "test-key"
        assert config.base_url == "https://agent-prod.studio.lyzr.ai"

    def test_auth_config_custom_base_url(self):
        """AuthConfig should accept custom base_url."""
        config = AuthConfig(api_key="test-key", base_url="https://custom.api.com")
        assert config.base_url == "https://custom.api.com"


class TestLoadAuth:
    """Tests for load_auth function."""

    @pytest.fixture(autouse=True)
    def clear_env_vars(self):
        """Clear environment variables before each test to ensure isolation."""
        # Save any existing values
        saved_api_key = os.environ.pop(ENV_VAR_NAME, None)
        saved_user_id = os.environ.pop(ENV_USER_ID, None)
        saved_token = os.environ.pop(ENV_MEMBERSTACK_TOKEN, None)

        yield

        # Restore original values if they existed
        if saved_api_key is not None:
            os.environ[ENV_VAR_NAME] = saved_api_key
        if saved_user_id is not None:
            os.environ[ENV_USER_ID] = saved_user_id
        if saved_token is not None:
            os.environ[ENV_MEMBERSTACK_TOKEN] = saved_token

    def test_load_auth_missing_env_file(self):
        """load_auth should raise AuthError if .env missing."""
        # Temporarily remove .env if it exists (sandbox may have one)
        env_file = Path.cwd() / ".env"
        env_backup = Path.cwd() / ".env.backup"
        had_env = env_file.exists()
        if had_env:
            env_file.rename(env_backup)

        try:
            with pytest.raises(AuthError) as exc_info:
                load_auth()
            assert "Authentication required" in str(exc_info.value)
            assert "lk auth" in str(exc_info.value)
        finally:
            # Restore .env if it existed
            if had_env and env_backup.exists():
                env_backup.rename(env_file)

    def test_load_auth_missing_api_key(self):
        """load_auth should raise AuthError if LYZR_API_KEY missing."""
        env_file = Path.cwd() / ".env"
        env_file.write_text("OTHER_VAR=value\n")

        with pytest.raises(AuthError) as exc_info:
            load_auth()
        assert "LYZR_API_KEY" in str(exc_info.value)

    def test_load_auth_success(self):
        """load_auth should return AuthConfig with API key."""
        env_file = Path.cwd() / ".env"
        env_file.write_text("LYZR_API_KEY=my-test-key\n")

        config = load_auth()
        assert config.api_key == "my-test-key"
        assert config.base_url == "https://agent-prod.studio.lyzr.ai"


class TestValidateAuth:
    """Tests for validate_auth function."""

    @patch("lyzr_kit.utils.auth.httpx.get")
    def test_validate_auth_success(self, mock_get):
        """validate_auth should return True for valid credentials."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        config = AuthConfig(api_key="valid-key")
        assert validate_auth(config) is True

        # Verify correct headers were sent
        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs["headers"]["x-api-key"] == "valid-key"

    @patch("lyzr_kit.utils.auth.httpx.get")
    def test_validate_auth_invalid_key(self, mock_get):
        """validate_auth should raise AuthError for 401."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        config = AuthConfig(api_key="invalid-key")
        with pytest.raises(AuthError) as exc_info:
            validate_auth(config)
        assert "Invalid API key" in str(exc_info.value)

    @patch("lyzr_kit.utils.auth.httpx.get")
    def test_validate_auth_forbidden(self, mock_get):
        """validate_auth should raise AuthError for 403."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response

        config = AuthConfig(api_key="expired-key")
        with pytest.raises(AuthError) as exc_info:
            validate_auth(config)
        assert "forbidden" in str(exc_info.value).lower()

    @patch("lyzr_kit.utils.auth.httpx.get")
    def test_validate_auth_connection_error(self, mock_get):
        """validate_auth should raise AuthError on connection failure."""
        import httpx

        mock_get.side_effect = httpx.ConnectError("Connection refused")

        config = AuthConfig(api_key="test-key")
        with pytest.raises(AuthError) as exc_info:
            validate_auth(config)
        assert "Could not connect" in str(exc_info.value)

    @patch("lyzr_kit.utils.auth.httpx.get")
    def test_validate_auth_timeout(self, mock_get):
        """validate_auth should raise AuthError on timeout."""
        import httpx

        mock_get.side_effect = httpx.TimeoutException("Timeout")

        config = AuthConfig(api_key="test-key")
        with pytest.raises(AuthError) as exc_info:
            validate_auth(config)
        assert "timed out" in str(exc_info.value)

    @patch("lyzr_kit.utils.auth.httpx.get")
    def test_validate_auth_server_error(self, mock_get):
        """validate_auth should raise AuthError for 5xx server errors."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        config = AuthConfig(api_key="test-key")
        with pytest.raises(AuthError) as exc_info:
            validate_auth(config)
        assert "HTTP 500" in str(exc_info.value)
        assert "failed" in str(exc_info.value).lower()


class TestRequireAuth:
    """Tests for require_auth function."""

    @patch("lyzr_kit.utils.auth.validate_auth", return_value=True)
    @patch("lyzr_kit.utils.auth.load_auth")
    def test_require_auth_success(self, mock_load, mock_validate):
        """require_auth should return AuthConfig when valid."""
        mock_load.return_value = AuthConfig(api_key="valid-key")

        config = require_auth()
        assert config.api_key == "valid-key"
        mock_load.assert_called_once()
        mock_validate.assert_called_once()


class TestGetApiHeaders:
    """Tests for get_api_headers function."""

    def test_get_api_headers(self):
        """get_api_headers should return correct headers dict."""
        config = AuthConfig(api_key="my-key")
        headers = get_api_headers(config)

        assert headers["accept"] == "application/json"
        assert headers["x-api-key"] == "my-key"
