"""Tests for approval system."""

import asyncio

import pytest

from governor import govern, ApprovalPolicy
from governor.approval.handlers import CallbackApprovalHandler
from governor.approval.manager import get_default_approval_manager, ApprovalManager
from governor.storage.memory import InMemoryStorage


@pytest.mark.asyncio
async def test_approval_policy_blocks_execution():
    """Test that ApprovalPolicy blocks execution until approved."""
    manager = ApprovalManager()

    @govern(
        policies=[ApprovalPolicy(approvers=["admin@company.com"], timeout_seconds=1)],
        approval_manager=manager,
    )
    async def protected_function() -> str:
        return "executed"

    # Should timeout and raise PermissionError
    with pytest.raises(PermissionError, match="Approval required"):
        await protected_function()


@pytest.mark.asyncio
async def test_approval_with_callback_handler():
    """Test approval with callback handler that immediately approves."""
    manager = get_default_approval_manager()

    async def immediate_approval(exec_id, func_name, inputs, approvers):
        """Immediately approve the request."""
        # Provide decision before timeout
        await asyncio.sleep(0.1)
        manager.provide_decision(exec_id, approved=True, approver="admin", reason="Test approval")
        return (True, "admin", "Approved")

    handler = CallbackApprovalHandler(callback=immediate_approval)

    @govern(
        policies=[ApprovalPolicy(approvers=["admin"], timeout_seconds=2)],
        approval_handler=handler,
        approval_manager=manager,
    )
    async def protected_function() -> str:
        return "executed"

    # Should succeed with approval
    result = await protected_function()
    assert result == "executed"


@pytest.mark.asyncio
async def test_approval_rejection():
    """Test that rejected approval blocks execution."""
    manager = get_default_approval_manager()

    async def reject_approval(exec_id, func_name, inputs, approvers):
        """Reject the request."""
        await asyncio.sleep(0.1)
        manager.provide_decision(exec_id, approved=False, approver="admin", reason="Rejected for testing")
        return (False, "admin", "Rejected")

    handler = CallbackApprovalHandler(callback=reject_approval)

    @govern(
        policies=[ApprovalPolicy(approvers=["admin"], timeout_seconds=2)],
        approval_handler=handler,
        approval_manager=manager,
    )
    async def protected_function() -> str:
        return "executed"

    # Should be rejected
    with pytest.raises(PermissionError, match="Rejected for testing"):
        await protected_function()


@pytest.mark.asyncio
async def test_approval_with_multiple_approvers():
    """Test approval policy with multiple approvers."""
    manager = get_default_approval_manager()

    async def multi_approver(exec_id, func_name, inputs, approvers):
        """Simulate approval from one of multiple approvers."""
        await asyncio.sleep(0.1)
        # Approve from one of the approvers
        manager.provide_decision(exec_id, approved=True, approver=approvers[0], reason="Approved")
        return (True, approvers[0], "Approved")

    handler = CallbackApprovalHandler(callback=multi_approver)

    @govern(
        policies=[ApprovalPolicy(approvers=["admin1@co.com", "admin2@co.com"], timeout_seconds=2)],
        approval_handler=handler,
        approval_manager=manager,
    )
    async def protected_function() -> str:
        return "executed"

    result = await protected_function()
    assert result == "executed"


@pytest.mark.asyncio
async def test_approval_timeout():
    """Test that approval times out if no decision is made."""
    manager = ApprovalManager()

    async def slow_approval(exec_id, func_name, inputs, approvers):
        """Never provides a decision."""
        await asyncio.sleep(10)  # Longer than timeout
        return (False, "system", "Timeout")

    handler = CallbackApprovalHandler(callback=slow_approval)

    @govern(
        policies=[ApprovalPolicy(approvers=["admin"], timeout_seconds=0.5, on_timeout="reject")],
        approval_handler=handler,
        approval_manager=manager,
    )
    async def protected_function() -> str:
        return "executed"

    # Should timeout
    with pytest.raises(PermissionError):
        await protected_function()


@pytest.mark.asyncio
async def test_approval_with_state_capture():
    """Test that approval works with state capture enabled."""
    storage = InMemoryStorage()
    manager = get_default_approval_manager()

    async def approve_callback(exec_id, func_name, inputs, approvers):
        await asyncio.sleep(0.1)
        manager.provide_decision(exec_id, approved=True, approver="admin", reason="Approved")
        return (True, "admin", "Approved")

    handler = CallbackApprovalHandler(callback=approve_callback)

    @govern(
        policies=[ApprovalPolicy(approvers=["admin"], timeout_seconds=2)],
        approval_handler=handler,
        approval_manager=manager,
        storage=storage,
        capture_state=True,
    )
    async def protected_function(value: int) -> int:
        return value * 2

    result = await protected_function(21)
    assert result == 42

    # Verify execution was stored
    executions = await storage.list_executions()
    assert len(executions) > 0
    assert executions[0].function_name == "protected_function"


@pytest.mark.asyncio
async def test_approval_manager_get_decision():
    """Test ApprovalManager get_decision method."""
    manager = ApprovalManager()

    # No decision yet
    decision = manager.get_decision("test-exec-id")
    assert decision is None

    # Provide decision
    manager.provide_decision("test-exec-id", approved=True, approver="admin", reason="Test")

    # Should now have decision
    decision = manager.get_decision("test-exec-id")
    assert decision is not None
    assert decision.approved is True
    assert decision.approver == "admin"
    assert decision.reason == "Test"


@pytest.mark.asyncio
async def test_approval_manager_wait_for_decision():
    """Test ApprovalManager wait_for_decision method."""
    manager = ApprovalManager()

    exec_id = "test-exec-id"

    async def provide_decision_later():
        await asyncio.sleep(0.2)
        manager.provide_decision(exec_id, approved=True, approver="admin", reason="Delayed approval")

    # Start task to provide decision
    asyncio.create_task(provide_decision_later())

    # Wait for decision
    decision = await manager.wait_for_decision(exec_id, timeout_seconds=1)

    assert decision is not None
    assert decision.approved is True
    assert decision.approver == "admin"


@pytest.mark.asyncio
async def test_approval_with_auto_approve_conditions():
    """Test ApprovalPolicy with auto-approve conditions."""
    manager = get_default_approval_manager()

    @govern(
        policies=[
            ApprovalPolicy(
                approvers=["admin"],
                timeout_seconds=2,
                auto_approve_if=lambda inputs: inputs.get("kwargs", {}).get("amount", 0) < 100,
            )
        ],
        approval_manager=manager,
    )
    async def process_transaction(amount: int) -> str:
        return f"Processed ${amount}"

    # Small amount - should auto-approve
    result = await process_transaction(amount=50)
    assert result == "Processed $50"

    # Large amount - should require approval and timeout
    with pytest.raises(PermissionError):
        await process_transaction(amount=500)
