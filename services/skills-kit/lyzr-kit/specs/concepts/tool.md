# Tool Specification

## Overview

A **Tool** is a capability that agents can invoke to perform specific tasks. Tools extend agent functionality beyond text generation.

## Built-in Tools

| ID | Description |
|----|-------------|
| `file_reader` | Read contents from local files |
| `calculator` | Evaluate mathematical expressions |

## Schema

### YAML Definition

```yaml
# local-kit/tools/<tool-id>.yaml

# ============ META ============
id: "my-tool"                     # Unique identifier (snake_case)
name: "My Tool"                   # Display name
description: "A custom tool"      # Tool description

owner: "user-123"                 # Owner ID
share: "private"                  # private | org | public
tags: ["utility", "custom"]       # Searchable tags

created_at: "2024-01-01T00:00:00Z"
updated_at: "2024-01-01T00:00:00Z"

is_active: true                   # Set by 'lk tool get'
endpoint: "https://agent.api.lyzr.app/v3/tool/xyz789"  # Populated by 'get'

# ============ PARAMETERS ============
parameters:
  - name: "input"
    type: "string"                # string | number | boolean | array | object
    required: true
    description: "Input text"
  - name: "uppercase"
    type: "boolean"
    required: false
    default: false
    description: "Convert to uppercase"

# ============ RETURNS ============
returns:
  - name: "output"
    type: "string"
    description: "Processed result"
```

### Minimal Valid

```yaml
id: "my-tool"
name: "My Tool"
description: "Does something useful"
parameters:
  - name: "input"
    type: "string"
    required: true
    description: "Input value"
```

### Field Reference

#### Meta Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | string | Yes | - | Unique identifier (1-50 chars, snake_case) |
| `name` | string | Yes | - | Display name (1-100 chars) |
| `description` | string | Yes | - | Tool description (1-1000 chars) |
| `owner` | string | No | `null` | Owner user/org ID |
| `share` | enum | No | `"private"` | Sharing level: private, org, public |
| `tags` | string[] | No | `[]` | Searchable tags |
| `created_at` | datetime | No | `null` | Creation timestamp |
| `updated_at` | datetime | No | `null` | Last update timestamp |
| `is_active` | bool | No | `false` | Set to true by `lk tool get` |
| `endpoint` | string | No | `null` | Inference URL (populated by `get`) |

#### Parameter Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `parameters[].name` | string | Yes | - | Parameter name (1-50 chars) |
| `parameters[].type` | enum | Yes | - | string, number, boolean, array, object |
| `parameters[].required` | bool | No | `true` | Is parameter required |
| `parameters[].default` | any | No | `null` | Default value |
| `parameters[].description` | string | Yes | - | Parameter description |

#### Return Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `returns[].name` | string | Yes | - | Return field name |
| `returns[].type` | enum | Yes | - | string, number, boolean, array, object |
| `returns[].description` | string | Yes | - | Return field description |

## Operations

| Operation | Description | CLI Command |
|-----------|-------------|-------------|
| **ls** | List all tools | `lk tool ls` |
| **get** | Clone/activate tool | `lk tool get <id>` |
| **set** | Update tool | `lk tool set <id>` |

## Design Principles

1. **ID References**: Agents reference tools by ID
2. **Endpoint-Based**: Tools execute via inference endpoints
3. **Type Safety**: Strong parameter validation
4. **Platform-First**: Tools activated on Lyzr platform via `get`
