# Agent-Govern Architecture

Visual guide to understanding the approval system architecture.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT APPLICATION                          │
│                                                                      │
│  @govern(policies=[...])                                            │
│  async def wire_transfer(amount, recipient):                        │
│      # Your business logic                                          │
└────────────────┬────────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      GOVERNANCE ENGINE                               │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Pre-Actions  │→ │   Policies   │→ │ Post-Actions │              │
│  └──────────────┘  └──────┬───────┘  └──────────────┘              │
│                           │                                          │
│                           ▼                                          │
│                  ┌─────────────────┐                                │
│                  │ Approval Policy │                                │
│                  └────────┬────────┘                                │
└───────────────────────────┼─────────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
    SYNC PATTERN                  ASYNC PATTERN
  (Fast approval)               (Slow approval)
              │                           │
              │                           │
┌─────────────▼──────────┐   ┌────────────▼──────────────┐
│   APPROVAL HANDLER     │   │   APPROVAL HANDLER        │
│                        │   │                           │
│  • Slack notification  │   │  • Email with link        │
│  • Wait 2 seconds      │   │  • Save state to DB       │
│  • Manager approves    │   │  • Return 202 Accepted    │
│  • Return approved     │   │  • Close connection       │
└─────────────┬──────────┘   └────────────┬──────────────┘
              │                           │
              ▼                           │
┌─────────────────────────┐              │
│   EXECUTE FUNCTION      │              │
│                         │              │
│  • Process payment      │              │
│  • Return 200 OK        │              │
└─────────────────────────┘              │
                                         │
                         ┌───────────────▼────────────────┐
                         │      BACKGROUND WORKER          │
                         │                                 │
                         │  ┌───────────────────────────┐  │
                         │  │  AUTO-RESUME MANAGER      │  │
                         │  │                           │  │
                         │  │  • Listen for approval    │  │
                         │  │  • Load saved state       │  │
                         │  │  • Resume execution       │  │
                         │  └───────────────────────────┘  │
                         └─────────────────────────────────┘
```

---

## Pattern 1: Sync Wait (Fast Approval)

**Timeline**: Connection stays open for 2-5 seconds

```
Client                 API Server              Slack              Manager
  │                        │                     │                  │
  │─── POST /transfer ────>│                     │                  │
  │                        │                     │                  │
  │                        │── Send notification ─────────────────>│
  │                        │                     │                  │
  │    [Connection Open]   │                     │                  │
  │         ⏳             │    [Waiting...]     │    [Sees msg]   │
  │                        │                     │                  │
  │                        │<──── Clicks Approve ──────────────────│
  │                        │                     │                  │
  │                        │─── Execute ────>    │                  │
  │                        │                     │                  │
  │<── 200 OK + Result ────│                     │                  │
  │                        │                     │                  │

Duration: 2-5 seconds
Response: HTTP 200 OK with transaction result
```

**Code Flow**:
```python
# 1. Client makes request
result = await quick_wire_transfer(amount=5000, ...)

# 2. Governance engine evaluates policies
# 3. Approval required → Send Slack notification
# 4. WAIT for manager to click approve (2 seconds)
# 5. Manager approves → Continue execution
# 6. Execute business logic
# 7. Return result to client

# Total: ~2-5 seconds
```

---

## Pattern 2: Async Job Queue (Slow Approval)

**Timeline**: Connection closes in < 1 second, resume happens hours later

```
Client          API Server          Email          CFO          Background Worker
  │                 │                 │             │                  │
  │─ POST /transfer>│                 │             │                  │
  │                 │                 │             │                  │
  │                 │─ Send email ────────────────>│                  │
  │                 │                 │             │                  │
  │                 │─ Save state ──> [MongoDB]    │                  │
  │                 │                 │             │                  │
  │<─ 202 Accepted ─│                 │             │                  │
  │                 │                 │             │                  │
  [Connection       │                 │             │                  │
   closed]          │                 │             │                  │
                    │                 │             │                  │
              [3 hours pass...]       │             │                  │
                    │                 │             │                  │
                    │                 │    [Opens email]               │
                    │                 │             │                  │
                    │<─ Clicks Approve ─────────────│                  │
                    │                 │             │                  │
                    │─ Record approval ────────────────────────────────>│
                    │                 │             │                  │
                    │                 │             │   [Load state]   │
                    │                 │             │   [Resume exec]  │
                    │                 │             │   [Complete]     │
                    │                 │             │                  │
  [Client polls]    │                 │             │                  │
  │                 │                 │             │                  │
  │─ GET /status ──>│                 │             │                  │
  │<─ 200 Result ───│                 │             │                  │
  │                 │                 │             │                  │

Initial Response: < 1 second (202 Accepted)
Approval Time: 3 hours (CFO clicks link)
Execution: Background worker auto-resumes
```

**Code Flow**:
```python
# 1. Client makes request
try:
    result = await large_wire_transfer(amount=50000, ...)
except TimeoutError:
    # Expected - approval takes too long
    pass

# 2. Governance engine evaluates policies
# 3. Approval required → Send email
# 4. State captured to MongoDB:
#    - Function name
#    - Arguments
#    - Local variables
#    - Checkpoint location
# 5. Return 202 Accepted to client (< 1 second)
# 6. Connection closes

# [3 hours later...]

# 7. CFO clicks approval link in email
# 8. Webhook records approval decision
# 9. Event emitted: ApprovalGrantedEvent
# 10. Auto-resume manager detects event
# 11. Load saved state from MongoDB
# 12. Resume execution from checkpoint
# 13. Complete business logic
# 14. Store result in MongoDB
```

---

## State Persistence Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        EXECUTION FLOW                            │
└─────────────────────────────────────────────────────────────────┘

Step 1: Function Called
┌──────────────────────────────┐
│  @govern(capture_state=True) │
│  async def transfer(amount): │
│      # Business logic        │
└──────────────┬───────────────┘
               │
               ▼
Step 2: State Captured
┌──────────────────────────────┐
│   STATE SNAPSHOT             │
│   ─────────────────          │
│   execution_id: exec-123     │
│   function_name: transfer    │
│   function_args: {amount:..} │
│   local_vars: {...}          │
│   checkpoint: "pre_approval" │
│   serialized_state: <bytes>  │
└──────────────┬───────────────┘
               │
               ▼
Step 3: Stored in Database
┌──────────────────────────────┐
│      MONGODB                 │
│   ┌────────────────────┐     │
│   │ Executions         │     │
│   ├────────────────────┤     │
│   │ exec-123           │     │
│   │ status: pending    │     │
│   │ function: transfer │     │
│   └────────────────────┘     │
│                              │
│   ┌────────────────────┐     │
│   │ Snapshots          │     │
│   ├────────────────────┤     │
│   │ snap-456           │     │
│   │ exec_id: exec-123  │     │
│   │ state: <bytes>     │     │
│   └────────────────────┘     │
└──────────────────────────────┘

[Server can now restart - state is safe!]

Step 4: Approval Granted
┌──────────────────────────────┐
│   APPROVAL EVENT             │
│   ─────────────────          │
│   execution_id: exec-123     │
│   approved: true             │
│   approver: cfo@company.com  │
│   timestamp: 2025-10-18...   │
└──────────────┬───────────────┘
               │
               ▼
Step 5: Auto-Resume
┌──────────────────────────────┐
│   AUTO-RESUME MANAGER        │
│   ─────────────────          │
│   1. Detect approval event   │
│   2. Load snapshot           │
│   3. Restore state           │
│   4. Resume execution        │
└──────────────┬───────────────┘
               │
               ▼
Step 6: Execution Continues
┌──────────────────────────────┐
│   BUSINESS LOGIC             │
│   ─────────────────          │
│   # Continue from checkpoint │
│   process_payment(...)       │
│   record_transaction(...)    │
│   return result              │
└──────────────┬───────────────┘
               │
               ▼
Step 7: Result Stored
┌──────────────────────────────┐
│      MONGODB                 │
│   ┌────────────────────┐     │
│   │ Executions         │     │
│   ├────────────────────┤     │
│   │ exec-123           │     │
│   │ status: completed  │     │
│   │ outputs: {...}     │     │
│   └────────────────────┘     │
└──────────────────────────────┘
```

---

## Multi-Tier Approval Example

```
Transaction Amount → Approval Flow

$0 - $1,000
    └─> Auto-approved (no human required)
        └─> Executes immediately

$1,000 - $10,000
    └─> Manager approval (Slack)
        └─> Sync pattern (2-5 seconds)
            └─> Connection stays open
                └─> 200 OK with result

$10,000 - $100,000
    └─> CFO approval (Email)
        └─> Async pattern (hours)
            └─> 202 Accepted immediately
                └─> Background worker resumes

$100,000+
    └─> Multi-signature approval (Email)
        ├─> CFO approval required
        ├─> CEO approval required
        └─> Board approval required
            └─> Async pattern (days)
                └─> 202 Accepted immediately
                    └─> Background worker resumes
```

**Code Implementation**:

```python
# Tier 1: Auto-approve small amounts
@govern(
    policies=[
        ValidationPolicy(
            validator=lambda inputs: inputs["amount"] <= 1000
        )
    ]
)
async def auto_transfer(amount, recipient):
    # No approval needed - executes immediately
    pass

# Tier 2: Manager approval (Sync)
@govern(
    policies=[
        ValidationPolicy(
            validator=lambda inputs: 1000 < inputs["amount"] <= 10000
        ),
        ApprovalPolicy(
            approvers=["manager@company.com"],
            timeout_seconds=30  # Sync pattern
        )
    ]
)
async def manager_transfer(amount, recipient):
    # Manager approves via Slack - connection stays open
    pass

# Tier 3: CFO approval (Async)
@govern(
    policies=[
        ValidationPolicy(
            validator=lambda inputs: 10000 < inputs["amount"] <= 100000
        ),
        ApprovalPolicy(
            approvers=["cfo@company.com"],
            timeout_seconds=10  # Async pattern
        )
    ],
    capture_state=True  # Required for async
)
async def cfo_transfer(amount, recipient):
    # CFO approves via email - returns 202 immediately
    pass

# Tier 4: Multi-signature (Async)
@govern(
    policies=[
        ValidationPolicy(
            validator=lambda inputs: inputs["amount"] > 100000
        ),
        ApprovalPolicy(
            approvers=["cfo@company.com", "ceo@company.com", "board@company.com"],
            timeout_seconds=10,
            approval_threshold=3  # All must approve
        )
    ],
    capture_state=True
)
async def multisig_transfer(amount, recipient):
    # Multiple approvals required - returns 202 immediately
    pass
```

---

## Scaling Architecture

### Single Server (Development)

```
┌─────────────────────────────────────┐
│         SERVER                      │
│  ┌──────────────┐                   │
│  │  API Process │                   │
│  └──────┬───────┘                   │
│         │                           │
│  ┌──────▼────────┐                  │
│  │ Background    │                  │
│  │ Worker Thread │                  │
│  └───────────────┘                  │
│                                     │
│  ┌───────────────┐                  │
│  │  InMemory     │                  │
│  │  Storage      │                  │
│  └───────────────┘                  │
└─────────────────────────────────────┘
```

### Production (Horizontal Scaling)

```
                Load Balancer
                      │
          ┌───────────┼───────────┐
          │           │           │
          ▼           ▼           ▼
    ┌─────────┐ ┌─────────┐ ┌─────────┐
    │ API     │ │ API     │ │ API     │
    │ Server1 │ │ Server2 │ │ Server3 │
    └────┬────┘ └────┬────┘ └────┬────┘
         │           │           │
         └───────────┼───────────┘
                     │
                     ▼
            ┌────────────────┐
            │    MongoDB     │
            │  Replica Set   │
            └────────┬───────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
         ▼           ▼           ▼
    ┌─────────┐ ┌─────────┐ ┌─────────┐
    │Worker 1 │ │Worker 2 │ │Worker 3 │
    │(Resume) │ │(Resume) │ │(Resume) │
    └─────────┘ └─────────┘ └─────────┘
```

**Key Points**:
- API servers are stateless
- Workers can run on separate machines
- MongoDB provides shared state
- Horizontal scaling for both API and workers
- Any worker can resume any execution

---

## Event Flow

```
Execution Lifecycle Events:

1. execution.started
   └─> Function call initiated

2. policy.validation.passed
   └─> Input validation successful

3. policy.approval.requested
   └─> Approval notification sent

4. execution.state.captured
   └─> State snapshot saved to database

5. policy.approval.granted
   └─> Approver granted approval

6. execution.resumed
   └─> Background worker resumed execution

7. execution.completed
   └─> Function completed successfully

8. audit.logged
   └─> Audit trail recorded
```

**Event Subscribers**:
```python
# Log all events
emitter.on(EventType.ALL, lambda e: logger.info(f"Event: {e.event_type}"))

# Alert on approval requests
emitter.on(EventType.APPROVAL_REQUESTED, send_slack_alert)

# Metrics
emitter.on(EventType.EXECUTION_COMPLETED, record_metric)

# Auto-resume (built-in)
emitter.on(EventType.APPROVAL_GRANTED, auto_resume.handle_approval)
```

---

## Database Schema

### Executions Collection

```json
{
  "execution_id": "exec-123",
  "function_name": "large_wire_transfer",
  "status": "completed",
  "started_at": "2025-10-18T14:23:45Z",
  "completed_at": "2025-10-18T17:26:52Z",
  "inputs": {
    "amount": 50000,
    "recipient": "BigCorp Industries",
    "account_number": "987-654-3210"
  },
  "outputs": {
    "transaction_id": "TXN-0002",
    "status": "completed"
  },
  "current_checkpoint": "post_approval",
  "approval_required": true
}
```

### Snapshots Collection

```json
{
  "snapshot_id": "snap-456",
  "execution_id": "exec-123",
  "checkpoint": "pre_approval",
  "captured_at": "2025-10-18T14:23:46Z",
  "function_args": {
    "args": [],
    "kwargs": {
      "amount": 50000,
      "recipient": "BigCorp Industries"
    }
  },
  "local_vars": {},
  "serialized_state": "<binary data>"
}
```

### Events Collection

```json
{
  "event_id": "evt-789",
  "execution_id": "exec-123",
  "event_type": "approval.granted",
  "timestamp": "2025-10-18T17:26:50Z",
  "metadata": {
    "approver": "cfo@company.com",
    "reason": "Approved - legitimate business expense"
  }
}
```

---

## Summary

### Sync Pattern (Fast)
✅ Connection stays open
✅ Immediate response
✅ Simple implementation
❌ Doesn't scale
❌ Lost on restart

### Async Pattern (Production)
✅ Connection closes immediately
✅ Survives restarts
✅ Scales horizontally
✅ Production-ready
⚠️  More complex (handled by library)

**The library handles both patterns automatically based on timeout!**

---

For complete code examples, see:
- `examples/financial_approval_system.py` - Full implementation
- `examples/approval_patterns.py` - Pattern comparison
- `DEPLOYMENT.md` - Production deployment guide
