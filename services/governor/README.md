# governor

**Built by [Lyzr](https://www.lyzr.ai)**

**A clean, minimal, and powerful governance library for agentic systems.**

governor provides comprehensive governance for autonomous agents and AI systems with state management, policy enforcement, human-in-the-loop approval, and event tracking.

🟢 **Simple for beginners**: Add `@govern()` - that's it! Works out of the box.
🔵 **Powerful for experts**: Full customization, production-grade scaling, enterprise features.

**Progressive complexity** - Start with 1 line, grow to full production infrastructure.

## Visualize on Lyzr Studio

See your approval flows in action on [Lyzr Studio](https://www.lyzr.ai):

![Governance Flow Visualization](governance.png)

*Example: Multi-stage approval pipeline with AI Safety → Security → Executive stages visualized in Lyzr Studio*

## Features

- **Simple `@govern` Decorator**: Apply to any async function, class, or FastAPI endpoint
- **Execution Lifecycle Management**: Pre-actions, execution, post-actions, and evaluation
- **State Management**: Automatic state capture, versioning, and replay for debugging/recovery
- **Policy System**: Validation, authorization, rate limiting, audit, and approval policies
- **Human-in-the-Loop Approvals**:
  - **Sync pattern**: Fast approvals (seconds) - connection stays open
  - **Async pattern**: Slow approvals (hours/days) - state persisted, auto-resume
  - CLI, webhook, email, Slack integrations
- **Background Processing**: Job queue with auto-resume for long-running operations
- **Event System**: Async event emission for monitoring and observability
- **Storage Backends**: In-memory and MongoDB (pluggable architecture)
- **Replay Engine**: Continue from any checkpoint, debug past executions
- **FastAPI Integration**: Built-in middleware and approval endpoints
- **Web Dashboard**: Visual approval flow management with React-powered UI
- **Full Async Support**: Native async/await throughout
- **Production Ready**: Horizontal scaling, state persistence, fault tolerance

## Installation

```bash
# Basic installation
pip install governor

# With MongoDB support
pip install governor[mongodb]

# With FastAPI integration
pip install governor[fastapi]

# With Web Dashboard
pip install governor[dashboard]

# Everything
pip install governor[all]
```

## Quick Start

### Basic Usage

```python
from governor import govern, AuditPolicy

@govern(policies=[AuditPolicy()])
async def process_data(data: dict) -> dict:
    """Process data with automatic audit logging."""
    return {"processed": True, "data": data}

# Use it
result = await process_data({"key": "value"})
```

### Real-World Example: Financial Approval System

See a **complete production-ready example** with multi-tier approvals, sync/async patterns, and state persistence:

```python
from governor import govern, ApprovalPolicy, ValidationPolicy
from governor.background import BackgroundJobQueue, AutoResumeManager

# Small transactions: Fast sync approval via Slack (< 5 seconds)
@govern(
    policies=[
        ValidationPolicy(validator=lambda i: i["amount"] < 10000),
        ApprovalPolicy(approvers=["manager@company.com"], timeout_seconds=30)
    ]
)
async def quick_wire_transfer(amount: float, recipient: str):
    return {"status": "completed", "amount": amount}

# Large transactions: Async approval via email (hours/days)
@govern(
    policies=[
        ValidationPolicy(validator=lambda i: i["amount"] >= 10000),
        ApprovalPolicy(approvers=["cfo@company.com"], timeout_seconds=10)
    ],
    capture_state=True  # State survives server restarts!
)
async def large_wire_transfer(amount: float, recipient: str):
    return {"status": "completed", "amount": amount}

# Setup background worker for auto-resume
job_queue = BackgroundJobQueue()
auto_resume = AutoResumeManager(storage=storage, job_queue=job_queue)
auto_resume.register_function("large_wire_transfer", large_wire_transfer)
await auto_resume.start()

# Small transaction: Completes in ~2 seconds (sync pattern)
result = await quick_wire_transfer(amount=5000, recipient="Acme Corp")
# → Manager approves via Slack → Returns immediately

# Large transaction: Returns 202 Accepted in < 1 second (async pattern)
try:
    result = await large_wire_transfer(amount=50000, recipient="BigCorp")
except TimeoutError:
    # Expected - returns 202 Accepted, state saved
    # CFO will approve via email hours later
    # Background worker will auto-resume execution
    pass
```

**What happens with large transactions:**
1. Client requests $50,000 transfer
2. Email sent to CFO with approval link
3. State saved to MongoDB
4. Client receives **202 Accepted** (< 1 second)
5. Connection closes
6. [3 hours later] CFO clicks "Approve" in email
7. Background worker **auto-resumes** from saved state
8. Transfer completes automatically

**See the complete example**: `examples/financial_approval_system.py`

**Architecture guide**: `examples/ARCHITECTURE.md`

**Production deployment**: `DEPLOYMENT.md`

### Get Execution ID with Callback

Get the `execution_id` (ticket ID) immediately when state is saved to the database - perfect for returning to clients in async pattern:

```python
from governor import govern, ApprovalPolicy

def handle_state_saved(execution_id: str, state: dict):
    """Called when state is saved - get execution_id immediately!"""
    if state.get("timeout"):
        # Timeout occurred - return 202 Accepted to client
        print(f"Return to client: execution_id={execution_id}")

@govern(
    policies=[ApprovalPolicy(approvers=["cfo"], timeout_seconds=10)],
    capture_state=True,
    on_state_saved=handle_state_saved  # ← Get callback with execution_id
)
async def large_transfer(amount, recipient):
    return {"status": "completed"}

# In FastAPI endpoint:
try:
    result = await large_transfer(50000, "BigCorp")
    return {"status": "completed", "result": result}  # 200 OK
except PermissionError:
    # execution_id captured in callback - return 202 Accepted
    return JSONResponse(202, {
        "execution_id": execution_id,  # From callback
        "status": "pending_approval",
        "poll_url": f"/api/status/{execution_id}"
    })
```

**Use cases**:
- Return execution_id to client for tracking (202 Accepted)
- Store in your own database
- Send to monitoring systems (DataDog, Prometheus)
- Generate support tickets (Jira, ServiceNow)
- Trigger external workflows

**See**: `examples/state_callback_example.py` for 6 complete examples
**Guide**: `ON_STATE_SAVED_CALLBACK.md`

### Manual Resume Control (Developer-Triggered)

Want full control over when to resume? Trigger resume manually via webhooks or custom logic:

```python
from governor.background import AutoResumeManager

# Setup (without auto-start for manual control)
auto_resume = AutoResumeManager(storage, job_queue)
auto_resume.register_function("my_function", my_governed_function)
# NOT calling auto_resume.start() - manual control only!

# Webhook endpoint - developer triggers resume
@app.post("/webhook/approve/{execution_id}")
async def manual_approve(execution_id: str, approver: str):
    # Add your custom business logic here!
    # - Check risk scores
    # - Validate with external APIs
    # - Apply business rules
    # - Time constraints

    # MANUALLY RESUME when ready
    result = await auto_resume.resume_by_execution_id(
        execution_id=execution_id,
        func=my_governed_function
    )

    return {"status": "resumed", "result": result}
```

**Use cases**:
- Jira/ServiceNow ticket approval → webhook triggers resume
- Slack button click → webhook triggers resume
- Admin dashboard → manual approve button
- Cron job → scheduled resume at specific time
- Conditional resume based on external API checks
- Custom business rules before resume

**Approaches**:
- **Auto-resume**: Framework automatically resumes (set and forget)
- **Manual resume**: Developer triggers via webhook (full control)
- **Hybrid**: Auto for most cases, manual override for special scenarios

**See**: `examples/manual_resume_example.py` for complete working example
**Guide**: `MANUAL_RESUME_GUIDE.md` | `AUTO_VS_MANUAL_RESUME.md`

### Using Policy Configuration Files

```python
from governor import govern, load_policies_from_file

# Load policies from YAML or JSON
policies = load_policies_from_file("governance.yaml")

@govern(policies=policies)
async def process_data(data: dict) -> dict:
    return {"processed": True}
```

**governance.yaml:**
```yaml
policies:
  - type: validation
    name: InputValidation
    enabled: true
    strict: true

  - type: authorization
    required_roles: [admin, finance]

  - type: rate_limit
    max_calls: 100
    window_seconds: 60

  - type: audit
    compliance_tags: [GDPR, SOC2]
    sensitive_fields: [password, ssn]
```

### With Validation

```python
from governor import govern, ValidationPolicy
from pydantic import BaseModel

class UserInput(BaseModel):
    name: str
    age: int

@govern(policies=[ValidationPolicy(input_schema=UserInput)])
async def create_user(name: str, age: int) -> dict:
    return {"user_id": 123, "name": name, "age": age}
```

### With Authorization

```python
from governor import govern, AuthorizationPolicy

@govern(
    policies=[AuthorizationPolicy(required_roles={"admin"})],
    context={"user": {"roles": ["admin", "user"]}}
)
async def admin_operation() -> str:
    return "Admin action completed"
```

### With Human-in-the-Loop Approval

```python
from governor import govern, ApprovalPolicy
from governor.approval.handlers import CLIApprovalHandler

handler = CLIApprovalHandler()

@govern(
    policies=[ApprovalPolicy(approvers=["admin@company.com"])],
    approval_handler=handler
)
async def critical_operation(data: dict) -> dict:
    """Requires approval before execution."""
    return {"status": "completed"}
```

### Multi-Stage Sequential Approvals

Create approval pipelines where different teams must approve in sequence:

```python
from governor import govern, ApprovalPolicy

# Stage 3: Final executive approval
@govern(policies=[ApprovalPolicy(approvers=["cto@company.com"])])
async def stage3_executive(model_name, version):
    return {"status": "deployed", "model": model_name}

# Stage 2: Security team approval → Executive
@govern(policies=[ApprovalPolicy(approvers=["security@company.com"])])
async def stage2_security(model_name, version):
    return await stage3_executive(model_name, version)

# Stage 1: AI Safety team approval → Security → Executive
@govern(policies=[ApprovalPolicy(approvers=["ai-safety@company.com"])])
async def deploy_ai_model(model_name, version):
    """AI Safety → Security → Executive approval pipeline"""
    return await stage2_security(model_name, version)

# Requires all 3 approvals in sequence
result = await deploy_ai_model("gpt-custom", "2.0")
```

Each stage can have different:
- Approvers (different teams)
- Timeouts
- Auto-approve conditions
- Audit requirements

Perfect for:
- AI model deployments (Safety → Security → Executive)
- Financial transactions (Manager → Finance → CFO)
- Data access (Team Lead → Privacy → Legal)
- Code deployments (Tech Lead → Security → DevOps)

**See**: `examples/multi_stage_approval_simple.py` for complete working examples

### Web Dashboard for Approval Flows

Visualize and manage approval flows with a built-in web dashboard:

```python
from governor import govern, ApprovalPolicy
from governor.dashboard import create_dashboard
from governor.storage.memory import InMemoryStorage

storage = InMemoryStorage()

# Create dashboard
dashboard = create_dashboard(storage=storage, host="0.0.0.0", port=8765)

# Register your approval flows for visualization
dashboard.register_flow(
    function_name="deploy_ai_model",
    description="AI Model Deployment Pipeline",
    stages=[
        {
            "name": "AI Safety Team",
            "approvers": ["ai-safety@company.com"],
            "description": "Review for bias and safety",
        },
        {
            "name": "Security Team",
            "approvers": ["security@company.com"],
            "description": "Security review",
        },
        {
            "name": "Executive Team",
            "approvers": ["cto@company.com"],
            "description": "Final authorization",
        },
    ]
)

@govern(
    policies=[ApprovalPolicy(approvers=["ai-safety@company.com"])],
    storage=storage
)
async def deploy_ai_model(model_name, version):
    return {"status": "deployed"}

# Start dashboard
await dashboard.start()
# Open http://localhost:8765 in your browser
```

**Dashboard Features:**
- 📊 Visual pipeline representation of approval stages
- 📋 Real-time list of pending approvals
- ✅ Interactive approve/reject buttons
- 🔌 WebSocket for live updates
- 📜 Approval history and audit trail
- 🎯 Filter by flow type, status, approver

**Install**: `pip install governor[dashboard]`

**See**: `examples/dashboard_example.py` for complete example

### With State Capture and Replay

```python
from governor import govern
from governor.storage.memory import InMemoryStorage
from governor.replay.engine import ReplayEngine

storage = InMemoryStorage()

@govern(capture_state=True, storage=storage)
async def multi_step_process(data: dict) -> dict:
    # Your complex workflow here
    return {"status": "success"}

# Execute
result = await multi_step_process({"input": "data"})

# Replay for debugging
replay = ReplayEngine(storage=storage)
executions = await storage.list_executions()
replay_info = await replay.replay_for_debugging(executions[0].execution_id)
```

## Core Concepts

### Execution Lifecycle

Every governed function follows this lifecycle:

1. **Pre-actions**: Run before execution (logging, setup, validation)
2. **Pre-execution policies**: Evaluate before function runs
3. **Approval** (if required): Wait for human approval
4. **Execution**: Run the main function
5. **Post-execution policies**: Evaluate after function completes
6. **Post-actions**: Run after execution (cleanup, notifications)

### Policies

Built-in policies:

- **ValidationPolicy**: Input/output validation with Pydantic or custom validators
- **AuthorizationPolicy**: RBAC, ABAC, and custom authorization
- **RateLimitPolicy**: Sliding window rate limiting and quotas
- **AuditPolicy**: Compliance logging and audit trails
- **ApprovalPolicy**: Human-in-the-loop approval with multiple handlers

```python
from governor import (
    govern,
    ValidationPolicy,
    AuthorizationPolicy,
    RateLimitPolicy,
    AuditPolicy,
    ApprovalPolicy
)

@govern(
    policies=[
        ValidationPolicy(input_validator=lambda x: x.get("amount", 0) > 0),
        AuthorizationPolicy(required_roles={"admin", "finance"}),
        RateLimitPolicy(max_calls=10, window_seconds=60),
        AuditPolicy(compliance_tags=["SOC2", "financial"]),
        ApprovalPolicy(approvers=["cfo@company.com"])
    ]
)
async def process_payment(amount: float, account: str) -> dict:
    return {"status": "success"}
```

### State Management

Capture execution state at any point for replay, debugging, or recovery:

```python
from governor import govern
from governor.replay.engine import ReplayEngine

@govern(capture_state=True)
async def agent_workflow(task: str) -> dict:
    # State is automatically captured at checkpoints
    return {"completed": True}

# Later, replay or continue from any checkpoint
replay = ReplayEngine(storage)
await replay.continue_from_checkpoint(execution_id, "pre_execution", agent_workflow)
```

### Criteria-Based Conditional Governance

Apply governance dynamically based on runtime criteria:

```python
from governor import govern, ApprovalPolicy

@govern(
    policies=[
        ApprovalPolicy(
            approvers=["cfo@company.com"],
            # Auto-approve transactions under $1000
            auto_approve_condition=lambda inputs: inputs.get("kwargs", {}).get("amount", 0) < 1000
        )
    ]
)
async def process_payment(amount: float, account: str) -> dict:
    return {"status": "success", "amount": amount}

# Small amounts auto-approved, large amounts require approval
await process_payment(500, "ACC123")   # Auto-approved
await process_payment(5000, "ACC456")  # Requires approval
```

**Advanced criteria patterns (9 examples):**

*Conditional:*
- **Threshold-based**: Different governance for small/medium/large values
- **Environment-based**: Stricter policies in production vs development
- **Risk-based**: Calculate risk scores and apply governance accordingly
- **Time-based**: Different rules for business hours vs off-hours
- **Multi-criteria**: Complex decision trees combining multiple factors
- **Dynamic policies**: Select which policies to apply based on input data

*Additive (criteria + approval):*
- **Additive criteria**: Multiple conditions that ALL must pass + approval
- **Layered criteria**: Progressive filtering through multiple governance layers
- **Composite criteria**: Independent checks that all must succeed

See `examples/criteria_based_governance.py` for 9 comprehensive examples.

### Events

All governance operations emit events:

```python
from governor.events.emitter import get_default_emitter
from governor.events.base import EventType

emitter = get_default_emitter()

async def log_policy_violations(event):
    print(f"Policy violated: {event.data}")

emitter.on(EventType.POLICY_VIOLATED, log_policy_violations)
```

## FastAPI Integration

```python
from fastapi import FastAPI
from governor import govern, RateLimitPolicy
from governor.integrations.fastapi import create_approval_router, GovernMiddleware

app = FastAPI()
app.add_middleware(GovernMiddleware)
app.include_router(create_approval_router())

@app.post("/users")
@govern(policies=[RateLimitPolicy(max_calls=100, window_seconds=60)])
async def create_user(name: str, email: str) -> dict:
    return {"user_id": "123", "name": name}
```

Governance endpoints:
- `GET /govern/approvals/pending` - List pending approvals
- `POST /govern/approvals/{id}/approve` - Approve execution
- `POST /govern/approvals/{id}/reject` - Reject execution
- `GET /govern/executions` - List executions
- `GET /govern/executions/{id}` - Get execution details

## Advanced Usage

### Custom Policies

```python
from governor.policies.base import Policy, PolicyResult

class CustomPolicy(Policy):
    async def evaluate(self, execution_id, function_name, inputs, outputs=None, context=None):
        # Your custom logic
        if some_condition:
            return PolicyResult.success(
                policy_name=self.name,
                policy_type=self.get_policy_type()
            )
        return PolicyResult.failure(
            policy_name=self.name,
            policy_type=self.get_policy_type(),
            message="Custom check failed"
        )
```

### Custom Storage Backend

```python
from governor.storage.base import StorageBackend

class MyStorage(StorageBackend):
    async def store_execution(self, context):
        # Your storage logic
        pass
    # Implement other methods...
```

### Govern Entire Classes

```python
from governor import govern_class, AuditPolicy

@govern_class(policies=[AuditPolicy()], methods=["process", "execute"])
class MyAgent:
    async def process(self, data):
        return data

    async def execute(self, cmd):
        return cmd
```

## Compliance & Reporting

governor provides **comprehensive compliance and reporting** for GDPR, SOC 2, and other regulations:

### GDPR Compliance

```python
from governor import AuditPolicy
from governor.compliance.gdpr import GDPRCompliance

# GDPR-compliant data processing with sensitive field redaction
@govern(
    policies=[
        AuditPolicy(
            sensitive_fields=["email", "ssn", "credit_card"],
            compliance_tags=["GDPR", "personal_data"]
        )
    ]
)
async def process_user_data(user_id: str, data: dict):
    return {"processed": True}

# Data subject rights
gdpr = GDPRCompliance(storage)

# Right to access (Article 15)
user_data = await gdpr.right_to_access("user123")

# Right to data portability (Article 20)
portable_data = await gdpr.right_to_data_portability("user123")

# Right to erasure (Article 17)
await gdpr.right_to_erasure("user123", reason="User request")
```

### SOC 2 Compliance

```python
from governor.compliance.soc2 import SOC2Compliance

soc2 = SOC2Compliance(storage)

# Generate Trust Service Criteria reports
security_report = await soc2.security_controls_report()
availability_report = await soc2.availability_report()
processing_integrity = await soc2.processing_integrity_report()
confidentiality = await soc2.confidentiality_report()
privacy = await soc2.privacy_report()

# Comprehensive SOC 2 Type II report
full_report = await soc2.generate_comprehensive_soc2_report(period_days=90)
```

### Compliance Reporting

```python
from governor.compliance.reporter import ComplianceReporter

reporter = ComplianceReporter(storage)

# Generate compliance reports
gdpr_report = await reporter.generate_gdpr_report(period_start, period_end)
soc2_report = await reporter.generate_soc2_report(period_start, period_end)

# Export for auditors
summary = await reporter.export_report_summary(gdpr_report)
json_export = await reporter.export_report_json(gdpr_report)
```

**Features:**
- ✅ **Complete audit trails** - All governance actions logged
- ✅ **Sensitive data redaction** - Automatic PII protection
- ✅ **GDPR compliance** - Data subject rights (access, deletion, portability)
- ✅ **SOC 2 compliance** - All 5 Trust Service Criteria
- ✅ **Compliance reports** - Ready for auditors
- ✅ **Privacy notices** - Auto-generated GDPR-compliant notices
- ✅ **Consent management** - Track and manage consent
- ✅ **Data breach logging** - GDPR Article 33 compliance

## Policy Configuration Files

Externalize your governance policies in **JSON or YAML** files for better configuration management:

### Supported Formats

**YAML (recommended):**
```yaml
policies:
  - type: validation
    name: InputValidation
    strict: true

  - type: authorization
    required_roles: [admin]
    required_permissions: [write]

  - type: rate_limit
    max_calls: 100
    window_seconds: 60
    per_user: true

  - type: audit
    log_inputs: true
    log_outputs: true
    sensitive_fields: [password, ssn, email]
    compliance_tags: [GDPR, SOC2]

  - type: approval
    approvers: [cfo@company.com]
    timeout_seconds: 3600
```

**JSON:**
```json
{
  "policies": [
    {
      "type": "validation",
      "name": "InputValidation",
      "strict": true
    },
    {
      "type": "audit",
      "compliance_tags": ["GDPR", "SOC2"]
    }
  ]
}
```

### Usage

```python
from governor import govern, load_policies_from_file

# Load from file
policies = load_policies_from_file("governance.yaml")

@govern(policies=policies)
async def my_function():
    pass

# Or load from dictionary (e.g., from database)
config = {"policies": [...]}
policies = load_policies_from_dict(config)
```

### Environment-Specific Configs

```python
import os

env = os.getenv("ENV", "development")
policies = load_policies_from_file(f"policies/{env}.yaml")

@govern(policies=policies)
async def env_aware_function():
    pass
```

### Pre-built Configurations

governor includes example configs for:
- `development.yaml` - Light governance for dev
- `production.yaml` - Strict governance for prod
- `financial-services.yaml` - Compliance for finance
- `governance.yaml` - General purpose template

## Examples

See the `examples/` directory for complete examples:

- 🌟 **`financial_approval_system.py`** - **[RECOMMENDED]** Complete real-world example with:
  - Multi-tier approval workflows (manager vs CFO)
  - Sync pattern for fast approvals (< 5s via Slack)
  - Async pattern for slow approvals (hours/days via email)
  - State persistence and auto-resume
  - Complete audit trail
  - Production-ready patterns
- 🆕 **`multi_stage_approval_simple.py`** - **[NEW]** Sequential approval pipelines:
  - AI model deployment (Safety → Security → Executive)
  - Financial transactions (Manager → Finance → CFO)
  - Data access (Team Lead → Privacy → Legal)
  - Different approvers, timeouts, and auto-approve conditions per stage
- 🎨 **`dashboard_example.py`** - **[NEW]** Web dashboard for approval flows:
  - Visual flow management with web UI
  - Real-time pending approvals list
  - Interactive approve/reject from browser
  - WebSocket live updates
  - Approval history and audit trail
- `basic_usage.py` - Basic governance features
- `approval_patterns.py` - Sync vs async approval pattern comparison
- `criteria_based_governance.py` - 9 conditional governance examples
- `approval_example.py` - Human-in-the-loop approval
- `replay_example.py` - State replay and continuation
- `fastapi_example.py` - FastAPI integration
- `compliance_reporting.py` - GDPR and SOC 2 compliance reporting
- `policy_config_example.py` - Policy configuration files (JSON/YAML)

**Documentation:**
- `examples/README.md` - Detailed guide with expected output
- `examples/ARCHITECTURE.md` - Visual architecture diagrams
- `DEPLOYMENT.md` - Production deployment guide (Docker, K8s, MongoDB, Celery)

## Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=governor --cov-report=html
```

## Architecture

```
governor/
├── governor/
│   ├── decorator.py           # @govern decorator
│   ├── core/                  # Execution engine
│   │   ├── context.py         # ExecutionContext
│   │   ├── state.py           # StateSnapshot
│   │   └── executor.py        # Core executor
│   ├── policies/              # Policy system
│   │   ├── base.py            # Base policy
│   │   ├── validation.py      # Validation policy
│   │   ├── authorization.py   # Authorization policy
│   │   ├── rate_limit.py      # Rate limiting policy
│   │   ├── audit.py           # Audit policy
│   │   └── approval.py        # Approval policy
│   ├── events/                # Event system
│   │   ├── base.py            # Event types
│   │   └── emitter.py         # EventEmitter
│   ├── storage/               # Storage backends
│   │   ├── base.py            # Base interface
│   │   ├── memory.py          # In-memory storage
│   │   └── mongodb.py         # MongoDB storage
│   ├── approval/              # Human-in-the-loop
│   │   ├── manager.py         # ApprovalManager
│   │   └── handlers.py        # Approval handlers
│   ├── replay/                # Replay engine
│   │   └── engine.py          # ReplayEngine
│   └── integrations/          # Framework integrations
│       └── fastapi.py         # FastAPI integration
├── examples/                  # Usage examples
└── tests/                     # Test suite
```

## Design Principles

- **Clean Code**: Readable, maintainable, well-documented
- **Minimal API**: Simple decorator-based interface
- **Composable**: Mix and match policies and actions
- **Extensible**: Pluggable policies, storage, and approval handlers
- **Type Safe**: Full type hints throughout
- **Async First**: Native async/await support
- **Production Ready**: Battle-tested patterns and error handling

## Use Cases

- **AI Agents**: Govern autonomous agent actions with approval workflows
- **API Governance**: Rate limiting, validation, and audit for APIs
- **Workflow Orchestration**: State management for multi-step processes
- **Compliance**: Audit trails and approval chains for regulated operations
- **Debugging**: Replay and inspect past executions
- **Recovery**: Continue failed operations from last good state

## Simple for Beginners, Powerful for Experts

### For Basic Developers 🟢

**Start in 5 minutes:**
```python
from governor import govern

@govern()  # ← That's it! One line.
async def my_function(data):
    return {"result": data}
```

**What you get automatically:**
- ✅ Execution tracking
- ✅ State capture
- ✅ Event emission
- ✅ Error handling
- ✅ Audit logging

**No configuration needed!**

**Add approval (3 lines):**
```python
from governor import govern, ApprovalPolicy

@govern(policies=[ApprovalPolicy(approvers=["boss@company.com"])])
async def critical_operation(data):
    return {"result": data}
```

Now you have human-in-the-loop approval!

### For Advanced Developers 🔵

**Full customization:**
```python
from governor import govern, ApprovalPolicy
from governor.storage.mongodb import MongoDBStorage
from governor.background import BackgroundJobQueue, AutoResumeManager

# Custom storage
storage = MongoDBStorage(uri="...", replicaSet="rs0")

# Custom policy
class MyPolicy(Policy):
    async def evaluate(self, ...):
        # Your business logic
        pass

# Custom approval handler
class SlackApprovalHandler(ApprovalHandler):
    async def handle_approval_request(self, ...):
        # Send to Slack with buttons
        pass

@govern(
    policies=[MyPolicy(), ApprovalPolicy(...)],
    storage=storage,
    approval_handler=SlackApprovalHandler(),
    on_state_saved=my_callback  # Track execution_id
)
async def production_operation(data):
    return result

# Production deployment
# - Horizontal scaling (N workers)
# - High availability (replica sets)
# - Fault tolerance (auto-resume)
# - Complete observability
```

**What you get:**
- ✅ Any database (MongoDB, PostgreSQL, custom)
- ✅ Custom policies (any business logic)
- ✅ Custom approval (Slack, Jira, email, SMS)
- ✅ Production scaling (horizontal, HA)
- ✅ Full monitoring (events, metrics, traces)

**See `SIMPLICITY_VS_POWER.md` for complete comparison!**

### Progressive Complexity

```
Level 1: @govern()                     ← Start here (1 line)
Level 2: Add policies                  ← Still simple (2 lines)
Level 3: Add approval                  ← Getting useful (3 lines)
Level 4: Add callback                  ← Production ready
Level 5: Custom policies               ← Advanced
Level 6: Custom storage                ← Full control
Level 7: Production scaling            ← Enterprise
```

**You choose your complexity level. The framework adapts to you.**

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

Apache License 2.0 - see LICENSE file for details

## Credits

**Built by [Lyzr](https://www.lyzr.ai)**

Lyzr is building the future of agentic AI systems. Visit [lyzr.ai](https://www.lyzr.ai) to learn more.

---

**governor** - Governance for the age of autonomous agents.
