# Phase 4: Tools

## Overview

Phase 4 implements the tool system, enabling agents to invoke tools for extended functionality.

## Goals

- Implement tool schema and storage
- Add built-in tools (file_reader, calculator)
- Build CLI commands for tools (ls, get, set)
- Integrate tools with agent execution

## Deliverables

### 1. Tool Schema

```python
# src/lyzr_kit/tools/schema.py
class ToolParameter(BaseModel):
    name: str
    type: str  # string | number | boolean | array | object
    required: bool = True
    default: Any = None
    description: str

class Tool(BaseModel):
    id: str
    name: str
    description: str
    parameters: list[ToolParameter]
    returns: list[ToolParameter] = []
    is_active: bool = False
    endpoint: str | None = None
```

### 2. Built-in Tools

| ID | Description |
|----|-------------|
| `file_reader` | Read contents from local files |
| `calculator` | Evaluate mathematical expressions |

### 3. Storage Structure

```
.lyzr-kit/
└── tools/
    ├── file_reader.yaml
    └── calculator.yaml

local-kit/
└── tools/
    └── <id>.yaml
```

### 4. CLI Commands

| Command | Implementation |
|---------|----------------|
| `lk t ls` | List tools from both directories |
| `lk t get <id>` | Clone to `local-kit/tools/<id>.yaml` |
| `lk t set <id>` | Update from local YAML |

### 5. Agent Integration

```yaml
# Agent with tools
id: "my-agent"
name: "My Agent"
category: "chat"
model:
  provider: "openai"
  name: "gpt-4"
  credential_id: "lyzr_openai"
tools:
  - "file_reader"
  - "calculator"
```

## Success Criteria

- `lk t ls` shows built-in tools
- `lk t get file_reader` clones to local-kit
- Agent with tools array can reference tools by ID
- Tools execute via inference endpoints

## Dependencies

Requires Phase 1, Phase 2, and Phase 3 completion
