"""
Approval Patterns: Sync Wait vs Async Job Queue

This example demonstrates the two patterns for handling approvals:
1. Sync Wait Pattern - For short timeouts (seconds to minutes)
2. Async Job Pattern - For long timeouts (hours to days)
"""

import asyncio
from datetime import datetime

from governor import govern, ApprovalPolicy
from governor.approval.handlers import CallbackApprovalHandler
from governor.approval.manager import get_default_approval_manager
from governor.background.queue import BackgroundJobQueue
from governor.background.resume import AutoResumeManager
from governor.storage.memory import InMemoryStorage


# Shared storage
storage = InMemoryStorage()


# ==============================================================================
# PATTERN 1: SYNC WAIT - Connection Stays Open
# ==============================================================================
# Use for: Interactive approvals with SHORT timeouts (< 5 minutes)
# Pros: Simple, immediate response when approved
# Cons: Connection must stay open, lost on restart, doesn't scale
# ==============================================================================

async def pattern1_sync_wait() -> None:
    """
    Pattern 1: Synchronous Wait

    Flow:
    1. Request comes in
    2. Approval required → System WAITS (connection stays open)
    3. Approver gets notification
    4. Approver approves (within timeout)
    5. Execution continues immediately
    6. Response returned

    **Connection stays open the entire time!**
    """
    print("=" * 70)
    print("PATTERN 1: Sync Wait (Connection Stays Open)")
    print("=" * 70)

    # Simulate quick approval callback
    async def quick_approval_callback(exec_id, func_name, inputs, approvers):
        """Simulates Slack/API approval within 2 seconds."""
        print(f"\n📱 Approval request sent to: {', '.join(approvers)}")
        print(f"   Function: {func_name}")
        print(f"   Waiting for response...")

        # Simulate approval delay (2 seconds)
        await asyncio.sleep(2)

        # Simulate approval
        print(f"   ✓ Approved by {approvers[0]}")
        return (True, approvers[0], "Looks good!")

    # Create handler with quick callback
    handler = CallbackApprovalHandler(callback=quick_approval_callback)

    # Govern with SHORT timeout
    @govern(
        policies=[
            ApprovalPolicy(
                approvers=["admin@company.com"],
                timeout_seconds=10,  # Short timeout (10 seconds)
            )
        ],
        approval_handler=handler,
        storage=storage,
    )
    async def quick_operation(data: dict) -> dict:
        """Operation that needs quick approval."""
        print(f"\n   Executing operation with: {data}")
        return {"status": "completed", "data": data}

    print("\n1. Making request (connection will stay open)...")
    print("   ⏳ Waiting for approval (connection open)...")

    start = asyncio.get_event_loop().time()

    # This BLOCKS until approval received or timeout
    result = await quick_operation({"action": "deploy"})

    elapsed = asyncio.get_event_loop().time() - start

    print(f"\n   ✓ Response received after {elapsed:.1f}s")
    print(f"   Result: {result}")
    print("\n   Note: HTTP connection was open for entire {:.1f}s".format(elapsed))


# ==============================================================================
# PATTERN 2: ASYNC JOB QUEUE - Immediate Return
# ==============================================================================
# Use for: Business approvals with LONG timeouts (hours to days)
# Pros: Scales, survives restarts, no connection overhead
# Cons: More complex, requires polling or webhooks
# ==============================================================================

async def pattern2_async_job() -> None:
    """
    Pattern 2: Async Job Queue

    Flow:
    1. Request comes in
    2. Approval required → Store state, return 202 Accepted IMMEDIATELY
    3. Connection closes
    4. Approver gets notification (hours later)
    5. Approver approves
    6. Background worker resumes execution
    7. Client polls or gets webhook notification

    **Connection closes immediately! Client polls for result.**
    """
    print("\n" + "=" * 70)
    print("PATTERN 2: Async Job Queue (Immediate Return)")
    print("=" * 70)

    # Create background job queue
    job_queue = BackgroundJobQueue()
    await job_queue.start()

    # Create auto-resume manager
    auto_resume = AutoResumeManager(storage=storage, job_queue=job_queue)
    await auto_resume.start()

    # Track job IDs
    pending_jobs = {}

    # Simulate approval that happens LATER
    async def delayed_approval_callback(exec_id, func_name, inputs, approvers):
        """
        Simulates email approval that happens hours later.

        In production:
        - Send email with approval link
        - Email contains execution_id
        - When user clicks link, it calls approval API
        - This callback returns immediately (doesn't wait for email)
        """
        print(f"\n📧 Email sent to: {', '.join(approvers)}")
        print(f"   Subject: Approval needed for {func_name}")
        print(f"   Execution ID: {exec_id}")
        print(f"   Approval link: https://approval.company.com/approve/{exec_id}")

        # Store the execution as pending
        print(f"\n   ⏸️  Execution PAUSED - stored in database")
        print(f"   🔁 Returning 202 Accepted to client...")

        # In production, this would:
        # 1. Send the email
        # 2. Return None (no immediate decision)
        # 3. Later, when user clicks link, webhook calls provide_decision()

        # For demo, we'll simulate approval after a delay
        async def approve_later():
            await asyncio.sleep(3)  # Simulate hours passing
            print(f"\n\n🔔 [LATER] User clicked approval link for {exec_id}")

            # Approve via approval manager
            manager = get_default_approval_manager()
            manager.provide_decision(
                execution_id=exec_id,
                approved=True,
                approver=approvers[0],
                reason="Approved via email",
            )
            print(f"   ✓ Approval recorded")
            print(f"   🔄 Auto-resume will pick this up...")

        # Schedule the delayed approval
        asyncio.create_task(approve_later())

        # Return "pending" - no immediate decision
        # This will cause a timeout, which triggers async pattern
        await asyncio.sleep(60)  # Wait longer than timeout
        return (False, "system", "Timeout - will resume on approval")

    handler = CallbackApprovalHandler(callback=delayed_approval_callback)

    # Define the governed function
    @govern(
        policies=[
            ApprovalPolicy(
                approvers=["cfo@company.com"],
                timeout_seconds=5,  # Short timeout triggers async pattern
                on_timeout="reject",  # Timeout = go async
            )
        ],
        approval_handler=handler,
        storage=storage,
        capture_state=True,  # IMPORTANT: Must capture state for resume
    )
    async def long_running_operation(data: dict) -> dict:
        """Operation that needs approval (might take hours)."""
        print(f"\n   🚀 Executing operation with: {data}")
        await asyncio.sleep(0.5)  # Simulate work
        return {"status": "completed", "data": data, "timestamp": str(datetime.now())}

    # Register function for auto-resume
    auto_resume.register_function("long_running_operation", long_running_operation)

    print("\n1. Making request...")

    try:
        # This will timeout after 5s, but state is saved
        result = await long_running_operation({"action": "wire_transfer", "amount": 50000})
        print(f"   ✓ Immediate result: {result}")
    except Exception as e:
        # Expected - times out because approval takes too long
        print(f"\n   ⏸️  Request timed out (expected for async pattern)")
        print(f"   📋 State saved to database")
        print(f"   📊 Client receives: 202 Accepted")
        print(f"      {{")
        print(f'        "status": "awaiting_approval",')
        print(f'        "execution_id": "exec-123",')
        print(f'        "poll_url": "/executions/exec-123"')
        print(f"      }}")

    print(f"\n2. Client connection closed (can disconnect)")
    print(f"   💤 Server can even restart - state is in database")

    print(f"\n3. Waiting for approval... (simulating hours passing)")

    # Wait for auto-resume to pick up the approved execution
    await asyncio.sleep(5)

    print(f"\n4. Checking execution status:")
    executions = await storage.list_executions(function_name="long_running_operation")
    if executions:
        latest = executions[0]
        print(f"   Status: {latest.status}")
        print(f"   Started: {latest.started_at}")
        if latest.completed_at:
            print(f"   Completed: {latest.completed_at}")
            print(f"   Result: {latest.outputs}")

    # Stop background services
    await auto_resume.stop()
    await job_queue.stop()


# ==============================================================================
# PATTERN COMPARISON
# ==============================================================================

async def comparison_table() -> None:
    """Show comparison of both patterns."""
    print("\n" + "=" * 70)
    print("PATTERN COMPARISON")
    print("=" * 70)

    comparison = """
┌─────────────────────┬───────────────────────┬────────────────────────┐
│ Aspect              │ Sync Wait             │ Async Job Queue        │
├─────────────────────┼───────────────────────┼────────────────────────┤
│ Timeout             │ Seconds to minutes    │ Hours to days          │
│ Connection          │ Stays open            │ Closes immediately     │
│ Response            │ Immediate when done   │ 202 Accepted           │
│ Survives restart    │ ❌ No                 │ ✅ Yes                 │
│ Scales              │ ❌ Limited            │ ✅ Yes                 │
│ Complexity          │ ✅ Simple             │ ⚠️  More complex       │
│ Best for            │ Interactive approvals │ Business approvals     │
│ Example             │ Slack button click    │ Email approval link    │
└─────────────────────┴───────────────────────┴────────────────────────┘

WHEN TO USE:

✅ Use Sync Wait when:
   - Timeout is SHORT (< 5 minutes)
   - Approver is online and responsive
   - Interactive approval (Slack, CLI, web form)
   - Simple deployment

✅ Use Async Job when:
   - Timeout is LONG (hours to days)
   - Approver might not be available immediately
   - Email approvals, business process approvals
   - Need to survive server restarts
   - Production deployment at scale
"""
    print(comparison)


async def main() -> None:
    """Run all pattern examples."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "APPROVAL PATTERNS: SYNC VS ASYNC" + " " * 20 + "║")
    print("╚" + "═" * 68 + "╝")

    await pattern1_sync_wait()
    await pattern2_async_job()
    await comparison_table()

    print("\n" + "=" * 70)
    print("✓ Pattern demonstrations complete!")
    print("\nKey Takeaways:")
    print("  • Pattern 1 (Sync): Connection stays open, simple but limited")
    print("  • Pattern 2 (Async): State stored, scalable, production-ready")
    print("  • Choose based on timeout requirements and scale needs")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
