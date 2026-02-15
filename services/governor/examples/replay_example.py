"""State replay and continuation example."""

import asyncio
from governor import govern
from governor.storage.memory import InMemoryStorage
from governor.replay.engine import ReplayEngine
from governor.core.context import ExecutionContext


# Shared storage for replay
storage = InMemoryStorage()


@govern(capture_state=True, storage=storage)
async def multi_step_process(data: dict) -> dict:
    """
    Multi-step process that can be replayed.

    This simulates a complex agentic workflow with multiple steps.
    """
    print(f"Step 1: Validate input - {data}")
    await asyncio.sleep(0.1)

    print(f"Step 2: Process data")
    processed = {"input": data, "validated": True}
    await asyncio.sleep(0.1)

    print(f"Step 3: Generate output")
    result = {"status": "success", "data": processed, "timestamp": "2025-10-18"}
    await asyncio.sleep(0.1)

    return result


@govern(capture_state=True, storage=storage)
async def failing_operation(value: int) -> int:
    """Operation that might fail."""
    print(f"Processing value: {value}")

    if value > 100:
        raise ValueError(f"Value {value} exceeds maximum allowed (100)")

    return value * 2


async def main() -> None:
    """Run replay examples."""
    print("=" * 70)
    print("State Replay and Continuation Examples")
    print("=" * 70)

    # Initialize replay engine
    replay = ReplayEngine(storage=storage)

    # Example 1: Successful execution and replay
    print("\n1. Execute and replay successful operation:")
    result = await multi_step_process({"name": "test", "value": 42})
    print(f"   Result: {result}")

    # Get execution details
    executions = await storage.list_executions(function_name="multi_step_process")
    if executions:
        exec_id = executions[0].execution_id
        print(f"   Execution ID: {exec_id}")

        # Get snapshots
        snapshots = await replay.get_snapshots(exec_id)
        print(f"   Snapshots captured: {len(snapshots)}")
        for snap in snapshots:
            print(f"     - {snap.checkpoint} at {snap.captured_at}")

        # Replay for debugging
        print("\n   Replaying execution:")
        replay_info = await replay.replay_for_debugging(exec_id)
        print(f"     Function: {replay_info['function_name']}")
        print(f"     Status: {replay_info['status']}")
        print(f"     Checkpoints: {', '.join(replay_info['checkpoints'])}")

    # Example 2: Failed execution
    print("\n2. Execute operation that will fail:")
    try:
        result = await failing_operation(150)
    except ValueError as e:
        print(f"   Failed as expected: {e}")

        # Find failed execution
        failed = await replay.list_failed_executions()
        if failed:
            exec_id = failed[0].execution_id
            print(f"   Failed execution ID: {exec_id}")
            print(f"   Error: {failed[0].error}")

            # Get last snapshot before failure
            last_snapshot = await replay.get_last_snapshot(exec_id)
            if last_snapshot:
                print(f"   Last checkpoint: {last_snapshot.checkpoint}")
                print("   State can be restored from this point for retry")

    # Example 3: Continue from last snapshot
    print("\n3. Successful execution with state tracking:")
    result = await failing_operation(50)
    print(f"   Result: {result}")

    executions = await storage.list_executions(
        function_name="failing_operation", status="completed"
    )
    if executions:
        exec_id = executions[0].execution_id

        # Continue from last checkpoint
        print(f"\n   Continuing from execution {exec_id}:")
        continued_result = await replay.continue_from_last(
            exec_id, failing_operation
        )
        print(f"   Continued result: {continued_result}")

    # Example 4: List all executions
    print("\n4. All executions summary:")
    all_executions = await storage.list_executions(limit=100)
    for exec_ctx in all_executions:
        print(
            f"   - {exec_ctx.function_name}: {exec_ctx.status} "
            f"(duration: {exec_ctx.duration_ms}ms)"
        )

    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
