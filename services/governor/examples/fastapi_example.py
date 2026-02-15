"""FastAPI integration example."""

from typing import Dict

try:
    from fastapi import FastAPI, Depends
    from pydantic import BaseModel
except ImportError:
    print("This example requires FastAPI. Install with: pip install governor[fastapi]")
    exit(1)

from governor import govern, ValidationPolicy, AuthorizationPolicy, RateLimitPolicy
from governor.integrations.fastapi import create_approval_router, GovernMiddleware
from governor.storage.memory import InMemoryStorage


# Shared storage
storage = InMemoryStorage()

# Create FastAPI app
app = FastAPI(title="Agent Govern FastAPI Example")

# Add governance middleware
app.add_middleware(GovernMiddleware)

# Add approval router
app.include_router(create_approval_router(storage=storage))


# Models
class UserCreate(BaseModel):
    """User creation model."""

    name: str
    email: str
    role: str


class PaymentRequest(BaseModel):
    """Payment request model."""

    amount: float
    account: str
    description: str


# Governed endpoints
@app.post("/users")
@govern(
    policies=[
        ValidationPolicy(input_schema=UserCreate),
        RateLimitPolicy(max_calls=100, window_seconds=60),
    ],
    storage=storage,
)
async def create_user(user: UserCreate) -> Dict[str, str]:
    """Create a new user with validation and rate limiting."""
    return {
        "user_id": "12345",
        "name": user.name,
        "email": user.email,
        "role": user.role,
    }


@app.post("/payments")
@govern(
    policies=[
        ValidationPolicy(input_schema=PaymentRequest),
        AuthorizationPolicy(required_roles={"admin", "finance"}),
        RateLimitPolicy(max_calls=10, window_seconds=60, per_user=True),
    ],
    storage=storage,
)
async def process_payment(payment: PaymentRequest) -> Dict[str, str]:
    """
    Process a payment with full governance.

    Requires admin or finance role, validates input, and rate limits per user.
    """
    return {
        "transaction_id": "TXN789",
        "amount": payment.amount,
        "account": payment.account,
        "status": "completed",
    }


@app.get("/agents/{agent_id}/execute")
@govern(
    policies=[
        AuthorizationPolicy(required_permissions={"agent.execute"}),
        RateLimitPolicy(max_calls=50, window_seconds=60),
    ],
    storage=storage,
    capture_state=True,
)
async def execute_agent(agent_id: str, task: str) -> Dict[str, str]:
    """
    Execute an agent task with governance.

    State is captured for replay and debugging.
    """
    return {
        "agent_id": agent_id,
        "task": task,
        "status": "executing",
        "execution_id": "EXEC123",
    }


# Health check
@app.get("/health")
async def health() -> Dict[str, str]:
    """Health check endpoint (not governed)."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    print("=" * 70)
    print("Agent Govern FastAPI Example")
    print("=" * 70)
    print("\nStarting server...")
    print("\nAvailable endpoints:")
    print("  - POST   /users              - Create user (with validation & rate limit)")
    print("  - POST   /payments           - Process payment (requires auth)")
    print("  - GET    /agents/{id}/execute - Execute agent (with state capture)")
    print("  - GET    /health             - Health check")
    print("\nGovernance endpoints:")
    print("  - GET    /govern/approvals/pending")
    print("  - GET    /govern/approvals/{execution_id}")
    print("  - POST   /govern/approvals/{execution_id}/approve")
    print("  - POST   /govern/approvals/{execution_id}/reject")
    print("  - GET    /govern/executions")
    print("  - GET    /govern/executions/{execution_id}")
    print("\nExample requests:")
    print("\n  Create user:")
    print('    curl -X POST http://localhost:8000/users \\')
    print('      -H "Content-Type: application/json" \\')
    print('      -d \'{"name": "Alice", "email": "alice@example.com", "role": "user"}\'')
    print("\n  List executions:")
    print("    curl http://localhost:8000/govern/executions")
    print("\n" + "=" * 70)

    uvicorn.run(app, host="0.0.0.0", port=8000)
