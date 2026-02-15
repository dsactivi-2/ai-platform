"""
Financial Approval System - Real-World Example

This example demonstrates a complete financial approval workflow with:
- Multi-tier approval policies based on transaction amount
- Sync approvals for small amounts (< $10,000)
- Async approvals for large amounts (> $10,000)
- State persistence and auto-resume
- Audit logging and compliance
"""

import asyncio
from datetime import datetime

from governor import govern, ApprovalPolicy, AuditPolicy, ValidationPolicy
from governor.approval.handlers import CallbackApprovalHandler
from governor.approval.manager import get_default_approval_manager
from governor.background.queue import BackgroundJobQueue
from governor.background.resume import AutoResumeManager
from governor.storage.memory import InMemoryStorage


# ==============================================================================
# 1. SETUP
# ==============================================================================

# Shared storage (use MongoDB in production)
storage = InMemoryStorage()

# Track transactions
transaction_ledger = []


# ==============================================================================
# 2. BUSINESS LOGIC - FINANCIAL OPERATIONS
# ==============================================================================

class TransactionResult:
    """Result of a financial transaction."""

    def __init__(self, transaction_id: str, status: str, amount: float,
                 recipient: str, timestamp: datetime):
        self.transaction_id = transaction_id
        self.status = status
        self.amount = amount
        self.recipient = recipient
        self.timestamp = timestamp

    def __repr__(self):
        return (f"Transaction({self.transaction_id}, "
                f"${self.amount:,.2f} to {self.recipient}, {self.status})")


# ==============================================================================
# 3. TIER 1: SMALL TRANSACTIONS (Sync Approval)
# ==============================================================================

async def manager_approval_callback(_exec_id, _func_name, inputs, approvers):
    """
    Simulates Slack/Teams approval for small transactions.
    Manager responds within seconds.
    """
    amount = inputs.get("amount", 0)
    recipient = inputs.get("recipient", "Unknown")

    print(f"\n{'='*70}")
    print(f"📱 SLACK NOTIFICATION")
    print(f"{'='*70}")
    print(f"   Channel: #finance-approvals")
    print(f"   To: {', '.join(approvers)}")
    print(f"   ")
    print(f"   🔔 Wire Transfer Approval Required")
    print(f"   Amount: ${amount:,.2f}")
    print(f"   Recipient: {recipient}")
    print(f"   ")
    print(f"   [✓ Approve]  [✗ Reject]")
    print(f"{'='*70}")

    # Simulate quick approval (manager clicks button)
    print(f"\n   ⏳ Waiting for manager response...")
    await asyncio.sleep(2)  # Manager approves within 2 seconds

    print(f"   ✅ APPROVED by {approvers[0]}")
    print(f"   Reason: Transaction within manager approval limits")

    return (True, approvers[0], "Approved via Slack")


@govern(
    policies=[
        ValidationPolicy(
            name="AmountValidation",
            input_validator=lambda inputs: inputs.get("kwargs", {}).get("amount", 0) < 10000
        ),
        ApprovalPolicy(
            approvers=["manager@company.com"],
            timeout_seconds=30,  # Short timeout - sync pattern
            on_timeout="reject"
        ),
        AuditPolicy(
            log_inputs=True,
            log_outputs=True,
            compliance_tags=["financial", "approval"]
        )
    ],
    approval_handler=CallbackApprovalHandler(callback=manager_approval_callback),
    storage=storage,
    capture_state=True
)
async def quick_wire_transfer(amount: float, recipient: str,
                              _account_number: str) -> TransactionResult:
    """
    Quick wire transfer for amounts < $10,000.
    Uses SYNC approval pattern - connection stays open.
    """
    print(f"\n   💸 Processing wire transfer...")
    await asyncio.sleep(0.5)  # Simulate processing

    # Record transaction
    transaction = TransactionResult(
        transaction_id=f"TXN-{len(transaction_ledger) + 1:04d}",
        status="completed",
        amount=amount,
        recipient=recipient,
        timestamp=datetime.now()
    )
    transaction_ledger.append(transaction)

    print(f"   ✓ Transfer completed: {transaction.transaction_id}")
    return transaction


# ==============================================================================
# 4. TIER 2: LARGE TRANSACTIONS (Async Approval)
# ==============================================================================

async def cfo_approval_callback(exec_id, _func_name, inputs, approvers):
    """
    Simulates email approval for large transactions.
    CFO might take hours/days to approve.
    """
    amount = inputs.get("amount", 0)
    recipient = inputs.get("recipient", "Unknown")

    print(f"\n{'='*70}")
    print(f"📧 EMAIL SENT")
    print(f"{'='*70}")
    print(f"   To: {', '.join(approvers)}")
    print(f"   Subject: URGENT - Wire Transfer Approval Required")
    print(f"   ")
    print(f"   Dear CFO,")
    print(f"   ")
    print(f"   A large wire transfer requires your approval:")
    print(f"   ")
    print(f"   Amount:     ${amount:,.2f}")
    print(f"   Recipient:  {recipient}")
    print(f"   Requested:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   ")
    print(f"   Approve: https://approvals.company.com/approve/{exec_id}")
    print(f"   Reject:  https://approvals.company.com/reject/{exec_id}")
    print(f"   ")
    print(f"   This request will expire in 24 hours.")
    print(f"{'='*70}")

    print(f"\n   ⏸️  EXECUTION PAUSED - State saved to database")
    print(f"   🔁 Returning 202 Accepted to client...")
    print(f"   💤 Server can now restart - state is persistent")

    # Simulate email approval happening LATER (async)
    async def approve_later():
        # Simulate time passing (hours in production)
        await asyncio.sleep(5)

        print(f"\n\n{'='*70}")
        print(f"🔔 [3 HOURS LATER] CFO clicked approval link")
        print(f"{'='*70}")

        # CFO approves via webhook
        manager = get_default_approval_manager()
        manager.provide_decision(
            execution_id=exec_id,
            approved=True,
            approver=approvers[0],
            reason="Approved - legitimate business expense"
        )

        print(f"   ✅ Approval recorded in database")
        print(f"   🔄 Auto-resume manager will pick this up...")

    # Schedule delayed approval
    asyncio.create_task(approve_later())

    # Return "pending" - this will timeout and trigger async pattern
    await asyncio.sleep(100)  # Wait longer than timeout
    return (False, "system", "Email sent - awaiting CFO response")


@govern(
    policies=[
        ValidationPolicy(
            name="LargeAmountValidation",
            input_validator=lambda inputs: inputs.get("kwargs", {}).get("amount", 0) >= 10000
        ),
        ApprovalPolicy(
            approvers=["cfo@company.com"],
            timeout_seconds=10,  # Short timeout to trigger async pattern
            on_timeout="reject"
        ),
        AuditPolicy(
            log_inputs=True,
            log_outputs=True,
            compliance_tags=["financial", "approval"]
        )
    ],
    approval_handler=CallbackApprovalHandler(callback=cfo_approval_callback),
    storage=storage,
    capture_state=True  # CRITICAL: Must capture state for resume
)
async def large_wire_transfer(amount: float, recipient: str,
                              _account_number: str) -> TransactionResult:
    """
    Large wire transfer for amounts >= $10,000.
    Uses ASYNC approval pattern - returns immediately, resumes on approval.
    """
    print(f"\n   💰 Processing large wire transfer...")
    await asyncio.sleep(0.5)  # Simulate processing

    # Record transaction
    transaction = TransactionResult(
        transaction_id=f"TXN-{len(transaction_ledger) + 1:04d}",
        status="completed",
        amount=amount,
        recipient=recipient,
        timestamp=datetime.now()
    )
    transaction_ledger.append(transaction)

    print(f"   ✓ Transfer completed: {transaction.transaction_id}")
    return transaction


# ==============================================================================
# 5. DEMONSTRATION
# ==============================================================================

async def demo_small_transaction():
    """Demo: Small transaction with sync approval."""
    print("\n" + "█" * 70)
    print("█" + " " * 68 + "█")
    print("█" + " " * 15 + "SCENARIO 1: SMALL TRANSACTION" + " " * 23 + "█")
    print("█" + " " * 20 + "(Sync Approval Pattern)" + " " * 25 + "█")
    print("█" + " " * 68 + "█")
    print("█" * 70)

    print("\n📋 Client Request:")
    print("   POST /api/wire-transfer")
    print("   {")
    print('     "amount": 5000,')
    print('     "recipient": "Acme Corp",')
    print('     "account": "123-456-7890"')
    print("   }")

    try:
        start_time = datetime.now()

        # Make request - will WAIT for approval
        result = await quick_wire_transfer(
            amount=5000,
            recipient="Acme Corp",
            account_number="123-456-7890"
        )

        duration = (datetime.now() - start_time).total_seconds()

        print(f"\n📤 Client Response (after {duration:.1f}s):")
        print("   HTTP 200 OK")
        print("   {")
        print(f'     "transaction_id": "{result.transaction_id}",')
        print(f'     "status": "{result.status}",')
        print(f'     "amount": {result.amount},')
        print(f'     "recipient": "{result.recipient}"')
        print("   }")
        print(f"\n   ⏱️  Total time: {duration:.1f}s (connection stayed open)")

    except Exception as e:
        print(f"\n❌ Transaction failed: {e}")


async def demo_large_transaction():
    """Demo: Large transaction with async approval."""
    print("\n\n" + "█" * 70)
    print("█" + " " * 68 + "█")
    print("█" + " " * 15 + "SCENARIO 2: LARGE TRANSACTION" + " " * 23 + "█")
    print("█" + " " * 19 + "(Async Approval Pattern)" + " " * 24 + "█")
    print("█" + " " * 68 + "█")
    print("█" * 70)

    print("\n📋 Client Request:")
    print("   POST /api/wire-transfer")
    print("   {")
    print('     "amount": 50000,')
    print('     "recipient": "BigCorp Industries",')
    print('     "account": "987-654-3210"')
    print("   }")

    # Start background services
    print("\n🔧 Starting background services...")
    job_queue = BackgroundJobQueue()
    await job_queue.start()

    auto_resume = AutoResumeManager(storage=storage, job_queue=job_queue)
    auto_resume.register_function("large_wire_transfer", large_wire_transfer)
    await auto_resume.start()
    print("   ✓ Job queue started")
    print("   ✓ Auto-resume manager started")

    try:
        start_time = datetime.now()

        # Make request - will timeout and return immediately
        result = await large_wire_transfer(
            amount=50000,
            recipient="BigCorp Industries",
            account_number="987-654-3210"
        )

        # This won't execute because of timeout
        print(f"\n📤 Immediate response: {result}")

    except Exception:
        # Expected - timeout triggers async pattern
        duration = (datetime.now() - start_time).total_seconds()

        print(f"\n📤 Client Response (after {duration:.1f}s):")
        print("   HTTP 202 Accepted")
        print("   {")
        print('     "status": "awaiting_approval",')
        print('     "execution_id": "exec-123",')
        print('     "message": "Transfer pending CFO approval",')
        print('     "poll_url": "/api/executions/exec-123"')
        print("   }")
        print(f"\n   ⚡ Response time: {duration:.1f}s (connection closed immediately)")
        print(f"   💾 State saved to database")

    # Wait for approval and auto-resume
    print(f"\n⏳ Waiting for CFO approval and auto-resume...")
    await asyncio.sleep(8)  # Wait for approval + resume

    # Check execution status
    print(f"\n📊 Checking execution status...")
    executions = await storage.list_executions(function_name="large_wire_transfer")
    if executions:
        latest = executions[0]
        print(f"\n   Execution ID: {latest.execution_id}")
        print(f"   Status: {latest.status}")
        print(f"   Started: {latest.started_at.strftime('%H:%M:%S')}")
        if latest.completed_at:
            print(f"   Completed: {latest.completed_at.strftime('%H:%M:%S')}")
            print(f"   Result: {latest.outputs}")

    # Cleanup
    await auto_resume.stop()
    await job_queue.stop()


async def show_audit_trail():
    """Show complete audit trail."""
    print("\n\n" + "█" * 70)
    print("█" + " " * 68 + "█")
    print("█" + " " * 25 + "AUDIT TRAIL" + " " * 31 + "█")
    print("█" + " " * 68 + "█")
    print("█" * 70)

    # Show all transactions
    print(f"\n📚 Transaction Ledger ({len(transaction_ledger)} transactions):")
    print("   " + "-" * 66)
    for txn in transaction_ledger:
        print(f"   {txn.transaction_id} | ${txn.amount:>10,.2f} | {txn.recipient:<20} | {txn.status}")
    print("   " + "-" * 66)

    # Show all executions
    all_executions = await storage.list_executions()
    print(f"\n📋 Governance Log ({len(all_executions)} executions):")
    print("   " + "-" * 66)
    for exec_ctx in all_executions:
        status_icon = "✓" if exec_ctx.status == "completed" else "⏳"
        print(f"   {status_icon} {exec_ctx.execution_id} | {exec_ctx.function_name:<25} | {exec_ctx.status}")
    print("   " + "-" * 66)

    # Show all events
    all_events = await storage.list_events()
    print(f"\n📝 Event Log ({len(all_events)} events):")
    print("   " + "-" * 66)
    for event in all_events[:10]:  # Show first 10
        print(f"   {event.timestamp.strftime('%H:%M:%S')} | {event.event_type:<30} | {event.execution_id}")
    if len(all_events) > 10:
        print(f"   ... and {len(all_events) - 10} more events")
    print("   " + "-" * 66)


async def show_pattern_comparison():
    """Show pattern comparison table."""
    print("\n\n" + "█" * 70)
    print("█" + " " * 68 + "█")
    print("█" + " " * 20 + "PATTERN COMPARISON" + " " * 28 + "█")
    print("█" + " " * 68 + "█")
    print("█" * 70)

    comparison = """
┌────────────────────┬─────────────────────┬──────────────────────────┐
│ Aspect             │ Small ($< 10k)      │ Large ($≥ 10k)           │
│                    │ Sync Wait           │ Async Job Queue          │
├────────────────────┼─────────────────────┼──────────────────────────┤
│ Approver           │ Manager             │ CFO                      │
│ Channel            │ Slack (instant)     │ Email (delayed)          │
│ Timeout            │ 30 seconds          │ 10 seconds (→ async)     │
│ Response Time      │ 2-5 seconds         │ < 1 second (202 Accepted)│
│ Connection         │ Stays open          │ Closes immediately       │
│ State Persistence  │ In-memory           │ Database (MongoDB)       │
│ Survives Restart   │ ❌ No               │ ✅ Yes                   │
│ Auto-Resume        │ Not needed          │ ✅ Yes                   │
│ Scalability        │ ⚠️  Limited         │ ✅ Horizontal            │
│ Best For           │ Interactive UX      │ Business workflows       │
└────────────────────┴─────────────────────┴──────────────────────────┘

KEY INSIGHTS:

✅ Pattern Selection is AUTOMATIC based on timeout:
   • Approval completes within timeout → Sync pattern (immediate response)
   • Approval exceeds timeout → Async pattern (202 + resume later)

✅ State Capture ensures ZERO data loss:
   • Every step captured in database
   • Execution resumes from exact checkpoint
   • Complete audit trail for compliance

✅ Production Ready:
   • Horizontal scaling (multiple workers)
   • High availability (persistent state)
   • Fault tolerant (survives restarts)
"""
    print(comparison)


async def main():
    """Run complete demonstration."""

    print("\n\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + " " * 10 + "FINANCIAL APPROVAL SYSTEM - DEMO" + " " * 26 + "║")
    print("║" + " " * 15 + "Real-World Governance Example" + " " * 24 + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")

    # Demo both patterns
    await demo_small_transaction()
    await demo_large_transaction()

    # Show audit trail
    await show_audit_trail()

    # Show comparison
    await show_pattern_comparison()

    # Summary
    print("\n" + "=" * 70)
    print("✅ DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\n🎯 Key Takeaways:")
    print("   1. Small transactions (<$10k): Fast sync approval via Slack")
    print("   2. Large transactions (≥$10k): Async approval via email")
    print("   3. State persistence: Survives restarts, zero data loss")
    print("   4. Auto-resume: Picks up where it left off after approval")
    print("   5. Complete audit trail: Every action logged for compliance")
    print("\n💡 Production Usage:")
    print("   • Replace InMemoryStorage with MongoDBStorage")
    print("   • Deploy background workers with auto-resume")
    print("   • Integrate with real Slack/Email systems")
    print("   • Add webhook endpoints for approval links")
    print("   • Scale horizontally with multiple workers")
    print("\n📖 See DEPLOYMENT.md for production setup guide")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
