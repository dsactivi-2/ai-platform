"""Unit tests for platform client utilities."""

from unittest.mock import MagicMock, patch

import pytest

from lyzr_kit.utils.auth import AuthConfig
from lyzr_kit.utils.platform import (
    AgentResponse,
    PlatformClient,
    PlatformError,
    get_provider_for_model,
)


class TestGetProviderForModel:
    """Tests for get_provider_for_model function."""

    def test_openai_models(self):
        """Should return OpenAI for gpt models."""
        assert get_provider_for_model("gpt-4o") == "OpenAI"
        assert get_provider_for_model("gpt-4o-mini") == "OpenAI"
        assert get_provider_for_model("o1-mini") == "OpenAI"

    def test_anthropic_models(self):
        """Should return Anthropic for claude models."""
        assert get_provider_for_model("claude-3-sonnet") == "Anthropic"
        assert get_provider_for_model("anthropic/claude-sonnet-4-0") == "Anthropic"

    def test_google_models(self):
        """Should return Google for gemini models."""
        assert get_provider_for_model("gemini/gemini-2.5-pro") == "Google"

    def test_groq_models(self):
        """Should return Groq for groq models."""
        assert get_provider_for_model("groq/llama-3.3-70b") == "Groq"

    def test_bedrock_models(self):
        """Should return Aws-Bedrock for bedrock models."""
        assert get_provider_for_model("bedrock/amazon.nova-pro") == "Aws-Bedrock"

    def test_perplexity_models(self):
        """Should return Perplexity for perplexity models."""
        assert get_provider_for_model("perplexity/sonar-pro") == "Perplexity"

    def test_default_provider(self):
        """Should return OpenAI as default."""
        assert get_provider_for_model("unknown-model") == "OpenAI"


class TestAgentResponse:
    """Tests for AgentResponse dataclass."""

    def test_agent_response_fields(self):
        """AgentResponse should have all required fields."""
        response = AgentResponse(
            agent_id="agent-123",
            env_id="env-456",
            endpoint="https://api.example.com/chat/agent-123",
            platform_url="https://studio.lyzr.ai/agent-create/agent-123",
            chat_url="https://studio.lyzr.ai/agent/agent-123/",
        )

        assert response.agent_id == "agent-123"
        assert response.env_id == "env-456"
        assert response.endpoint == "https://api.example.com/chat/agent-123"
        assert response.platform_url == "https://studio.lyzr.ai/agent-create/agent-123"
        assert response.chat_url == "https://studio.lyzr.ai/agent/agent-123/"

    def test_agent_response_optional_fields(self):
        """AgentResponse should have optional fields with defaults."""
        response = AgentResponse(
            agent_id="agent-123",
            env_id="env-456",
            endpoint="https://api.example.com/chat/agent-123",
        )

        assert response.platform_url is None
        assert response.chat_url is None
        assert response.app_id is None


class TestPlatformClientInit:
    """Tests for PlatformClient initialization."""

    def test_platform_client_init(self):
        """PlatformClient should initialize with auth config."""
        auth = AuthConfig(api_key="test-key")
        client = PlatformClient(auth)

        assert client.auth == auth
        assert client._headers["x-api-key"] == "test-key"
        assert client._headers["Content-Type"] == "application/json"

    def test_marketplace_app_without_token(self):
        """_create_marketplace_app returns None when no memberstack token."""
        auth = AuthConfig(api_key="test-key", user_id="user-123")  # No token
        client = PlatformClient(auth)

        result = client._create_marketplace_app("agent-123", "Test", "Description")

        assert result is None

    def test_marketplace_app_without_user_id(self):
        """_create_marketplace_app returns None when no user_id."""
        auth = AuthConfig(api_key="test-key", memberstack_token="token-123")  # No user_id
        client = PlatformClient(auth)

        result = client._create_marketplace_app("agent-123", "Test", "Description")

        assert result is None


class TestPlatformClientCreateAgent:
    """Tests for PlatformClient.create_agent method."""

    @patch("lyzr_kit.utils.platform.httpx.post")
    def test_create_agent_error_status(self, mock_post):
        """create_agent should raise PlatformError on non-200/201 status."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        auth = AuthConfig(api_key="test-key")
        client = PlatformClient(auth)

        # Create a minimal mock agent
        mock_agent = MagicMock()
        mock_agent.name = "Test Agent"
        mock_agent.description = "Test"
        mock_agent.config.instructions = "Test instructions"
        mock_agent.config.role = None
        mock_agent.config.goal = None
        mock_agent.model.name = "gpt-4o"
        mock_agent.model.temperature = 0.7
        mock_agent.model.top_p = 0.9

        with pytest.raises(PlatformError) as exc_info:
            client.create_agent(mock_agent)

        assert "Failed to create agent" in str(exc_info.value)
        assert "400" in str(exc_info.value)

    @patch("lyzr_kit.utils.platform.httpx.post")
    def test_create_agent_no_agent_id_in_response(self, mock_post):
        """create_agent should raise PlatformError if no agent_id in response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}  # No agent_id
        mock_post.return_value = mock_response

        auth = AuthConfig(api_key="test-key")
        client = PlatformClient(auth)

        mock_agent = MagicMock()
        mock_agent.name = "Test Agent"
        mock_agent.description = "Test"
        mock_agent.config.instructions = "Test instructions"
        mock_agent.config.role = None
        mock_agent.config.goal = None
        mock_agent.model.name = "gpt-4o"
        mock_agent.model.temperature = 0.7
        mock_agent.model.top_p = 0.9

        with pytest.raises(PlatformError) as exc_info:
            client.create_agent(mock_agent)

        assert "No agent_id in response" in str(exc_info.value)


class TestPlatformClientUpdateAgent:
    """Tests for PlatformClient.update_agent method."""

    @patch("lyzr_kit.utils.platform.httpx.put")
    def test_update_agent_error_status(self, mock_put):
        """update_agent should raise PlatformError on non-200/201 status."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_put.return_value = mock_response

        auth = AuthConfig(api_key="test-key")
        client = PlatformClient(auth)

        mock_agent = MagicMock()
        mock_agent.name = "Test Agent"
        mock_agent.description = "Test"
        mock_agent.config.instructions = "Test instructions"
        mock_agent.config.role = None
        mock_agent.config.goal = None
        mock_agent.model.name = "gpt-4o"
        mock_agent.model.temperature = 0.7
        mock_agent.model.top_p = 0.9

        with pytest.raises(PlatformError) as exc_info:
            client.update_agent(mock_agent, "agent-123", "env-456")

        assert "Failed to update agent" in str(exc_info.value)
        assert "404" in str(exc_info.value)


class TestPlatformClientMarketplace:
    """Tests for PlatformClient._create_marketplace_app method."""

    @patch("lyzr_kit.utils.platform.httpx.post")
    def test_marketplace_app_success(self, mock_post):
        """_create_marketplace_app should return app_id on success."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "app-123"}
        mock_post.return_value = mock_response

        auth = AuthConfig(
            api_key="test-key",
            user_id="user-456",
            memberstack_token="token-789",
        )
        client = PlatformClient(auth)

        result = client._create_marketplace_app("agent-123", "Test App", "Description")

        assert result == "app-123"

    @patch("lyzr_kit.utils.platform.httpx.post")
    def test_marketplace_app_returns_none_on_error_status(self, mock_post):
        """_create_marketplace_app should return None on non-200/201 status."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        auth = AuthConfig(
            api_key="test-key",
            user_id="user-456",
            memberstack_token="token-789",
        )
        client = PlatformClient(auth)

        result = client._create_marketplace_app("agent-123", "Test App", "Description")

        assert result is None

    @patch("lyzr_kit.utils.platform.httpx.post")
    def test_marketplace_app_returns_none_on_exception(self, mock_post):
        """_create_marketplace_app should return None on exception."""
        mock_post.side_effect = Exception("Network error")

        auth = AuthConfig(
            api_key="test-key",
            user_id="user-456",
            memberstack_token="token-789",
        )
        client = PlatformClient(auth)

        result = client._create_marketplace_app("agent-123", "Test App", "Description")

        assert result is None

    @patch("lyzr_kit.utils.platform.httpx.post")
    def test_marketplace_app_returns_none_when_no_id_in_response(self, mock_post):
        """_create_marketplace_app should return None if no id in response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}  # No _id or id
        mock_post.return_value = mock_response

        auth = AuthConfig(
            api_key="test-key",
            user_id="user-456",
            memberstack_token="token-789",
        )
        client = PlatformClient(auth)

        result = client._create_marketplace_app("agent-123", "Test App", "Description")

        assert result is None
