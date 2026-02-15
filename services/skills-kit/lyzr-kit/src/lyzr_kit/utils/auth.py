"""Authentication utilities for lyzr-kit."""

import os
from dataclasses import dataclass
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Constants
ENV_VAR_NAME = "LYZR_API_KEY"
ENV_USER_ID = "LYZR_USER_ID"
ENV_ORG_ID = "LYZR_ORG_ID"
ENV_MEMBERSTACK_TOKEN = "LYZR_MEMBERSTACK_TOKEN"
API_BASE_URL = "https://agent-prod.studio.lyzr.ai"
MARKETPLACE_BASE_URL = "https://marketplace-prod.studio.lyzr.ai"
STUDIO_BASE_URL = "https://studio.lyzr.ai"


@dataclass
class AuthConfig:
    """Authentication configuration."""

    api_key: str
    base_url: str = API_BASE_URL
    marketplace_url: str = MARKETPLACE_BASE_URL
    studio_url: str = STUDIO_BASE_URL
    user_id: str | None = None
    org_id: str | None = None
    memberstack_token: str | None = None


class AuthError(Exception):
    """Authentication error."""

    pass


def load_auth() -> AuthConfig:
    """Load authentication from .env file.

    Returns:
        AuthConfig with API key and base URL.

    Raises:
        AuthError: If .env file or API key is missing.
    """
    env_path = Path(".env")

    if not env_path.exists():
        try:
            cwd = Path.cwd()
        except (FileNotFoundError, OSError):
            cwd = Path(".")
        raise AuthError(
            "Authentication required.\n"
            f"  → No .env file found in: {cwd}\n"
            "  → Run 'lk auth' to save your API key.\n"
            "  → Get your API key from https://agent.api.lyzr.app"
        )

    load_dotenv(env_path, override=True)
    api_key = os.getenv(ENV_VAR_NAME)

    if not api_key:
        raise AuthError(
            f"{ENV_VAR_NAME} not found in .env file.\n"
            "  → Run 'lk auth' to save your API key.\n"
            "  → Get your API key from https://agent.api.lyzr.app"
        )

    user_id = os.getenv(ENV_USER_ID)
    org_id = os.getenv(ENV_ORG_ID)
    memberstack_token = os.getenv(ENV_MEMBERSTACK_TOKEN)

    return AuthConfig(
        api_key=api_key,
        user_id=user_id,
        org_id=org_id,
        memberstack_token=memberstack_token,
    )


def validate_auth(auth: AuthConfig) -> bool:
    """Validate authentication by calling health endpoint.

    Args:
        auth: AuthConfig with API key.

    Returns:
        True if authentication is valid.

    Raises:
        AuthError: If authentication fails.
    """
    try:
        response = httpx.get(
            f"{auth.base_url}/health",
            headers={
                "accept": "application/json",
                "x-api-key": auth.api_key,
            },
            timeout=10.0,
        )

        if response.status_code == 200:
            return True
        elif response.status_code == 401:
            raise AuthError(
                "Invalid API key.\n"
                "  → Run 'lk auth' to update your API key.\n"
                "  → Get a new key from https://agent.api.lyzr.app"
            )
        elif response.status_code == 403:
            raise AuthError(
                "Access forbidden. Your API key may be expired or revoked.\n"
                "  → Run 'lk auth' to update your API key.\n"
                "  → Contact support if the issue persists."
            )
        else:
            raise AuthError(
                f"Authentication check failed (HTTP {response.status_code}).\n"
                "  → Check your internet connection.\n"
                "  → Try again later or contact support."
            )
    except httpx.ConnectError as e:
        raise AuthError(
            "Could not connect to Lyzr API.\n"
            "  → Check your internet connection.\n"
            "  → API endpoint: https://agent.api.lyzr.app"
        ) from e
    except httpx.TimeoutException as e:
        raise AuthError(
            "Connection to Lyzr API timed out.\n"
            "  → Check your internet connection.\n"
            "  → Try again later."
        ) from e


def require_auth() -> AuthConfig:
    """Load and validate authentication.

    Returns:
        AuthConfig if authentication is valid.

    Raises:
        AuthError: If authentication fails.
    """
    auth = load_auth()
    validate_auth(auth)
    return auth


def get_api_headers(auth: AuthConfig) -> dict[str, str]:
    """Get HTTP headers for API requests.

    Args:
        auth: AuthConfig with API key.

    Returns:
        Dictionary of headers.
    """
    return {
        "accept": "application/json",
        "x-api-key": auth.api_key,
    }
