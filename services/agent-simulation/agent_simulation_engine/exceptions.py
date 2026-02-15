"""
Custom exceptions for the Agent Simulation Engine SDK.
"""


class ASIMError(Exception):
    """Base exception for all ASIM SDK errors."""

    def __init__(self, message: str, status_code: int = None, response: dict = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)


class AuthenticationError(ASIMError):
    """Raised when API key is invalid or missing."""

    def __init__(self, message: str = "Invalid or missing API key", response: dict = None):
        super().__init__(message, status_code=401, response=response)


class AuthorizationError(ASIMError):
    """Raised when user lacks permission for the requested action."""

    def __init__(self, message: str = "Permission denied", response: dict = None):
        super().__init__(message, status_code=403, response=response)


class NotFoundError(ASIMError):
    """Raised when the requested resource is not found."""

    def __init__(self, message: str = "Resource not found", response: dict = None):
        super().__init__(message, status_code=404, response=response)


class ValidationError(ASIMError):
    """Raised when request data is invalid."""

    def __init__(self, message: str = "Invalid request data", response: dict = None):
        super().__init__(message, status_code=400, response=response)


class RateLimitError(ASIMError):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", response: dict = None):
        super().__init__(message, status_code=429, response=response)


class ServerError(ASIMError):
    """Raised when the server encounters an error."""

    def __init__(self, message: str = "Server error", status_code: int = 500, response: dict = None):
        super().__init__(message, status_code=status_code, response=response)


class TimeoutError(ASIMError):
    """Raised when a request times out."""

    def __init__(self, message: str = "Request timed out", response: dict = None):
        super().__init__(message, status_code=None, response=response)


class ConnectionError(ASIMError):
    """Raised when unable to connect to the API."""

    def __init__(self, message: str = "Unable to connect to API", response: dict = None):
        super().__init__(message, status_code=None, response=response)
