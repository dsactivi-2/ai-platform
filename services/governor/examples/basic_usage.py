"""Basic usage examples for governor."""

import asyncio
from governor import govern, ValidationPolicy, AuditPolicy


# Example 1: Simple function with audit policy
@govern(policies=[AuditPolicy()])
async def process_data(data: dict) -> dict:
    """Process some data with audit logging."""
    return {"processed": True, "data": data}


# Example 2: Function with validation
from pydantic import BaseModel


class InputSchema(BaseModel):
    """Input validation schema."""

    name: str
    age: int


@govern(policies=[ValidationPolicy(input_schema=InputSchema)])
async def create_user(name: str, age: int) -> dict:
    """Create a user with input validation."""
    return {"user_id": 123, "name": name, "age": age}


# Example 3: Pre and post actions
from governor.core.context import ExecutionContext


async def log_start(ctx: ExecutionContext) -> None:
    """Log when execution starts."""
    print(f"[PRE] Starting {ctx.function_name} with inputs: {ctx.inputs}")


async def log_end(ctx: ExecutionContext) -> None:
    """Log when execution completes."""
    print(f"[POST] Completed {ctx.function_name} with status: {ctx.status}")


@govern(pre=[log_start], post=[log_end])
async def important_operation(value: int) -> int:
    """Operation with logging."""
    return value * 2


# Example 4: Multiple policies
from governor import AuthorizationPolicy, RateLimitPolicy


@govern(
    policies=[
        ValidationPolicy(input_validator=lambda x: x.get("amount", 0) > 0),
        AuthorizationPolicy(required_roles={"admin", "finance"}),
        RateLimitPolicy(max_calls=10, window_seconds=60),
        AuditPolicy(compliance_tags=["SOC2", "financial"]),
    ]
)
async def process_payment(amount: float, account: str) -> dict:
    """Process a payment with full governance."""
    return {"status": "success", "amount": amount, "account": account}


async def main() -> None:
    """Run examples."""
    print("=" * 70)
    print("governor: Basic Usage Examples")
    print("=" * 70)

    # Example 1: Audit
    print("\n1. Simple audit:")
    result = await process_data({"key": "value"})
    print(f"   Result: {result}")

    # Example 2: Validation (will pass)
    print("\n2. Valid input:")
    try:
        result = await create_user(name="Alice", age=30)
        print(f"   Result: {result}")
    except Exception as e:
        print(f"   Error: {e}")

    # Example 2b: Validation (will fail)
    print("\n3. Invalid input (missing required field):")
    try:
        result = await create_user(name="Bob", age="invalid")  # type: ignore
        print(f"   Result: {result}")
    except Exception as e:
        print(f"   Error: {type(e).__name__}: {e}")

    # Example 3: Pre/post actions
    print("\n4. Pre/post actions:")
    result = await important_operation(21)
    print(f"   Result: {result}")

    # Example 4: Multiple policies (will fail without proper context)
    print("\n5. Multiple policies (no auth context - will fail):")
    try:
        result = await process_payment(100.0, "ACC123")
        print(f"   Result: {result}")
    except Exception as e:
        print(f"   Error: {type(e).__name__}: {e}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
