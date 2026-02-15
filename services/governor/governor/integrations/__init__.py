"""Integrations with web frameworks and libraries."""

__all__: list[str] = []

# FastAPI is optional dependency
try:
    from governor.integrations.fastapi import create_approval_router, GovernMiddleware

    __all__.extend(["create_approval_router", "GovernMiddleware"])
except ImportError:
    pass
