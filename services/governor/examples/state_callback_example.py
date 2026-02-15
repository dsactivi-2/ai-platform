"""
State Callback Example

This example demonstrates the on_state_saved callback feature which gives you:
- execution_id (ticket_id) immediately when state is saved
- state object with all execution details
- Ability to return execution_id to client for tracking

Perfect for async long-approval pattern (202 Accepted responses)
"""

import asyncio
from datetime import datetime

from governor import govern, ApprovalPolicy
from governor.approval.handlers import CallbackApprovalHandler
from governor.approval.manager import get_default_approval_manager
from governor.background.queue import BackgroundJobQueue
from governor.background.resume import AutoResumeManager
from governor.storage.memory import InMemoryStorage


# ==============================================================================
# 1. SIMPLE CALLBACK - Just Print
# ==============================================================================

def simple_callback(execution_id: str, state: dict):
    """Simple callback that prints the execution_id and state."""
    print(f"\n🔔 State saved callback triggered!")
    print(f"   Execution ID: {execution_id}")
    print(f"   Function: {state['function_name']}")
    print(f"   Status: {state['status']}")
    print(f"   Checkpoint: {state['checkpoint']}")
    if state.get('timeout'):
        print(f"   ⚠️  Timeout occurred - async pattern triggered")


@govern(
    policies=[ApprovalPolicy(approvers=["admin"], timeout_seconds=2)],
    capture_state=True,
    on_state_saved=simple_callback  # ← GET CALLBACK WHEN STATE IS SAVED
)
async def simple_operation(data: str):
    """Operation with simple callback."""
    return {"result": data}


# ==============================================================================
# 2. TRACK EXECUTION IDs - Store for Client Response
# ==============================================================================

# Global tracker to store execution IDs
execution_tracker = {}


def track_execution(execution_id: str, state: dict):
    """Track execution_id to return to client."""
    execution_tracker[execution_id] = {
        "execution_id": execution_id,
        "function": state["function_name"],
        "status": state["status"],
        "started_at": datetime.now().isoformat(),
        "timeout": state.get("timeout", False),
    }

    if state.get("timeout"):
        print(f"\n📋 Client should receive:")
        print(f"   HTTP 202 Accepted")
        print(f"   {{")
        print(f'     "status": "awaiting_approval",')
        print(f'     "execution_id": "{execution_id}",')
        print(f'     "poll_url": "/api/status/{execution_id}",')
        print(f'     "message": "Pending approval - check status later"')
        print(f"   }}")


@govern(
    policies=[ApprovalPolicy(approvers=["admin"], timeout_seconds=2)],
    capture_state=True,
    on_state_saved=track_execution
)
async def tracked_operation(amount: float, recipient: str):
    """Operation that tracks execution_id."""
    return {"amount": amount, "recipient": recipient, "status": "completed"}


# ==============================================================================
# 3. FASTAPI INTEGRATION - Return 202 Accepted
# ==============================================================================

# Simulated FastAPI pattern
class ClientResponse:
    """Simulates capturing execution_id for FastAPI response."""

    def __init__(self):
        self.execution_id = None
        self.state = None

    def capture(self, execution_id: str, state: dict):
        """Capture execution_id to return in response."""
        self.execution_id = execution_id
        self.state = state


# Create response capture instance
response = ClientResponse()


@govern(
    policies=[ApprovalPolicy(approvers=["cfo"], timeout_seconds=2)],
    capture_state=True,
    on_state_saved=response.capture  # ← CAPTURE FOR RESPONSE
)
async def wire_transfer(amount: float, recipient: str):
    """Wire transfer that captures execution_id for API response."""
    return {
        "transaction_id": f"TXN-{amount}",
        "amount": amount,
        "recipient": recipient,
        "status": "completed"
    }


async def simulate_api_endpoint():
    """Simulates FastAPI endpoint with 202 Accepted response."""
    print("\n" + "=" * 70)
    print("FASTAPI PATTERN: Return 202 Accepted with execution_id")
    print("=" * 70)

    print("\n📥 Client Request: POST /api/wire-transfer")
    print("   {\"amount\": 50000, \"recipient\": \"BigCorp\"}")

    try:
        # Try to execute (will timeout for async pattern)
        result = await wire_transfer(amount=50000, recipient="BigCorp")
        print(f"\n✅ Immediate Response: {result}")

    except PermissionError as e:
        # Expected - timeout triggered async pattern
        # Return 202 Accepted with execution_id captured in callback

        print(f"\n📤 API Response: HTTP 202 Accepted")
        print(f"   {{")
        print(f'     "status": "awaiting_approval",')
        print(f'     "execution_id": "{response.execution_id}",')
        print(f'     "function": "{response.state["function_name"]}",')
        print(f'     "poll_url": "/api/status/{response.execution_id}",')
        print(f'     "message": "Pending CFO approval"')
        print(f"   }}")

        print(f"\n💡 Client can now:")
        print(f"   • Poll: GET /api/status/{response.execution_id}")
        print(f"   • Wait for webhook notification")
        print(f"   • Check status periodically")


# ==============================================================================
# 4. EXTERNAL NOTIFICATION - Send to Monitoring System
# ==============================================================================

async def notify_monitoring_system(execution_id: str, state: dict):
    """Send notification to external monitoring system."""
    # Simulates sending to DataDog, Prometheus, Slack, etc.
    print(f"\n📊 Sending to monitoring system:")
    print(f"   Metric: execution.started")
    print(f"   Tags: function={state['function_name']}, status={state['status']}")
    print(f"   Execution ID: {execution_id}")

    if state.get("timeout"):
        print(f"   Alert: Approval timeout - async pattern triggered")


@govern(
    policies=[ApprovalPolicy(approvers=["admin"], timeout_seconds=2)],
    capture_state=True,
    on_state_saved=notify_monitoring_system
)
async def monitored_operation(data: dict):
    """Operation that sends metrics to monitoring system."""
    return {"processed": data}


# ==============================================================================
# 5. DATABASE STORAGE - Store in Your Own DB
# ==============================================================================

# Simulated database
custom_database = []


def store_in_database(execution_id: str, state: dict):
    """Store execution info in your own database."""
    record = {
        "id": execution_id,
        "function": state["function_name"],
        "status": state["status"],
        "checkpoint": state["checkpoint"],
        "inputs": state["inputs"],
        "created_at": state.get("captured_at", datetime.now().isoformat()),
        "needs_approval": state.get("approval_required", False),
        "is_async": state.get("timeout", False),
    }

    custom_database.append(record)

    print(f"\n💾 Stored in custom database:")
    print(f"   ID: {record['id']}")
    print(f"   Function: {record['function']}")
    print(f"   Needs Approval: {record['needs_approval']}")
    print(f"   Async Pattern: {record['is_async']}")


@govern(
    policies=[ApprovalPolicy(approvers=["admin"], timeout_seconds=2)],
    capture_state=True,
    on_state_saved=store_in_database
)
async def database_tracked_operation(data: dict):
    """Operation that stores execution in custom database."""
    return {"result": data}


# ==============================================================================
# 6. COMPLETE ASYNC EXAMPLE - Production Pattern
# ==============================================================================

# Storage
storage = InMemoryStorage()

# Execution tracking
pending_executions = {}


def handle_async_approval(execution_id: str, state: dict):
    """
    Complete handler for async approval pattern.

    This is what you'd use in production to:
    - Track execution_id
    - Return 202 to client
    - Store for later retrieval
    """
    # Store execution info
    pending_executions[execution_id] = {
        "execution_id": execution_id,
        "function": state["function_name"],
        "status": state["status"],
        "inputs": state["inputs"],
        "captured_at": state.get("captured_at"),
        "poll_url": f"/api/executions/{execution_id}",
    }

    # Log for debugging
    print(f"\n🎫 Execution tracked:")
    print(f"   Ticket ID: {execution_id}")
    print(f"   Function: {state['function_name']}")

    if state.get("timeout"):
        print(f"\n   ⏰ Timeout triggered - State saved to database")
        print(f"   📋 Return to client:")
        print(f"      {{\"execution_id\": \"{execution_id}\", \"status\": \"pending\"}}")


# Approval callback
async def cfo_approval(exec_id, _func_name, inputs, approvers):
    """CFO approval via email (takes hours)."""
    print(f"\n📧 Email sent to: {', '.join(approvers)}")
    print(f"   Approve: https://app.com/approve/{exec_id}")

    # Simulate approval coming later
    async def approve_later():
        await asyncio.sleep(3)
        print(f"\n✅ [LATER] CFO approved {exec_id}")

        manager = get_default_approval_manager()
        manager.provide_decision(exec_id, approved=True, approver="cfo", reason="OK")

    asyncio.create_task(approve_later())

    # Wait longer than timeout
    await asyncio.sleep(100)
    return (False, "system", "Email sent")


@govern(
    policies=[ApprovalPolicy(approvers=["cfo"], timeout_seconds=2, on_timeout="reject")],
    approval_handler=CallbackApprovalHandler(callback=cfo_approval),
    capture_state=True,
    storage=storage,
    on_state_saved=handle_async_approval  # ← PRODUCTION CALLBACK
)
async def production_transfer(amount: float, recipient: str):
    """Production wire transfer with complete async pattern."""
    print(f"   💰 Processing ${amount:,.2f} to {recipient}")
    return {"amount": amount, "recipient": recipient, "status": "completed"}


async def production_example():
    """Complete production example."""
    print("\n" + "=" * 70)
    print("PRODUCTION ASYNC PATTERN")
    print("=" * 70)

    # Setup background worker
    job_queue = BackgroundJobQueue()
    await job_queue.start()

    auto_resume = AutoResumeManager(storage=storage, job_queue=job_queue)
    auto_resume.register_function("production_transfer", production_transfer)
    await auto_resume.start()

    print("\n📥 Client: POST /api/wire-transfer {amount: 50000, ...}")

    try:
        result = await production_transfer(amount=50000, recipient="BigCorp")
        print(f"✅ Result: {result}")
    except PermissionError:
        # Get execution_id from tracking
        latest = list(pending_executions.values())[-1]

        print(f"\n📤 API Response: HTTP 202 Accepted")
        print(f"   {{")
        print(f'     "execution_id": "{latest["execution_id"]}",')
        print(f'     "status": "pending_approval",')
        print(f'     "poll_url": "{latest["poll_url"]}"')
        print(f"   }}")

    # Wait for approval and auto-resume
    await asyncio.sleep(5)

    print(f"\n✅ Execution completed via auto-resume")

    # Cleanup
    await auto_resume.stop()
    await job_queue.stop()


# ==============================================================================
# DEMO
# ==============================================================================

async def main():
    """Run all examples."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "STATE CALLBACK EXAMPLES" + " " * 30 + "║")
    print("╚" + "═" * 68 + "╝")

    # Example 1: Simple callback
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Simple Callback")
    print("=" * 70)
    try:
        await simple_operation("test data")
    except PermissionError:
        pass

    # Example 2: Track execution
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Track Execution IDs")
    print("=" * 70)
    try:
        await tracked_operation(amount=5000, recipient="Acme")
    except PermissionError:
        pass

    print(f"\n📊 Tracked executions: {len(execution_tracker)}")
    for exec_id, info in execution_tracker.items():
        print(f"   {exec_id[:8]}... → {info['function']} ({info['status']})")

    # Example 3: FastAPI pattern
    await simulate_api_endpoint()

    # Example 4: Monitoring
    print("\n" + "=" * 70)
    print("EXAMPLE 4: External Monitoring")
    print("=" * 70)
    try:
        await monitored_operation({"key": "value"})
    except PermissionError:
        pass

    # Example 5: Database storage
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Custom Database Storage")
    print("=" * 70)
    try:
        await database_tracked_operation({"data": "example"})
    except PermissionError:
        pass

    print(f"\n💾 Database records: {len(custom_database)}")

    # Example 6: Production pattern
    await production_example()

    # Summary
    print("\n" + "=" * 70)
    print("✅ EXAMPLES COMPLETE")
    print("=" * 70)

    print("\n🎯 Key Takeaways:")
    print("   1. on_state_saved callback gives you execution_id immediately")
    print("   2. State object contains all execution details")
    print("   3. Perfect for returning 202 Accepted in async pattern")
    print("   4. Can track, store, or notify external systems")
    print("   5. Callback triggered BEFORE timeout exception is raised")

    print("\n💡 Production Use Cases:")
    print("   • Return execution_id to client for tracking")
    print("   • Store in your own database")
    print("   • Send to monitoring/observability systems")
    print("   • Trigger external workflows")
    print("   • Generate support tickets")

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
