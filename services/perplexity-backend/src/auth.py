"""Authentication module for Perplexity OSS backend."""

import os
import asyncio
from typing import Dict, Any, Optional
from fastapi import HTTPException, Depends, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx

bearer_scheme = HTTPBearer()

# Constants for timeouts and retries
TIMEOUT_SECONDS = 30.0
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # Delay between retries in seconds


class AuthenticationError(Exception):
    """Custom exception for authentication errors"""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail


class AuthenticatedUser:
    """User data from authentication"""

    def __init__(self, email: str, user_id: str, api_key: str, token: str, org_id: str):
        self.email = email
        self.user_id = user_id
        self.api_key = api_key
        self.token = token
        self.org_id = org_id


async def verify_with_pagos(
    token: str, x_api_key: Optional[str] = None, attempt: int = 0
) -> Dict[str, Any]:
    """
    Helper function to verify with pagos service with retry logic
    """
    pagos_base_url = os.getenv(
        "PAGOS_BASE_URL", "https://pagos-prod.studio.lyzr.ai" # "https://pagos-dev.test.studio.lyzr.ai"
    )
    url = f"{pagos_base_url}/keys/user"

    try:
        timeout = httpx.Timeout(
            TIMEOUT_SECONDS,
            connect=TIMEOUT_SECONDS / 2,  # Shorter timeout for connection
            read=TIMEOUT_SECONDS,  # Full timeout for reading
            write=TIMEOUT_SECONDS / 2,  # Shorter timeout for writing
        )

        print(token, x_api_key)
        async with httpx.AsyncClient(timeout=timeout) as client:
            params = {}
            if x_api_key:
                params["api_key"] = x_api_key
                
            response = await client.get(
                url,
                params=params,
                headers={
                    "Authorization": f"Bearer {token}",
                },
            )
            response.raise_for_status()
            return response.json()

    except httpx.ConnectTimeout:
        if attempt < MAX_RETRIES - 1:
            await asyncio.sleep(RETRY_DELAY * (attempt + 1))  # Exponential backoff
            return await verify_with_pagos(token, x_api_key, attempt + 1)
        raise AuthenticationError(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Connection to authentication service timed out after {MAX_RETRIES} attempts",
        )

    except httpx.TimeoutException:
        raise AuthenticationError(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Request to authentication service timed out",
        )

    except httpx.HTTPStatusError as exc:
        print(exc)
        if exc.response.status_code == status.HTTP_401_UNAUTHORIZED:
            raise AuthenticationError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
        elif exc.response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                return await verify_with_pagos(token, x_api_key, attempt + 1)
        raise AuthenticationError(
            status_code=exc.response.status_code,
            detail=f"Authentication server error: {exc.response.text}",
        )

    except Exception as e:
        raise AuthenticationError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during authentication: {str(e)}",
        )


async def get_authenticated_user(
    x_api_key: str = Header(None, alias="x-api-key"),
    x_user_id: str = Header(None, alias="x-user-id"),
) -> AuthenticatedUser:
    """
    Authentication using API key and user ID headers from SDK.
    Falls back to gateway defaults when headers are not provided
    (gateway Basic Auth handles access control in that case).
    """
    # Use provided headers or fall back to gateway defaults
    effective_api_key = x_api_key or "gateway-default"
    effective_user_id = x_user_id or "gateway-user"

    try:
        return AuthenticatedUser(
            email="admin@platform.ai",
            user_id=effective_user_id,
            api_key=effective_api_key,
            token="",
            org_id="default",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
