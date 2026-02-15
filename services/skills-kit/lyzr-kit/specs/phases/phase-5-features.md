# Phase 5: Features

## Overview

Phase 5 implements the feature system, enabling behavioral modifiers that extend or constrain agent behavior.

## Goals

- Implement feature schema and storage
- Add built-in features (memory, rag, pii_detector, rate_limiter)
- Build CLI commands for features (ls, get, set)
- Integrate features with agent execution pipeline

## Deliverables

### 1. Feature Schema

```python
# src/lyzr_kit/features/schema.py
class Feature(BaseModel):
    id: str
    name: str
    description: str
    category: str  # context | guard | policy
    config: dict = {}
    is_active: bool = False
    endpoint: str | None = None
```

### 2. Built-in Features

| ID | Category | Description |
|----|----------|-------------|
| `memory` | context | Conversation history |
| `rag` | context | Retrieval-augmented generation |
| `pii_detector` | guard | Detect/redact PII |
| `rate_limiter` | policy | Control request frequency |

### 3. Storage Structure

```
.lyzr-kit/
└── features/
    ├── memory.yaml
    ├── rag.yaml
    ├── pii_detector.yaml
    └── rate_limiter.yaml

local-kit/
└── features/
    └── <id>.yaml
```

### 4. CLI Commands

| Command | Implementation |
|---------|----------------|
| `lk f ls` | List features from both directories |
| `lk f get <id>` | Clone to `local-kit/features/<id>.yaml` |
| `lk f set <id>` | Update from local YAML |

### 5. Agent Integration

```yaml
# Agent with features
id: "my-agent"
name: "My Agent"
category: "chat"
model:
  provider: "openai"
  name: "gpt-4"
  credential_id: "lyzr_openai"
features:
  - "memory"
  - "pii_detector"
```

### 6. Feature Pipeline

Features execute in order by category:

```
Input → Guards → Context → Policies → LLM → Guards → Policies → Output
```

## Success Criteria

- `lk f ls` shows built-in features
- `lk f get memory` clones to local-kit
- Agent with features array can reference features by ID
- Features execute via inference endpoints
- Feature pipeline runs in correct order

## Dependencies

Requires Phase 1, Phase 2, Phase 3, and Phase 4 completion
