"""Tests for storage backends."""

import pytest

from governor import govern
from governor.core.context import ExecutionContext, ExecutionStatus
from governor.storage.memory import InMemoryStorage


@pytest.mark.asyncio
async def test_inmemory_storage_save_and_get():
    """Test saving and retrieving execution from InMemory storage."""
    storage = InMemoryStorage()

    context = ExecutionContext(
        execution_id="test-123",
        function_name="test_function",
        inputs={"args": (42,), "kwargs": {}},
    )
    context.status = ExecutionStatus.COMPLETED
    context.result = "success"

    # Save
    await storage.save_execution(context)

    # Retrieve
    retrieved = await storage.get_execution("test-123")
    assert retrieved is not None
    assert retrieved.execution_id == "test-123"
    assert retrieved.function_name == "test_function"
    assert retrieved.status == ExecutionStatus.COMPLETED
    assert retrieved.result == "success"


@pytest.mark.asyncio
async def test_inmemory_storage_list_executions():
    """Test listing executions from InMemory storage."""
    storage = InMemoryStorage()

    # Save multiple executions
    for i in range(3):
        context = ExecutionContext(
            execution_id=f"test-{i}",
            function_name=f"function_{i}",
            inputs={"args": (), "kwargs": {}},
        )
        context.status = ExecutionStatus.COMPLETED if i % 2 == 0 else ExecutionStatus.FAILED
        await storage.save_execution(context)

    # List all
    all_executions = await storage.list_executions()
    assert len(all_executions) == 3

    # List by status
    completed = await storage.list_executions(status=ExecutionStatus.COMPLETED)
    assert len(completed) == 2

    failed = await storage.list_executions(status=ExecutionStatus.FAILED)
    assert len(failed) == 1


@pytest.mark.asyncio
async def test_inmemory_storage_list_by_function():
    """Test listing executions by function name."""
    storage = InMemoryStorage()

    # Save executions for different functions
    for func in ["func_a", "func_b", "func_a"]:
        context = ExecutionContext(
            execution_id=f"test-{func}-{id(func)}",
            function_name=func,
            inputs={"args": (), "kwargs": {}},
        )
        await storage.save_execution(context)

    # List by function name
    func_a_executions = await storage.list_executions(function_name="func_a")
    assert len(func_a_executions) == 2

    func_b_executions = await storage.list_executions(function_name="func_b")
    assert len(func_b_executions) == 1


@pytest.mark.asyncio
async def test_inmemory_storage_get_nonexistent():
    """Test retrieving non-existent execution returns None."""
    storage = InMemoryStorage()

    result = await storage.get_execution("nonexistent-id")
    assert result is None


@pytest.mark.asyncio
async def test_inmemory_storage_save_snapshot():
    """Test saving snapshots to InMemory storage."""
    storage = InMemoryStorage()

    context = ExecutionContext(
        execution_id="test-123",
        function_name="test_function",
        inputs={"args": (), "kwargs": {}},
    )

    # Execution must be saved first
    await storage.save_execution(context)

    # Save snapshot
    from governor.core.state import StateSnapshot

    snapshot = StateSnapshot(
        snapshot_id="snap-1",
        execution_id="test-123",
        checkpoint="pre_execution",
        function_args={"args": (42,)},
        function_kwargs={"name": "test"},
    )

    await storage.save_snapshot(snapshot)

    # Retrieve execution and check snapshots
    retrieved = await storage.get_execution("test-123")
    assert retrieved is not None
    assert len(retrieved.snapshots) == 1
    assert retrieved.snapshots[0].checkpoint == "pre_execution"


@pytest.mark.asyncio
async def test_storage_integration_with_govern():
    """Test storage integration with @govern decorator."""
    storage = InMemoryStorage()

    @govern(storage=storage, capture_state=True)
    async def test_function(x: int) -> int:
        return x * 2

    result = await test_function(21)
    assert result == 42

    # Check execution was saved
    executions = await storage.list_executions()
    assert len(executions) > 0
    assert executions[0].function_name == "test_function"
    assert executions[0].status == ExecutionStatus.COMPLETED
    assert executions[0].result == 42


@pytest.mark.asyncio
async def test_storage_captures_failed_execution():
    """Test that storage captures failed executions."""
    storage = InMemoryStorage()

    @govern(storage=storage, capture_state=True)
    async def failing_function() -> None:
        raise ValueError("Test error")

    with pytest.raises(ValueError, match="Test error"):
        await failing_function()

    # Check failed execution was saved
    executions = await storage.list_executions()
    assert len(executions) > 0
    assert executions[0].status == ExecutionStatus.FAILED
    assert "Test error" in executions[0].error


@pytest.mark.asyncio
async def test_storage_with_multiple_snapshots():
    """Test storage with multiple snapshots during execution."""
    storage = InMemoryStorage()

    @govern(storage=storage, capture_state=True)
    async def multi_step_function(x: int) -> int:
        # Pre-execution snapshot created automatically
        intermediate = x * 2
        # Post-execution snapshot created automatically
        return intermediate + 10

    result = await multi_step_function(5)
    assert result == 20

    # Check snapshots were captured
    executions = await storage.list_executions()
    assert len(executions) > 0

    execution = executions[0]
    # Should have pre and post execution snapshots
    assert len(execution.snapshots) >= 1


@pytest.mark.asyncio
async def test_storage_limit_parameter():
    """Test storage list_executions with limit parameter."""
    storage = InMemoryStorage()

    # Save 10 executions
    for i in range(10):
        context = ExecutionContext(
            execution_id=f"test-{i}",
            function_name="test_function",
            inputs={"args": (), "kwargs": {}},
        )
        await storage.save_execution(context)

    # List with limit
    executions = await storage.list_executions(limit=5)
    assert len(executions) == 5


@pytest.mark.asyncio
async def test_storage_persistence_across_calls():
    """Test that storage persists data across multiple function calls."""
    storage = InMemoryStorage()

    @govern(storage=storage, capture_state=True)
    async def tracked_function(value: int) -> int:
        return value + 1

    # Multiple calls
    await tracked_function(1)
    await tracked_function(2)
    await tracked_function(3)

    # All executions should be stored
    executions = await storage.list_executions()
    assert len(executions) == 3
    assert executions[0].result == 2
    assert executions[1].result == 3
    assert executions[2].result == 4
