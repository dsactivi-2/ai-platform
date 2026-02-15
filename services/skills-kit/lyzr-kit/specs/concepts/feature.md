# Feature Specification

## Overview

A **Feature** is a behavioral modifier that extends or constrains agent behavior. Features are composable components that plug into the agent execution pipeline.

## Categories

| Category | Description | Examples |
|----------|-------------|----------|
| `context` | Provide additional context before LLM calls | `memory`, `rag`, `knowledge_base` |
| `guard` | Validate and filter inputs/outputs | `pii_detector`, `content_filter` |
| `policy` | Enforce operational constraints | `rate_limiter`, `cost_controller` |

## Built-in Features

| ID | Category | Description |
|----|----------|-------------|
| `memory` | context | Conversation history |
| `rag` | context | Retrieval-augmented generation |
| `pii_detector` | guard | Detect/redact PII |
| `rate_limiter` | policy | Control request frequency |

## Schema

### YAML Definition

```yaml
# local-kit/features/<feature-id>.yaml

# ============ META ============
id: "my-guard"                    # Unique identifier
name: "My Custom Guard"           # Display name
description: "Custom validation"  # Feature description
category: "guard"                 # context | guard | policy

owner: "user-123"                 # Owner ID
share: "private"                  # private | org | public
tags: ["validation", "custom"]    # Searchable tags

created_at: "2024-01-01T00:00:00Z"
updated_at: "2024-01-01T00:00:00Z"

is_active: true                   # Set by 'lk feature get'
endpoint: "https://agent.api.lyzr.app/v3/feature/def456"  # Populated by 'get'

# ============ CONFIG ============
config:
  blocked_words: ["spam", "malicious"]
  action: "block"                 # block | warn | redact
```

### Minimal Valid

```yaml
id: "my-guard"
name: "My Guard"
description: "Custom validation guard"
category: "guard"
```

### Field Reference

#### Meta Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | string | Yes | - | Unique identifier (1-50 chars) |
| `name` | string | Yes | - | Display name (1-100 chars) |
| `description` | string | Yes | - | Feature description (1-1000 chars) |
| `category` | enum | Yes | - | context, guard, policy |
| `owner` | string | No | `null` | Owner user/org ID |
| `share` | enum | No | `"private"` | Sharing level: private, org, public |
| `tags` | string[] | No | `[]` | Searchable tags |
| `created_at` | datetime | No | `null` | Creation timestamp |
| `updated_at` | datetime | No | `null` | Last update timestamp |
| `is_active` | bool | No | `false` | Set to true by `lk feature get` |
| `endpoint` | string | No | `null` | Inference URL (populated by `get`) |

#### Config Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `config` | object | No | `{}` | Feature-specific configuration |

## Operations

| Operation | Description | CLI Command |
|-----------|-------------|-------------|
| **ls** | List all features | `lk feature ls` |
| **get** | Clone/activate feature | `lk feature get <id>` |
| **set** | Update feature | `lk feature set <id>` |

## Design Principles

1. **ID References**: Agents reference features by ID
2. **Endpoint-Based**: Features execute via inference endpoints
3. **Category-Based Order**: Execution order determined by category
4. **Composable**: Features stack and combine cleanly
5. **Platform-First**: Features activated on Lyzr platform via `get`
