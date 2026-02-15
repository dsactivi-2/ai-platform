"""
Main client for the Agent Simulation Engine SDK.
"""

import requests
from typing import Optional

from .exceptions import (
    ASIMError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ConnectionError,
)


class ASIMEngine:
    """
    Agent Simulation Engine API.

    Usage:
        from agent_simulation_engine import ASIMEngine

        engine = ASIMEngine(api_key="studio-api-key")
        env = engine.environments.create(agent_id="...", name="My Tests")
    """

    DEFAULT_BASE_URL = "https://agentsim-api.studio.lyzr.ai"
    DEFAULT_TIMEOUT = 30

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        """
        Initialize the ASIM engine.

        Args:
            api_key: Your Lyzr API key
            base_url: Optional custom API base URL
            timeout: Request timeout in seconds (default: 30)
        """
        self.api_key = api_key
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout or self.DEFAULT_TIMEOUT

        # Create session with default headers
        self.session = requests.Session()
        self.session.headers.update({
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

        # Initialize resource classes
        self._init_resources()

    def _init_resources(self):
        """Initialize resource classes."""
        from .resources.environments import Environments
        from .resources.personas import Personas
        from .resources.scenarios import Scenarios
        from .resources.simulations import Simulations
        from .resources.evaluations import Evaluations
        from .resources.jobs import Jobs
        from .resources.evaluation_runs import EvaluationRuns
        from .resources.hardening import Hardening
        from .resources.dashboard import Dashboard

        self.environments = Environments(self)
        self.personas = Personas(self)
        self.scenarios = Scenarios(self)
        self.simulations = Simulations(self)
        self.evaluations = Evaluations(self)
        self.jobs = Jobs(self)
        self.evaluation_runs = EvaluationRuns(self)
        self.hardening = Hardening(self)
        self.dashboard = Dashboard(self)

    def _build_url(self, path: str) -> str:
        """Build full URL from path."""
        return f"{self.base_url}/api/environments{path}"

    def _handle_response(self, response: requests.Response) -> dict:
        """Handle API response and raise appropriate exceptions."""
        try:
            data = response.json() if response.text else {}
        except ValueError:
            data = {"detail": response.text}

        if response.status_code == 200 or response.status_code == 201:
            return data

        error_message = data.get("detail", str(data))

        if response.status_code == 401:
            raise AuthenticationError(error_message, response=data)
        elif response.status_code == 403:
            raise AuthorizationError(error_message, response=data)
        elif response.status_code == 404:
            raise NotFoundError(error_message, response=data)
        elif response.status_code == 400 or response.status_code == 422:
            raise ValidationError(error_message, response=data)
        elif response.status_code == 429:
            raise RateLimitError(error_message, response=data)
        elif response.status_code >= 500:
            raise ServerError(error_message, status_code=response.status_code, response=data)
        else:
            raise ASIMError(error_message, status_code=response.status_code, response=data)

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[dict] = None,
        json: Optional[dict] = None,
    ) -> dict:
        """
        Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API path (will be appended to /api/environments)
            params: Query parameters
            json: JSON request body

        Returns:
            Parsed JSON response

        Raises:
            ASIMError: On API errors
        """
        url = self._build_url(path)

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json,
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Request to {url} timed out after {self.timeout}s")
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(f"Failed to connect to {url}: {str(e)}")

    def get(self, path: str, params: Optional[dict] = None) -> dict:
        """Make a GET request."""
        return self._request("GET", path, params=params)

    def post(self, path: str, json: Optional[dict] = None) -> dict:
        """Make a POST request."""
        return self._request("POST", path, json=json)

    def put(self, path: str, json: Optional[dict] = None) -> dict:
        """Make a PUT request."""
        return self._request("PUT", path, json=json)

    def delete(self, path: str) -> dict:
        """Make a DELETE request."""
        return self._request("DELETE", path)
