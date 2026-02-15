"""Platform client for Lyzr Agent API v3."""

from dataclasses import dataclass

import httpx

from lyzr_kit.schemas.agent import Agent
from lyzr_kit.utils.auth import AuthConfig


class PlatformError(Exception):
    """Platform API error."""

    pass


@dataclass
class AgentResponse:
    """Response from agent creation/update."""

    agent_id: str
    env_id: str
    endpoint: str
    platform_url: str | None = None
    chat_url: str | None = None
    app_id: str | None = None


# Provider mapping for model names
PROVIDER_MAP = {
    "gpt": "OpenAI",
    "o1": "OpenAI",
    "o3": "OpenAI",
    "o4": "OpenAI",
    "claude": "Anthropic",
    "anthropic": "Anthropic",
    "gemini": "Google",
    "groq": "Groq",
    "bedrock": "Aws-Bedrock",
    "perplexity": "Perplexity",
}


def get_provider_for_model(model: str) -> str:
    """Get the provider ID for a given model name."""
    model_lower = model.lower()
    for prefix, provider in PROVIDER_MAP.items():
        if model_lower.startswith(prefix) or f"/{prefix}" in model_lower:
            return provider
    return "OpenAI"  # Default to OpenAI


def _build_agent_payload(agent: Agent) -> dict[str, object]:
    """Build the API payload for agent create/update.

    Args:
        agent: Agent configuration.

    Returns:
        Dictionary payload for the v3 API.
    """
    payload = {
        "name": agent.name,
        "description": agent.description or "",
        "agent_instructions": agent.config.instructions or "",
        "model": agent.model.name,
        "temperature": agent.model.temperature,
        "top_p": agent.model.top_p,
        "provider_id": get_provider_for_model(agent.model.name),
        "features": [
            {
                "type": "SHORT_TERM_MEMORY",
                "priority": 0,
                "config": {},
            }
        ],
    }

    if agent.config.role:
        payload["agent_role"] = agent.config.role
    if agent.config.goal:
        payload["agent_goal"] = agent.config.goal

    return payload


class PlatformClient:
    """Client for interacting with Lyzr platform API v3."""

    def __init__(self, auth: AuthConfig) -> None:
        """Initialize platform client.

        Args:
            auth: Authentication configuration with API key.
        """
        self.auth = auth
        self._headers = {
            "Content-Type": "application/json",
            "accept": "application/json",
            "x-api-key": auth.api_key,
        }

    def create_agent(self, agent: Agent) -> AgentResponse:
        """Create agent on the platform using v3 API.

        Args:
            agent: Agent configuration from local YAML.

        Returns:
            AgentResponse with agent_id, env_id, and inference endpoint.

        Raises:
            PlatformError: If agent creation fails.
        """
        try:
            payload = _build_agent_payload(agent)

            # Create agent via v3 API
            url = f"{self.auth.base_url}/v3/agents/template/single-task"
            response = httpx.post(url, json=payload, headers=self._headers, timeout=30.0)

            if response.status_code not in (200, 201):
                raise Exception(f"{response.status_code} - {response.text}")

            data = response.json()
            agent_id = data.get("agent_id") or data.get("_id")

            if not agent_id:
                raise Exception("No agent_id in response")

            # Create app on marketplace first (required for Studio chat to work)
            app_id = None
            if self.auth.memberstack_token and self.auth.user_id:
                app_id = self._create_marketplace_app(
                    agent_id=agent_id,
                    name=agent.name,
                    description=agent.description or "",
                )

            # Build URLs - use v3 inference endpoint
            endpoint = f"{self.auth.base_url}/v3/inference/chat/"
            platform_url = f"{self.auth.studio_url}/agent-create/{agent_id}"
            # Chat URL uses marketplace app_id (required for Studio chat to work)
            chat_url = f"{self.auth.studio_url}/agent/{app_id}/" if app_id else None

            return AgentResponse(
                agent_id=agent_id,
                env_id=agent_id,  # v3 API doesn't use separate env_id
                endpoint=endpoint,
                platform_url=platform_url,
                chat_url=chat_url,
                app_id=app_id,
            )

        except Exception as e:
            raise PlatformError(f"Failed to create agent: {e}") from e

    def update_agent(self, agent: Agent, agent_id: str, env_id: str) -> AgentResponse:
        """Update agent on the platform using v3 API.

        Args:
            agent: Updated agent configuration.
            agent_id: Existing agent ID on platform.
            env_id: Existing environment ID on platform (unused in v3).

        Returns:
            AgentResponse with updated information.

        Raises:
            PlatformError: If agent update fails.
        """
        try:
            payload = _build_agent_payload(agent)

            # Update agent via v3 API
            url = f"{self.auth.base_url}/v3/agents/template/single-task/{agent_id}"
            response = httpx.put(url, json=payload, headers=self._headers, timeout=30.0)

            if response.status_code not in (200, 201):
                raise Exception(f"{response.status_code} - {response.text}")

            # Build URLs - use v3 inference endpoint
            endpoint = f"{self.auth.base_url}/v3/inference/chat/"
            platform_url = f"{self.auth.studio_url}/agent-create/{agent_id}"
            # Note: chat_url requires app_id which we don't have during update
            # The app_id was returned during create and stored locally

            return AgentResponse(
                agent_id=agent_id,
                env_id=env_id,
                endpoint=endpoint,
                platform_url=platform_url,
                chat_url=None,  # Requires app_id from marketplace
            )

        except Exception as e:
            raise PlatformError(f"Failed to update agent: {e}") from e

    def _create_marketplace_app(self, agent_id: str, name: str, description: str) -> str | None:
        """Create an app on the marketplace for the agent.

        Args:
            agent_id: The agent ID to associate with the app.
            name: The name of the app.
            description: The description of the app.

        Returns:
            The app ID if creation succeeded, None otherwise.
        """
        if not self.auth.memberstack_token or not self.auth.user_id:
            return None

        try:
            # Make app name unique by appending short agent_id suffix
            # This prevents "App with this name already exists" errors
            unique_name = f"{name} ({agent_id[-8:]})"

            response = httpx.post(
                f"{self.auth.marketplace_url}/app/",
                json={
                    "name": unique_name,
                    "description": description,
                    "agent_id": agent_id,
                    "creator": "lyzr-kit",
                    "user_id": self.auth.user_id,
                    "public": False,
                    "welcome_message": "",
                    "tags": {"industry": "", "function": "", "category": ""},
                },
                headers={
                    "accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.auth.memberstack_token}",
                },
                timeout=30.0,
            )

            if response.status_code in (200, 201):
                data = response.json()
                app_id = data.get("_id") or data.get("id")
                return str(app_id) if app_id else None
            return None
        except Exception:
            # Marketplace app creation is optional, don't fail the whole operation
            return None
