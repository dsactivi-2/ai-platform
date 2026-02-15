"""
Manual Resume Example

This example shows how developers can manually control when to resume
executions based on webhooks or custom triggers, rather than auto-resume.

Use cases:
- Webhook from external system (Jira, Slack, etc.)
- Admin dashboard approval
- Custom business logic before resume
- Scheduled resume (cron jobs)
"""

import asyncio
from datetime import datetime

from governor import govern, ApprovalPolicy
from governor.approval.handlers import CallbackApprovalHandler
from governor.background.queue import BackgroundJobQueue
from governor.background.resume import AutoResumeManager
from governor.storage.memory import InMemoryStorage


# ==============================================================================
# SETUP
# ==============================================================================

storage = InMemoryStorage()
pending_executions = {}  # Track pending executions for manual resume


def track_pending(execution_id: str, state: dict):
    """Track execution_id when timeout occurs."""
    if state.get("timeout"):
        pending_executions[execution_id] = {
            "function": state["function_name"],
            "inputs": state["inputs"],
            "status": "pending_manual_approval",
            "created_at": datetime.now().isoformat()
        }
        print(f"\n📋 Execution {execution_id} is pending manual approval")


# ==============================================================================
# GOVERNED FUNCTION
# ==============================================================================

async def send_approval_request(exec_id, _func_name, inputs, approvers):
    """Simulate sending approval request (email, Slack, etc.)."""
    print(f"\n📧 Approval request sent to: {', '.join(approvers)}")
    print(f"   Execution ID: {exec_id}")
    print(f"   Inputs: {inputs}")
    print(f"   Approve via webhook: POST /webhook/approve/{exec_id}")

    # Don't auto-approve - wait for manual webhook trigger
    await asyncio.sleep(100)
    return (False, "system", "Waiting for webhook")


@govern(
    policies=[
        ApprovalPolicy(
            approvers=["admin@company.com"],
            timeout_seconds=2,  # Short timeout for demo
            on_timeout="reject"
        )
    ],
    approval_handler=CallbackApprovalHandler(callback=send_approval_request),
    storage=storage,
    capture_state=True,
    on_state_saved=track_pending  # Track for manual resume
)
async def critical_operation(amount: float, description: str):
    """Critical operation requiring manual approval."""
    print(f"\n   ✅ Executing operation:")
    print(f"      Amount: ${amount:,.2f}")
    print(f"      Description: {description}")

    await asyncio.sleep(0.5)  # Simulate work

    return {
        "status": "completed",
        "amount": amount,
        "description": description,
        "timestamp": datetime.now().isoformat()
    }


# ==============================================================================
# MANUAL RESUME HANDLERS
# ==============================================================================

class WebhookSimulator:
    """Simulates webhook endpoints for manual resume."""

    def __init__(self, auto_resume: AutoResumeManager):
        self.auto_resume = auto_resume

    async def approve_execution(self, execution_id: str, approver: str, reason: str):
        """
        Webhook endpoint: POST /webhook/approve/{execution_id}

        This is called by:
        - External approval system (Jira, ServiceNow)
        - Slack bot (user clicks button)
        - Admin dashboard (admin clicks approve)
        - Email link (user clicks approve)
        """
        print(f"\n{'='*70}")
        print(f"WEBHOOK TRIGGERED: Manual Approval")
        print(f"{'='*70}")

        # 1. Validate execution exists
        context = await storage.get_execution(execution_id)
        if not context:
            return {"error": "Execution not found"}

        # 2. Check if pending
        if execution_id not in pending_executions:
            return {"error": "Execution not pending approval"}

        print(f"\n   Approver: {approver}")
        print(f"   Reason: {reason}")
        print(f"   Execution: {execution_id}")

        # 3. Record approval
        from governor.approval.manager import get_default_approval_manager
        manager = get_default_approval_manager()
        manager.provide_decision(
            execution_id=execution_id,
            approved=True,
            approver=approver,
            reason=reason
        )

        # 4. MANUALLY RESUME EXECUTION
        print(f"\n   🔄 Manually resuming execution...")

        try:
            result = await self.auto_resume.resume_by_execution_id(
                execution_id=execution_id,
                func=critical_operation  # Provide function
            )

            # 5. Update tracking
            pending_executions.pop(execution_id, None)

            print(f"\n   ✅ Execution completed via manual resume!")
            print(f"   Result: {result}")

            return {
                "status": "resumed_and_completed",
                "execution_id": execution_id,
                "approver": approver,
                "result": result
            }

        except Exception as e:
            return {
                "error": f"Failed to resume: {str(e)}",
                "execution_id": execution_id
            }

    async def reject_execution(self, execution_id: str, rejector: str, reason: str):
        """Webhook endpoint: POST /webhook/reject/{execution_id}"""
        print(f"\n{'='*70}")
        print(f"WEBHOOK TRIGGERED: Manual Rejection")
        print(f"{'='*70}")

        print(f"\n   ❌ Execution rejected by {rejector}")
        print(f"   Reason: {reason}")

        # Record rejection (don't resume)
        from governor.approval.manager import get_default_approval_manager
        manager = get_default_approval_manager()
        manager.provide_decision(
            execution_id=execution_id,
            approved=False,
            approver=rejector,
            reason=reason
        )

        pending_executions.pop(execution_id, None)

        return {
            "status": "rejected",
            "execution_id": execution_id,
            "rejector": rejector,
            "message": "Execution will not be resumed"
        }

    async def conditional_resume(self, execution_id: str, approver: str):
        """
        Webhook endpoint with custom business logic.
        Developer can add ANY conditions before resume.
        """
        print(f"\n{'='*70}")
        print(f"WEBHOOK TRIGGERED: Conditional Resume")
        print(f"{'='*70}")

        # Get execution
        context = await storage.get_execution(execution_id)
        if not context:
            return {"error": "Execution not found"}

        # Get original inputs from snapshot
        from governor.replay import ReplayEngine
        replay = ReplayEngine(storage)
        snapshot = await replay.get_last_snapshot(execution_id)
        state = snapshot.restore_state()
        inputs = state.get("function_kwargs", {})

        # CUSTOM BUSINESS LOGIC - Developer decides!
        amount = inputs.get("amount", 0)

        print(f"\n   Checking business rules...")

        # Rule 1: Amount limit
        if amount > 100000:
            print(f"   ❌ Amount ${amount:,.2f} exceeds limit ($100,000)")
            return {
                "status": "blocked",
                "reason": "Amount too high - board approval required"
            }

        # Rule 2: Time constraint
        from datetime import timedelta
        age = datetime.now() - context.started_at
        if age > timedelta(days=7):
            print(f"   ❌ Execution too old ({age.days} days)")
            return {
                "status": "expired",
                "reason": "Execution expired - please restart"
            }

        # Rule 3: Custom check (simulate external API)
        risk_score = await self._check_risk_score(execution_id)
        if risk_score > 0.8:
            print(f"   ❌ High risk score: {risk_score}")
            return {
                "status": "blocked",
                "reason": "High risk - manual review required"
            }

        # All checks passed - RESUME!
        print(f"   ✅ All business rules passed")
        print(f"   🔄 Resuming execution...")

        result = await self.auto_resume.resume_by_execution_id(
            execution_id=execution_id,
            func=critical_operation
        )

        return {
            "status": "conditionally_resumed",
            "execution_id": execution_id,
            "result": result
        }

    async def _check_risk_score(self, execution_id: str) -> float:
        """Simulate external risk check."""
        # In production: call external API, ML model, etc.
        return 0.3  # Low risk


# ==============================================================================
# DEMO
# ==============================================================================

async def demo_manual_resume():
    """Demonstrate manual resume via webhook."""

    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + " " * 15 + "MANUAL RESUME DEMONSTRATION" + " " * 26 + "║")
    print("║" + " " * 20 + "(Webhook-Triggered)" + " " * 28 + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")

    # Setup
    job_queue = BackgroundJobQueue()
    await job_queue.start()

    # Create auto-resume manager (but don't start auto-resume!)
    auto_resume = AutoResumeManager(storage=storage, job_queue=job_queue)
    auto_resume.register_function("critical_operation", critical_operation)

    # NOTE: We're NOT calling auto_resume.start()
    # This means NO automatic resume - only manual via webhook!
    print("\n🔧 Setup:")
    print("   ✓ Background job queue started")
    print("   ✓ AutoResumeManager created")
    print("   ✓ Function registered")
    print("   ⚠️  Auto-resume NOT started (manual control only!)")

    # Create webhook simulator
    webhook = WebhookSimulator(auto_resume)

    # ====================
    # SCENARIO 1: Manual Approve
    # ====================
    print("\n\n" + "=" * 70)
    print("SCENARIO 1: Manual Approval via Webhook")
    print("=" * 70)

    print("\n1️⃣  Client makes request...")

    execution_id_1 = None
    try:
        result = await critical_operation(
            amount=25000,
            description="Equipment purchase"
        )
        print(f"   Result: {result}")
    except PermissionError:
        # Expected - timeout occurred
        print(f"\n   ⏰ Timeout occurred - state saved")

        # Get execution_id from tracking
        execution_id_1 = list(pending_executions.keys())[0]
        print(f"\n   📋 Client receives:")
        print(f"      {{")
        print(f'        "status": "pending_approval",')
        print(f'        "execution_id": "{execution_id_1}",')
        print(f'        "webhook_url": "/webhook/approve/{execution_id_1}"')
        print(f"      }}")

    # Simulate webhook call (from Slack, Jira, etc.)
    print(f"\n2️⃣  [LATER] External system triggers webhook...")
    await asyncio.sleep(1)

    response = await webhook.approve_execution(
        execution_id=execution_id_1,
        approver="admin@company.com",
        reason="Approved - legitimate business expense"
    )

    print(f"\n   Webhook response: {response['status']}")

    # ====================
    # SCENARIO 2: Manual Reject
    # ====================
    print("\n\n" + "=" * 70)
    print("SCENARIO 2: Manual Rejection via Webhook")
    print("=" * 70)

    print("\n1️⃣  Client makes request...")

    execution_id_2 = None
    try:
        result = await critical_operation(
            amount=15000,
            description="Suspicious purchase"
        )
    except PermissionError:
        execution_id_2 = list(pending_executions.keys())[0]
        print(f"\n   ⏰ Timeout occurred")
        print(f"   📋 Execution ID: {execution_id_2}")

    print(f"\n2️⃣  [LATER] Admin rejects via webhook...")
    await asyncio.sleep(1)

    response = await webhook.reject_execution(
        execution_id=execution_id_2,
        rejector="security@company.com",
        reason="Suspicious activity - blocked"
    )

    print(f"\n   Webhook response: {response['status']}")

    # ====================
    # SCENARIO 3: Conditional Resume
    # ====================
    print("\n\n" + "=" * 70)
    print("SCENARIO 3: Conditional Resume with Business Logic")
    print("=" * 70)

    print("\n1️⃣  Client makes request...")

    execution_id_3 = None
    try:
        result = await critical_operation(
            amount=50000,
            description="Marketing campaign"
        )
    except PermissionError:
        execution_id_3 = list(pending_executions.keys())[0]
        print(f"\n   ⏰ Timeout occurred")
        print(f"   📋 Execution ID: {execution_id_3}")

    print(f"\n2️⃣  [LATER] Webhook with custom business logic...")
    await asyncio.sleep(1)

    response = await webhook.conditional_resume(
        execution_id=execution_id_3,
        approver="cfo@company.com"
    )

    print(f"\n   Webhook response: {response['status']}")

    # ====================
    # Show Pending Executions
    # ====================
    print("\n\n" + "=" * 70)
    print("PENDING EXECUTIONS STATUS")
    print("=" * 70)

    if pending_executions:
        print(f"\n   Pending: {len(pending_executions)}")
        for exec_id, info in pending_executions.items():
            print(f"   • {exec_id[:8]}... - {info['status']}")
    else:
        print(f"\n   ✅ No pending executions (all processed)")

    # Cleanup
    await job_queue.stop()

    # Summary
    print("\n\n" + "=" * 70)
    print("✅ DEMONSTRATION COMPLETE")
    print("=" * 70)

    print("\n🎯 Key Takeaways:")
    print("   1. Developer has FULL CONTROL over resume")
    print("   2. Resume triggered by webhooks (Jira, Slack, admin, etc.)")
    print("   3. Can add custom business logic before resume")
    print("   4. Can approve, reject, or conditionally resume")
    print("   5. No auto-resume - only manual trigger")

    print("\n💡 Production Use Cases:")
    print("   • Jira ticket approval → webhook triggers resume")
    print("   • Slack button click → webhook triggers resume")
    print("   • Admin dashboard → manual resume button")
    print("   • Cron job → scheduled resume at specific time")
    print("   • External API → conditional resume based on data")

    print("\n📚 See MANUAL_RESUME_GUIDE.md for complete guide")
    print("=" * 70 + "\n")


async def main():
    """Run demonstration."""
    await demo_manual_resume()


if __name__ == "__main__":
    asyncio.run(main())
