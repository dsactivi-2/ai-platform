# Production Deployment Guide

This guide covers deploying **governor** in production environments with proper state persistence, background job processing, and scalable approval workflows.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [State Persistence Setup](#state-persistence-setup)
3. [Background Worker Configuration](#background-worker-configuration)
4. [Approval Workflow Integration](#approval-workflow-integration)
5. [Scaling Considerations](#scaling-considerations)
6. [Deployment Examples](#deployment-examples)
7. [Monitoring and Observability](#monitoring-and-observability)

---

## Architecture Overview

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                     API Layer (FastAPI)                      │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐│
│  │  @govern       │  │  Approval API  │  │  Status API    ││
│  │  Endpoints     │  │  /approve/{id} │  │  /jobs/{id}    ││
│  └────────┬───────┘  └────────┬───────┘  └────────┬───────┘│
└───────────┼──────────────────┼──────────────────┼──────────┘
            │                  │                  │
            ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                   Governance Engine                          │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Policy      │  │ Approval     │  │ Event        │       │
│  │ Evaluation  │  │ Manager      │  │ Emitter      │       │
│  └─────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
            │                  │                  │
            ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Storage Layer                             │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ MongoDB     │  │ Redis        │  │ Event Log    │       │
│  │ (State)     │  │ (Cache)      │  │ (Audit)      │       │
│  └─────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│                 Background Workers                           │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Job Queue   │  │ Auto-Resume  │  │ Compliance   │       │
│  │ Worker      │  │ Manager      │  │ Reporter     │       │
│  └─────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### Approval Patterns

**Pattern 1: Sync Wait** (Development/Interactive)
- Connection stays open during approval
- Use for timeouts < 5 minutes
- Best for: Slack buttons, CLI prompts, web forms

**Pattern 2: Async Job Queue** (Production)
- Returns 202 Accepted immediately
- State persisted to database
- Background worker resumes on approval
- Use for timeouts > 5 minutes (hours/days)
- Best for: Email approvals, business workflows

---

## State Persistence Setup

### MongoDB Configuration

#### Installation

```bash
# Docker
docker run -d \
  --name governor-mongo \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=password \
  -v mongo-data:/data/db \
  mongo:7

# Or use managed service (MongoDB Atlas, AWS DocumentDB)
```

#### Application Configuration

```python
# config.py
import os
from governor.storage.mongodb import MongoDBStorage

# Connection string from environment
MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://admin:password@localhost:27017"
)

# Initialize storage
storage = MongoDBStorage(
    uri=MONGODB_URI,
    database="governor_prod",
    # Optional: configure collections
    execution_collection="executions",
    event_collection="events",
    snapshot_collection="snapshots"
)

# Initialize on startup
async def startup():
    await storage.initialize()
```

#### Production Settings

```python
# production_config.py
MONGODB_CONFIG = {
    # Connection
    "uri": os.getenv("MONGODB_URI"),
    "database": "governor_prod",

    # Connection pool
    "maxPoolSize": 100,
    "minPoolSize": 10,

    # Timeouts
    "serverSelectionTimeoutMS": 5000,
    "connectTimeoutMS": 10000,

    # Replica set (for high availability)
    "replicaSet": "rs0",
    "readPreference": "secondaryPreferred",

    # Write concern (for critical operations)
    "w": "majority",
    "journal": True,
}

storage = MongoDBStorage(**MONGODB_CONFIG)
```

#### Indexes for Performance

```python
# migrations/create_indexes.py
async def create_indexes(storage: MongoDBStorage):
    """Create indexes for optimal query performance."""

    # Execution indexes
    await storage._executions.create_index([("execution_id", 1)], unique=True)
    await storage._executions.create_index([("function_name", 1), ("status", 1)])
    await storage._executions.create_index([("started_at", -1)])
    await storage._executions.create_index([("status", 1), ("approval_required", 1)])

    # Event indexes
    await storage._events.create_index([("execution_id", 1), ("timestamp", -1)])
    await storage._events.create_index([("event_type", 1), ("timestamp", -1)])

    # Snapshot indexes
    await storage._snapshots.create_index([("execution_id", 1), ("checkpoint", 1)])
    await storage._snapshots.create_index([("captured_at", -1)])

    # TTL index for old data (optional)
    await storage._events.create_index(
        [("timestamp", 1)],
        expireAfterSeconds=90 * 24 * 60 * 60  # 90 days
    )
```

---

## Background Worker Configuration

### Job Queue Integration

#### Option 1: Built-in Background Queue (Simple)

```python
# worker.py
import asyncio
from governor.background import BackgroundJobQueue, AutoResumeManager
from governor.storage.mongodb import MongoDBStorage
from your_app import governed_functions

async def main():
    # Initialize storage
    storage = MongoDBStorage(uri=MONGODB_URI, database="governor_prod")
    await storage.initialize()

    # Start job queue
    job_queue = BackgroundJobQueue()
    await job_queue.start()

    # Start auto-resume manager
    auto_resume = AutoResumeManager(storage=storage, job_queue=job_queue)

    # Register all governed functions
    auto_resume.register_function("process_payment", governed_functions.process_payment)
    auto_resume.register_function("send_wire_transfer", governed_functions.send_wire_transfer)
    auto_resume.register_function("delete_user_data", governed_functions.delete_user_data)

    await auto_resume.start()

    print("✓ Background worker started")
    print("  Listening for approval events...")

    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        await auto_resume.stop()
        await job_queue.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

Run worker:
```bash
python worker.py
```

#### Option 2: Celery Integration (Production Scale)

```python
# celery_worker.py
from celery import Celery
from governor.storage.mongodb import MongoDBStorage
from governor.replay import ReplayEngine

# Configure Celery
celery_app = Celery(
    'governor_worker',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1'
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

# Storage singleton
storage = MongoDBStorage(uri=MONGODB_URI, database="governor_prod")
replay_engine = ReplayEngine(storage)

@celery_app.task(name='resume_execution', bind=True)
def resume_execution_task(self, execution_id: str, function_name: str):
    """Resume an approved execution."""
    import asyncio

    async def _resume():
        # Get snapshot
        snapshot = await replay_engine.get_last_snapshot(execution_id)
        if not snapshot:
            raise ValueError(f"No snapshot for {execution_id}")

        # Restore state
        state = snapshot.restore_state()
        args = state.get("function_args", {}).get("args", ())
        kwargs = state.get("function_kwargs", {})

        # Get function
        from your_app import governed_functions
        func = getattr(governed_functions, function_name)

        # Execute
        result = await func(*args, **kwargs)
        return result

    return asyncio.run(_resume())

# Start worker:
# celery -A celery_worker worker --loglevel=info --concurrency=4
```

#### Option 3: RQ (Redis Queue) Integration

```python
# rq_worker.py
from rq import Queue, Worker
from redis import Redis
import asyncio
from governor.storage.mongodb import MongoDBStorage

# Redis connection
redis_conn = Redis(host='localhost', port=6379, db=0)
queue = Queue('governor', connection=redis_conn)

# Storage
storage = MongoDBStorage(uri=MONGODB_URI, database="governor_prod")

def resume_execution_job(execution_id: str, function_name: str):
    """Job function to resume execution."""
    async def _resume():
        from governor.replay import ReplayEngine
        from your_app import governed_functions

        replay = ReplayEngine(storage)
        snapshot = await replay.get_last_snapshot(execution_id)
        state = snapshot.restore_state()

        func = getattr(governed_functions, function_name)
        result = await func(
            *state.get("function_args", {}).get("args", ()),
            **state.get("function_kwargs", {})
        )
        return result

    return asyncio.run(_resume())

# Submit job from approval handler:
# job = queue.enqueue(resume_execution_job, execution_id, function_name)

# Start worker:
# rq worker governor
```

### Systemd Service (Linux)

```ini
# /etc/systemd/system/governor-worker.service
[Unit]
Description=Agent Govern Background Worker
After=network.target mongodb.service

[Service]
Type=simple
User=appuser
Group=appuser
WorkingDirectory=/opt/governor
Environment="MONGODB_URI=mongodb://localhost:27017"
Environment="PYTHONPATH=/opt/governor"
ExecStart=/usr/bin/python3 /opt/governor/worker.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable governor-worker
sudo systemctl start governor-worker
sudo systemctl status governor-worker
```

---

## Approval Workflow Integration

### Webhook-Based Approval (Production Pattern)

#### 1. API Endpoint for Approvals

```python
# approval_api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from governor.approval.manager import get_default_approval_manager

app = FastAPI()

class ApprovalRequest(BaseModel):
    execution_id: str
    approved: bool
    approver: str
    reason: str

@app.post("/api/approve")
async def approve_execution(request: ApprovalRequest):
    """
    Webhook endpoint for approval.

    Called by external systems (email link, Slack button, etc.)
    """
    manager = get_default_approval_manager()

    # Validate execution exists
    from config import storage
    context = await storage.get_execution(request.execution_id)
    if not context:
        raise HTTPException(status_code=404, detail="Execution not found")

    # Record decision
    manager.provide_decision(
        execution_id=request.execution_id,
        approved=request.approved,
        approver=request.approver,
        reason=request.reason
    )

    return {
        "status": "recorded",
        "execution_id": request.execution_id,
        "decision": "approved" if request.approved else "rejected"
    }

@app.get("/api/executions/{execution_id}")
async def get_execution_status(execution_id: str):
    """Poll endpoint for execution status."""
    from config import storage

    context = await storage.get_execution(execution_id)
    if not context:
        raise HTTPException(status_code=404, detail="Execution not found")

    return {
        "execution_id": execution_id,
        "status": context.status,
        "function_name": context.function_name,
        "started_at": context.started_at.isoformat(),
        "completed_at": context.completed_at.isoformat() if context.completed_at else None,
        "outputs": context.outputs,
        "approval_required": context.approval_required
    }
```

#### 2. Email Approval Integration

```python
# email_approval.py
from governor.approval.handlers import ApprovalHandler
import aiosmtplib
from email.message import EmailMessage

class EmailApprovalHandler(ApprovalHandler):
    """Send approval request via email with magic link."""

    def __init__(self, smtp_host: str, smtp_port: int, from_email: str,
                 approval_base_url: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.from_email = from_email
        self.approval_base_url = approval_base_url

    async def request_approval(
        self,
        execution_id: str,
        function_name: str,
        inputs: dict,
        approvers: list[str],
    ) -> tuple[bool, str, str]:
        """
        Send email and return immediately (async pattern).

        Returns (None, None, None) to trigger timeout -> async pattern
        """
        # Generate approval link
        approve_link = f"{self.approval_base_url}/approve?id={execution_id}&decision=approve"
        reject_link = f"{self.approval_base_url}/approve?id={execution_id}&decision=reject"

        # Create email
        message = EmailMessage()
        message["Subject"] = f"Approval Required: {function_name}"
        message["From"] = self.from_email
        message["To"] = ", ".join(approvers)

        message.set_content(f"""
Approval Required
=================

Function: {function_name}
Execution ID: {execution_id}

Inputs:
{inputs}

Actions:
- Approve: {approve_link}
- Reject: {reject_link}

This request will expire in 24 hours.
        """)

        # Send email
        async with aiosmtplib.SMTP(hostname=self.smtp_host, port=self.smtp_port) as smtp:
            await smtp.send_message(message)

        print(f"📧 Approval email sent to: {', '.join(approvers)}")

        # Return "pending" - will trigger timeout and async pattern
        # Actual approval happens via webhook when user clicks link
        import asyncio
        await asyncio.sleep(3600)  # Wait longer than timeout
        return (False, "system", "Email sent - awaiting response")

# Usage in governed function:
handler = EmailApprovalHandler(
    smtp_host="smtp.company.com",
    smtp_port=587,
    from_email="approvals@company.com",
    approval_base_url="https://approvals.company.com"
)

@govern(
    policies=[ApprovalPolicy(approvers=["cfo@company.com"], timeout_seconds=60)],
    approval_handler=handler,
    capture_state=True  # Must capture state for async
)
async def wire_transfer(amount: int, recipient: str):
    # ... implementation
    pass
```

#### 3. Slack Approval Integration

```python
# slack_approval.py
from governor.approval.handlers import ApprovalHandler
from slack_sdk.web.async_client import AsyncWebClient

class SlackApprovalHandler(ApprovalHandler):
    """Send approval request to Slack with interactive buttons."""

    def __init__(self, slack_token: str, channel: str, approval_webhook_url: str):
        self.client = AsyncWebClient(token=slack_token)
        self.channel = channel
        self.approval_webhook_url = approval_webhook_url

    async def request_approval(
        self,
        execution_id: str,
        function_name: str,
        inputs: dict,
        approvers: list[str],
    ) -> tuple[bool, str, str]:
        """Send Slack message with approval buttons."""

        # Create message with buttons
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🔔 Approval Required: {function_name}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Execution ID:*\n{execution_id}"},
                    {"type": "mrkdwn", "text": f"*Approvers:*\n{', '.join(approvers)}"},
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Inputs:*\n```{inputs}```"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "✅ Approve"},
                        "style": "primary",
                        "value": f"{execution_id}:approve",
                        "action_id": "approve_action"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "❌ Reject"},
                        "style": "danger",
                        "value": f"{execution_id}:reject",
                        "action_id": "reject_action"
                    }
                ]
            }
        ]

        # Send to Slack
        response = await self.client.chat_postMessage(
            channel=self.channel,
            text=f"Approval required for {function_name}",
            blocks=blocks
        )

        print(f"📱 Slack approval request sent (message: {response['ts']})")

        # For sync pattern (< 5 min timeout), wait for response
        # For async pattern (> 5 min timeout), return immediately
        import asyncio
        await asyncio.sleep(300)  # Trigger timeout for async
        return (False, "system", "Slack message sent")

# Slack webhook handler (receives button clicks):
@app.post("/slack/interactive")
async def handle_slack_interaction(payload: dict):
    """Handle Slack button clicks."""
    action = payload["actions"][0]
    execution_id, decision = action["value"].split(":")
    approver = payload["user"]["name"]

    manager = get_default_approval_manager()
    manager.provide_decision(
        execution_id=execution_id,
        approved=(decision == "approve"),
        approver=approver,
        reason=f"Slack approval: {decision}"
    )

    return {"response_type": "in_channel", "text": f"Decision recorded: {decision}"}
```

---

## Scaling Considerations

### Horizontal Scaling

```yaml
# docker-compose.yml
version: '3.8'

services:
  # API Layer (multiple instances)
  api-1:
    build: .
    command: uvicorn main:app --host 0.0.0.0 --port 8000
    environment:
      - MONGODB_URI=mongodb://mongo:27017
      - REDIS_URL=redis://redis:6379
    depends_on:
      - mongo
      - redis
    deploy:
      replicas: 3

  # Background Workers (multiple instances)
  worker:
    build: .
    command: python worker.py
    environment:
      - MONGODB_URI=mongodb://mongo:27017
    depends_on:
      - mongo
    deploy:
      replicas: 2

  # MongoDB (replica set for HA)
  mongo:
    image: mongo:7
    command: --replSet rs0
    volumes:
      - mongo-data:/data/db

  # Redis (for caching and job queue)
  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data

  # Load Balancer
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - api-1

volumes:
  mongo-data:
  redis-data:
```

### Kubernetes Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: governor-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: governor-api
  template:
    metadata:
      labels:
        app: governor-api
    spec:
      containers:
      - name: api
        image: governor:latest
        command: ["uvicorn", "main:app", "--host", "0.0.0.0"]
        ports:
        - containerPort: 8000
        env:
        - name: MONGODB_URI
          valueFrom:
            secretKeyRef:
              name: governor-secrets
              key: mongodb-uri
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: governor-worker
spec:
  replicas: 2
  selector:
    matchLabels:
      app: governor-worker
  template:
    metadata:
      labels:
        app: governor-worker
    spec:
      containers:
      - name: worker
        image: governor:latest
        command: ["python", "worker.py"]
        env:
        - name: MONGODB_URI
          valueFrom:
            secretKeyRef:
              name: governor-secrets
              key: mongodb-uri
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"

---
apiVersion: v1
kind: Service
metadata:
  name: governor-api-service
spec:
  selector:
    app: governor-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

### Performance Optimization

```python
# optimized_config.py

# Connection pooling
MONGODB_CONFIG = {
    "maxPoolSize": 100,  # Max connections
    "minPoolSize": 10,   # Min connections
    "maxIdleTimeMS": 30000,
}

# Caching layer
from functools import lru_cache
import redis.asyncio as redis

redis_client = redis.from_url("redis://localhost:6379")

@lru_cache(maxsize=1000)
async def get_policy_config(policy_id: str):
    """Cache policy configs."""
    # Check Redis first
    cached = await redis_client.get(f"policy:{policy_id}")
    if cached:
        return json.loads(cached)

    # Load from storage
    policy = await storage.get_policy(policy_id)

    # Cache for 1 hour
    await redis_client.setex(
        f"policy:{policy_id}",
        3600,
        json.dumps(policy)
    )

    return policy

# Batch operations
async def batch_store_events(events: list):
    """Store events in batches for better performance."""
    if len(events) > 100:
        # Process in chunks
        for i in range(0, len(events), 100):
            chunk = events[i:i+100]
            await storage.store_events_batch(chunk)
    else:
        await storage.store_events_batch(events)
```

---

## Deployment Examples

### Docker Compose (Quick Start)

```yaml
# docker-compose.prod.yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.prod
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URI=mongodb://mongo:27017
      - ENVIRONMENT=production
    depends_on:
      - mongo
    restart: unless-stopped

  worker:
    build:
      context: .
      dockerfile: Dockerfile.prod
    command: python worker.py
    environment:
      - MONGODB_URI=mongodb://mongo:27017
    depends_on:
      - mongo
    restart: unless-stopped

  mongo:
    image: mongo:7
    volumes:
      - ./data/mongo:/data/db
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped
```

```dockerfile
# Dockerfile.prod
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY governor/ ./governor/
COPY main.py worker.py ./

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### AWS Deployment (ECS + DocumentDB)

```json
{
  "family": "governor",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "your-registry/governor:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "MONGODB_URI",
          "value": "mongodb://docdb-cluster.region.docdb.amazonaws.com:27017"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/governor",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "api"
        }
      }
    }
  ]
}
```

---

## Monitoring and Observability

### Health Checks

```python
# health.py
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/health")
async def health_check():
    """Liveness probe - is the service running?"""
    return {"status": "healthy"}

@app.get("/ready")
async def readiness_check():
    """Readiness probe - can the service accept traffic?"""
    from config import storage

    # Check MongoDB connection
    try:
        await storage.ping()
        mongo_ok = True
    except Exception:
        mongo_ok = False

    if not mongo_ok:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not ready", "mongo": "down"}
        )

    return {"status": "ready", "mongo": "up"}
```

### Metrics and Logging

```python
# metrics.py
from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Response
import structlog

# Metrics
execution_counter = Counter(
    'governance_executions_total',
    'Total number of governed executions',
    ['function_name', 'status']
)

approval_duration = Histogram(
    'approval_duration_seconds',
    'Time waiting for approval',
    ['function_name']
)

policy_violations = Counter(
    'policy_violations_total',
    'Total number of policy violations',
    ['policy_type', 'function_name']
)

# Structured logging
logger = structlog.get_logger()

# Usage in decorator:
class MetricsMiddleware:
    async def on_execution_start(self, context):
        logger.info("execution.started",
                   execution_id=context.execution_id,
                   function=context.function_name)

    async def on_execution_complete(self, context):
        execution_counter.labels(
            function_name=context.function_name,
            status=context.status
        ).inc()

        logger.info("execution.completed",
                   execution_id=context.execution_id,
                   duration=(context.completed_at - context.started_at).total_seconds())

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type="text/plain")
```

### Distributed Tracing

```python
# tracing.py
from opentelemetry import trace
from opentelemetry.exporter.jaeger import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Setup tracing
trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

tracer = trace.get_tracer(__name__)

# Usage in decorator:
class TracingMiddleware:
    async def on_execution_start(self, context):
        with tracer.start_as_current_span("governance.execution") as span:
            span.set_attribute("function.name", context.function_name)
            span.set_attribute("execution.id", context.execution_id)
```

---

## Security Best Practices

### Environment Variables

```bash
# .env.production
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/governor
SECRET_KEY=your-secret-key-change-this
ALLOWED_HOSTS=api.company.com
CORS_ORIGINS=https://app.company.com
APPROVAL_WEBHOOK_SECRET=webhook-secret-change-this
```

### Secret Management

```python
# secrets.py
import os
from typing import Optional

def get_secret(key: str, default: Optional[str] = None) -> str:
    """
    Get secret from environment or secret manager.

    Priority:
    1. Environment variable
    2. AWS Secrets Manager
    3. Default value
    """
    # Try environment first
    value = os.getenv(key)
    if value:
        return value

    # Try AWS Secrets Manager
    try:
        import boto3
        client = boto3.client('secretsmanager')
        response = client.get_secret_value(SecretId=f'governor/{key}')
        return response['SecretString']
    except Exception:
        pass

    # Fall back to default
    if default is not None:
        return default

    raise ValueError(f"Secret {key} not found")

# Usage:
MONGODB_URI = get_secret("MONGODB_URI")
```

### Network Security

```nginx
# nginx.conf
http {
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=approval_limit:10m rate=10r/s;

    server {
        listen 443 ssl http2;
        server_name api.company.com;

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;

        # Security headers
        add_header Strict-Transport-Security "max-age=31536000" always;
        add_header X-Frame-Options "DENY" always;
        add_header X-Content-Type-Options "nosniff" always;

        location /api/approve {
            limit_req zone=approval_limit burst=5;
            proxy_pass http://api:8000;
        }
    }
}
```

---

## Troubleshooting

### Common Issues

**Issue: Worker not resuming executions**
```bash
# Check worker logs
docker logs governor-worker

# Verify MongoDB connection
docker exec -it governor-mongo mongosh
> use governor_prod
> db.executions.find({status: "approved"})

# Check if functions are registered
# Look for: "Function X not registered for auto-resume"
```

**Issue: Approval decisions not persisted**
```python
# Verify storage configuration
from config import storage
context = await storage.get_execution("exec-123")
print(context.status)  # Should show "approved" or "rejected"

# Check event emission
events = await storage.list_events(execution_id="exec-123")
for event in events:
    print(f"{event.event_type}: {event.metadata}")
```

**Issue: High latency in production**
```python
# Enable query profiling
await storage._executions.database.command({
    "profile": 2,  # Log all operations
    "slowms": 100  # Log queries > 100ms
})

# Check slow queries
slow_queries = await storage._executions.database.system.profile.find({
    "millis": {"$gt": 100}
}).to_list(length=10)
```

---

## Checklist: Production Readiness

- [ ] MongoDB configured with replica set
- [ ] Indexes created for all collections
- [ ] Background worker running and registered functions
- [ ] Approval webhook endpoint secured (rate limiting, auth)
- [ ] Environment variables/secrets properly configured
- [ ] Health check endpoints implemented
- [ ] Logging and monitoring configured
- [ ] SSL/TLS certificates installed
- [ ] Backup strategy implemented
- [ ] Disaster recovery plan documented
- [ ] Load testing completed
- [ ] Security audit completed

---

## Next Steps

1. **Development**: Start with Pattern 1 (Sync Wait) for simple use cases
2. **Staging**: Test Pattern 2 (Async Job) with MongoDB + background worker
3. **Production**: Deploy with HA MongoDB, multiple workers, monitoring
4. **Scale**: Add Celery/RQ, Redis caching, horizontal scaling

For more examples, see:
- `examples/approval_patterns.py` - Pattern comparison
- `examples/fastapi_integration.py` - API deployment
- `examples/criteria_based_governance.py` - Advanced policies
