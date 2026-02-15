# Agent-Govern Examples

This directory contains comprehensive examples demonstrating the **governor** library's capabilities.

## Quick Start

```bash
# Install dependencies
pip install governor[mongodb]

# Run basic example
python basic_usage.py

# Run approval patterns comparison
python approval_patterns.py

# Run financial approval system (recommended)
python financial_approval_system.py
```

---

## Featured Example: Financial Approval System

**File**: `financial_approval_system.py`

This is the **most comprehensive example** showing real-world governance with:
- ✅ Multi-tier approval policies based on transaction amounts
- ✅ Sync approvals for small amounts (< $10,000)
- ✅ Async approvals for large amounts (≥ $10,000)
- ✅ State persistence and auto-resume
- ✅ Complete audit logging
- ✅ Production-ready patterns

### What It Demonstrates

#### Scenario 1: Small Transaction ($5,000)

**Pattern**: Sync Wait (connection stays open)

```python
@govern(
    policies=[
        ValidationPolicy(...),
        ApprovalPolicy(
            approvers=["manager@company.com"],
            timeout_seconds=30  # Short timeout
        ),
        AuditPolicy(...)
    ]
)
async def quick_wire_transfer(amount, recipient, account_number):
    # Process payment...
```

**Flow**:
1. Client requests $5,000 transfer
2. Slack notification sent to manager
3. Manager clicks "Approve" (2 seconds)
4. Transfer executes immediately
5. Client receives 200 OK with transaction details
6. **Total time**: 2-5 seconds

**Output**:
```
████████████████████████████████████████████████████████████████████
█                                                                  █
█               SCENARIO 1: SMALL TRANSACTION                     █
█                    (Sync Approval Pattern)                      █
█                                                                  █
████████████████████████████████████████████████████████████████████

📋 Client Request:
   POST /api/wire-transfer
   {
     "amount": 5000,
     "recipient": "Acme Corp",
     "account": "123-456-7890"
   }

======================================================================
📱 SLACK NOTIFICATION
======================================================================
   Channel: #finance-approvals
   To: manager@company.com

   🔔 Wire Transfer Approval Required
   Amount: $5,000.00
   Recipient: Acme Corp

   [✓ Approve]  [✗ Reject]
======================================================================

   ⏳ Waiting for manager response...
   ✅ APPROVED by manager@company.com
   Reason: Transaction within manager approval limits

   💸 Processing wire transfer...
   ✓ Transfer completed: TXN-0001

📤 Client Response (after 2.5s):
   HTTP 200 OK
   {
     "transaction_id": "TXN-0001",
     "status": "completed",
     "amount": 5000,
     "recipient": "Acme Corp"
   }

   ⏱️  Total time: 2.5s (connection stayed open)
```

---

#### Scenario 2: Large Transaction ($50,000)

**Pattern**: Async Job Queue (returns immediately)

```python
@govern(
    policies=[
        ValidationPolicy(...),
        ApprovalPolicy(
            approvers=["cfo@company.com"],
            timeout_seconds=10  # Short timeout → triggers async
        ),
        AuditPolicy(...)
    ],
    capture_state=True  # CRITICAL for resume
)
async def large_wire_transfer(amount, recipient, account_number):
    # Process payment...
```

**Flow**:
1. Client requests $50,000 transfer
2. Email sent to CFO with approval link
3. State saved to database
4. Client receives **202 Accepted** immediately (< 1 second)
5. Connection closes
6. [3 hours later] CFO clicks "Approve" in email
7. Background worker auto-resumes execution
8. Transfer completes

**Output**:
```
████████████████████████████████████████████████████████████████████
█                                                                  █
█               SCENARIO 2: LARGE TRANSACTION                     █
█                   (Async Approval Pattern)                      █
█                                                                  █
████████████████████████████████████████████████████████████████████

📋 Client Request:
   POST /api/wire-transfer
   {
     "amount": 50000,
     "recipient": "BigCorp Industries",
     "account": "987-654-3210"
   }

🔧 Starting background services...
   ✓ Job queue started
   ✓ Auto-resume manager started

======================================================================
📧 EMAIL SENT
======================================================================
   To: cfo@company.com
   Subject: URGENT - Wire Transfer Approval Required

   Dear CFO,

   A large wire transfer requires your approval:

   Amount:     $50,000.00
   Recipient:  BigCorp Industries
   Requested:  2025-10-18 14:23:45

   Approve: https://approvals.company.com/approve/exec-123
   Reject:  https://approvals.company.com/reject/exec-123

   This request will expire in 24 hours.
======================================================================

   ⏸️  EXECUTION PAUSED - State saved to database
   🔁 Returning 202 Accepted to client...
   💤 Server can now restart - state is persistent

📤 Client Response (after 0.8s):
   HTTP 202 Accepted
   {
     "status": "awaiting_approval",
     "execution_id": "exec-123",
     "message": "Transfer pending CFO approval",
     "poll_url": "/api/executions/exec-123"
   }

   ⚡ Response time: 0.8s (connection closed immediately)
   💾 State saved to database

⏳ Waiting for CFO approval and auto-resume...

======================================================================
🔔 [3 HOURS LATER] CFO clicked approval link
======================================================================
   ✅ Approval recorded in database
   🔄 Auto-resume manager will pick this up...

▶️  Auto-resuming large_wire_transfer (execution: exec-123)
   Submitted as background job: job-456

   💰 Processing large wire transfer...
   ✓ Transfer completed: TXN-0002

📊 Checking execution status...

   Execution ID: exec-123
   Status: completed
   Started: 14:23:45
   Completed: 14:26:52
   Result: Transaction(TXN-0002, $50,000.00 to BigCorp Industries, completed)
```

---

#### Audit Trail

```
████████████████████████████████████████████████████████████████████
█                                                                  █
█                         AUDIT TRAIL                             █
█                                                                  █
████████████████████████████████████████████████████████████████████

📚 Transaction Ledger (2 transactions):
   ------------------------------------------------------------------
   TXN-0001 |   $5,000.00 | Acme Corp            | completed
   TXN-0002 |  $50,000.00 | BigCorp Industries   | completed
   ------------------------------------------------------------------

📋 Governance Log (2 executions):
   ------------------------------------------------------------------
   ✓ exec-001 | quick_wire_transfer       | completed
   ✓ exec-123 | large_wire_transfer       | completed
   ------------------------------------------------------------------

📝 Event Log (18 events):
   ------------------------------------------------------------------
   14:23:42 | execution.started           | exec-001
   14:23:42 | policy.validation.passed    | exec-001
   14:23:42 | policy.approval.requested   | exec-001
   14:23:44 | policy.approval.granted     | exec-001
   14:23:45 | execution.completed         | exec-001
   14:23:45 | execution.started           | exec-123
   14:23:45 | policy.validation.passed    | exec-123
   14:23:45 | policy.approval.requested   | exec-123
   14:23:46 | execution.state.captured    | exec-123
   14:26:50 | policy.approval.granted     | exec-123
   ... and 8 more events
   ------------------------------------------------------------------
```

---

#### Pattern Comparison

```
████████████████████████████████████████████████████████████████████
█                                                                  █
█                    PATTERN COMPARISON                           █
█                                                                  █
████████████████████████████████████████████████████████████████████

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
```

---

## Example Files

### 1. `basic_usage.py`
Introduction to the `@govern` decorator with simple examples:
- Pre/post actions
- Policy evaluation
- State capture
- Event emission

**Run**: `python basic_usage.py`

### 2. `criteria_based_governance.py`
Advanced policy examples (9 patterns):
- Threshold-based policies
- Environment-based policies
- Risk-based policies
- Time-based policies
- Multi-criteria policies
- Dynamic policies
- Additive criteria patterns

**Run**: `python criteria_based_governance.py`

### 3. `approval_patterns.py`
Side-by-side comparison of approval patterns:
- Pattern 1: Sync Wait (connection open)
- Pattern 2: Async Job Queue (immediate return)
- When to use each pattern

**Run**: `python approval_patterns.py`

### 4. `financial_approval_system.py` ⭐ **RECOMMENDED**
Complete real-world example with:
- Multi-tier approval workflows
- Both sync and async patterns
- State persistence and resume
- Audit trail and compliance
- Production-ready patterns

**Run**: `python financial_approval_system.py`

### 5. `fastapi_integration.py`
Integration with FastAPI web framework:
- REST API endpoints with governance
- Webhook-based approvals
- Job status polling
- Error handling

**Run**: `uvicorn examples.fastapi_integration:app --reload`

---

## Production Usage

### Step 1: Install with Production Dependencies

```bash
pip install governor[mongodb]
```

### Step 2: Configure Storage

```python
from governor.storage.mongodb import MongoDBStorage

storage = MongoDBStorage(
    uri="mongodb://localhost:27017",
    database="governor_prod"
)
await storage.initialize()
```

### Step 3: Setup Background Worker

```python
# worker.py
from governor.background import BackgroundJobQueue, AutoResumeManager

job_queue = BackgroundJobQueue()
await job_queue.start()

auto_resume = AutoResumeManager(storage=storage, job_queue=job_queue)
auto_resume.register_function("my_function", my_governed_function)
await auto_resume.start()
```

### Step 4: Deploy

See **[DEPLOYMENT.md](../DEPLOYMENT.md)** for complete production deployment guide including:
- MongoDB setup with replica sets
- Celery/RQ integration
- Kubernetes deployment
- Monitoring and observability
- Security best practices

---

## Key Concepts

### Approval Patterns

#### Sync Wait Pattern
- **Use when**: Timeout < 5 minutes
- **Connection**: Stays open
- **Response**: Immediate when approved
- **Best for**: Slack buttons, CLI prompts, web forms

#### Async Job Queue Pattern
- **Use when**: Timeout > 5 minutes (hours/days)
- **Connection**: Closes immediately
- **Response**: 202 Accepted, poll for result
- **Best for**: Email approvals, business workflows

### State Persistence

```python
@govern(
    policies=[...],
    capture_state=True  # REQUIRED for async pattern
)
async def my_function(data):
    # Function state is automatically captured
    # Can resume from any point after approval
    pass
```

### Auto-Resume

```python
# Register function for automatic resume
auto_resume.register_function("my_function", my_governed_function)

# When approval is granted:
# 1. Event emitted: ApprovalGrantedEvent
# 2. Auto-resume manager detects event
# 3. Execution state restored from snapshot
# 4. Function resumes from checkpoint
# 5. Result stored in database
```

---

## Next Steps

1. **Start Simple**: Run `basic_usage.py` to understand core concepts
2. **Learn Patterns**: Run `approval_patterns.py` to see sync vs async
3. **See Real Example**: Run `financial_approval_system.py` for complete workflow
4. **Go to Production**: Read `DEPLOYMENT.md` for production setup

---

## Support

- **Documentation**: See main [README.md](../README.md)
- **Deployment Guide**: See [DEPLOYMENT.md](../DEPLOYMENT.md)
- **Issues**: Open an issue on GitHub
- **Examples**: All examples in this directory are self-contained and runnable

---

## Example Output Summary

When you run `financial_approval_system.py`, you'll see:

✅ **Scenario 1**: $5,000 transfer approved in 2 seconds via Slack (sync pattern)
✅ **Scenario 2**: $50,000 transfer pending CFO email approval (async pattern)
✅ **Auto-Resume**: Background worker picks up approved execution
✅ **Audit Trail**: Complete log of all transactions, executions, and events
✅ **Pattern Comparison**: Side-by-side analysis of both approaches

**Total runtime**: ~15 seconds (simulates hours with sleep delays)

Enjoy building governed agentic systems! 🚀
