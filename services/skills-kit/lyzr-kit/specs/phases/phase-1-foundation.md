# Phase 1: Agents Foundation

## Overview

Phase 1 establishes the core agent system with CLI commands and storage implementation. Agents in this phase work without tools or features.

## Goals

- Set up Python package structure
- Implement agent schema and storage
- Build CLI commands (ls, get, set, auth)
- Establish testing infrastructure

## Deliverables

### 1. Package Structure

```
lyzr-kit/
├── pyproject.toml
├── README.md
├── src/
│   └── lyzr_kit/
│       ├── __init__.py
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── main.py
│       │   └── commands/
│       │       ├── agent.py
│       │       └── auth.py
│       ├── agents/
│       │   ├── __init__.py
│       │   └── schema.py
│       ├── storage/
│       │   ├── __init__.py
│       │   └── manager.py
│       └── utils/
├── tests/
└── .lyzr-kit/
    └── agents/
        ├── chat-agent.yaml
        └── qa-agent.yaml
```

### 2. Agent Schema

```python
# src/lyzr_kit/agents/schema.py
from pydantic import BaseModel, Field

class ModelConfig(BaseModel):
    provider: str
    name: str
    credential_id: str
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 4096

class AgentConfig(BaseModel):
    role: str = "assistant"
    goal: str = ""
    instructions: str = ""

class Agent(BaseModel):
    id: str
    name: str
    category: str  # chat | qa
    model: ModelConfig
    config: AgentConfig = Field(default_factory=AgentConfig)
    is_active: bool = False
    endpoint: str | None = None
```

### 3. Storage Manager

```python
# src/lyzr_kit/storage/manager.py
class StorageManager:
    def __init__(
        self,
        builtin_path: str = ".lyzr-kit",
        local_path: str = "local-kit",
    ):
        self.builtin_path = Path(builtin_path)
        self.local_path = Path(local_path)

    def list_agents(self) -> list[Agent]: ...
    def get_agent(self, agent_id: str) -> Agent: ...
    def save_agent(self, agent: Agent) -> None: ...
```

### 4. CLI Commands

| Command | Implementation |
|---------|----------------|
| `lk auth` | Prompt for API key, save to `.env` |
| `lk a ls` | List agents from both directories |
| `lk a get <id>` | Clone to `local-kit/agents/<id>.yaml` |
| `lk a set <id>` | Update from local YAML |

## Success Criteria

- `lk auth` saves API key to `.env`
- `lk a ls` shows built-in agents (chat-agent, qa-agent)
- `lk a get chat-agent` clones to `local-kit/agents/chat-agent.yaml`
- `lk a set chat-agent` updates from local YAML
- All tests pass

## Dependencies

- Python 3.10+
- pyyaml, pydantic, typer, rich, python-dotenv
