"""Basic tests for governor."""

import pytest
from governor import (
    govern,
    ValidationPolicy,
    AuthorizationPolicy,
    AuditPolicy,
    RateLimitPolicy,
    InMemoryStorage,
)
from governor.core.context import ExecutionContext, ExecutionStatus


@pytest.mark.asyncio
async def test_simple_governed_function():
    """Test basic governed function execution."""

    @govern()
    async def simple_function(x: int) -> int:
        return x * 2

    result = await simple_function(21)
    assert result == 42


@pytest.mark.asyncio
async def test_validation_policy_success():
    """Test validation policy with valid input."""

    @govern(policies=[ValidationPolicy(input_validator=lambda x: x.get("kwargs", {}).get("value", 0) > 0)])
    async def validated_function(value: int) -> int:
        return value

    result = await validated_function(10)
    assert result == 10


@pytest.mark.asyncio
async def test_validation_policy_failure():
    """Test validation policy with invalid input."""

    @govern(policies=[ValidationPolicy(input_validator=lambda x: x.get("kwargs", {}).get("value", 0) > 0)])
    async def validated_function(value: int) -> int:
        return value

    with pytest.raises(PermissionError, match="Policy.*blocked execution"):
        await validated_function(-5)


@pytest.mark.asyncio
async def test_pre_post_actions():
    """Test pre and post actions."""
    executed = {"pre": False, "post": False}

    async def pre_action(ctx: ExecutionContext) -> None:
        executed["pre"] = True

    async def post_action(ctx: ExecutionContext) -> None:
        executed["post"] = True

    @govern(pre=[pre_action], post=[post_action])
    async def test_function() -> str:
        return "done"

    result = await test_function()
    assert result == "done"
    assert executed["pre"] is True
    assert executed["post"] is True


@pytest.mark.asyncio
async def test_state_capture():
    """Test state capture functionality."""
    storage = InMemoryStorage()

    @govern(capture_state=True, storage=storage)
    async def stateful_function(x: int, y: int) -> int:
        return x + y

    result = await stateful_function(10, 20)
    assert result == 30

    # Check execution was stored
    executions = await storage.list_executions()
    assert len(executions) > 0
    assert executions[0].status == ExecutionStatus.COMPLETED
    assert executions[0].function_name == "stateful_function"


@pytest.mark.asyncio
async def test_rate_limit_policy():
    """Test rate limiting policy."""
    policy = RateLimitPolicy(max_calls=2, window_seconds=60)

    @govern(policies=[policy])
    async def rate_limited_function() -> str:
        return "ok"

    # First two calls should succeed
    await rate_limited_function()
    await rate_limited_function()

    # Third call should fail
    with pytest.raises(PermissionError, match="Rate limit exceeded"):
        await rate_limited_function()


@pytest.mark.asyncio
async def test_audit_policy():
    """Test audit policy (should always pass)."""
    audit_log = []

    def custom_logger(record: dict) -> None:
        audit_log.append(record)

    @govern(policies=[AuditPolicy(custom_logger=custom_logger)])
    async def audited_function(value: int) -> int:
        return value * 2

    result = await audited_function(5)
    assert result == 10
    assert len(audit_log) > 0  # Audit record created


@pytest.mark.asyncio
async def test_authorization_policy_failure():
    """Test authorization policy without proper context."""

    @govern(
        policies=[AuthorizationPolicy(required_roles={"admin"})],
        context={"user": {"roles": ["user"]}},  # User doesn't have admin role
    )
    async def admin_function() -> str:
        return "admin action"

    with pytest.raises(PermissionError, match="lacks required roles"):
        await admin_function()


@pytest.mark.asyncio
async def test_authorization_policy_success():
    """Test authorization policy with proper context."""

    @govern(
        policies=[AuthorizationPolicy(required_roles={"admin"})],
        context={"user": {"roles": ["admin", "user"]}},  # User has admin role
    )
    async def admin_function() -> str:
        return "admin action"

    result = await admin_function()
    assert result == "admin action"


@pytest.mark.asyncio
async def test_multiple_policies():
    """Test multiple policies together."""
    storage = InMemoryStorage()

    @govern(
        policies=[
            ValidationPolicy(input_validator=lambda x: x.get("kwargs", {}).get("value", 0) > 0),
            AuditPolicy(),
        ],
        storage=storage,
    )
    async def multi_policy_function(value: int) -> int:
        return value * 2

    result = await multi_policy_function(10)
    assert result == 20

    # Verify execution was stored
    executions = await storage.list_executions()
    assert len(executions) > 0


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in governed functions."""
    storage = InMemoryStorage()

    @govern(storage=storage)
    async def failing_function() -> None:
        raise ValueError("Test error")

    with pytest.raises(ValueError, match="Test error"):
        await failing_function()

    # Verify failed execution was recorded
    executions = await storage.list_executions()
    assert len(executions) > 0
    assert executions[0].status == ExecutionStatus.FAILED
    assert "Test error" in executions[0].error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
