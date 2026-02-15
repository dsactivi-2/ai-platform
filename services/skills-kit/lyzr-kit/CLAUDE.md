# CLAUDE.md

Guidance for Claude Code when working with this repository.

## Project Overview

lyzr-kit is a Python SDK for managing AI agents via the Lyzr platform.

## CLI Commands

```bash
lk auth                    # Configure API credentials
lk ls                      # List agents (two tables)
lk get <source>            # Clone and deploy agent (creates copy-of-<name>)
lk set <identifier>        # Update agent on platform
lk chat <identifier>       # Interactive chat session
lk rm <identifier>         # Delete local agent
lk tree [identifier]       # Show agent dependency tree
lk doctor                  # Validate all local agents
```

**Note**: `agent` resource is optional. `lk ls` = `lk agent ls` = `lk a ls`

**Serial numbers**: Context-aware
- `get` → Built-in agents
- `set`/`chat`/`rm` → Your agents

## Agent Get Flow

The `get` command uses a plan-based approach:
1. Build clone plan (collects all dependencies recursively)
2. Display plan with single confirmation prompt
3. Execute plan (creates agents in dependency order)

```bash
$ lk get project-manager

Creating 'copy-of-project-manager' with 3 sub-agent(s):

  AGENT                        ACTION         FROM
  copy-of-task-planner         create         task-planner
  copy-of-data-analyst         create         data-analyst
  copy-of-summarizer           create         summarizer
  copy-of-project-manager      create         project-manager

Proceed? [Y/n]: y
```

No ID prompts - users rename via YAML edit + `lk set`.

## Storage

| Location | Purpose |
|----------|---------|
| `src/lyzr_kit/collection/agents/` | Built-in agents (bundled) |
| `agents/` | User agents (via `lk agent get`) |

## Project Structure

```
src/lyzr_kit/
├── main.py              # CLI entry point
├── schemas/             # Pydantic models (agent.py, tool.py, feature.py)
├── collection/agents/   # Built-in agent YAMLs
├── commands/            # CLI implementations
│   ├── _console.py      # Shared Rich console
│   ├── _resolver.py     # Serial number resolver
│   ├── _websocket.py    # WebSocket event streaming
│   ├── agent.py         # Agent Typer app
│   ├── agent_list.py    # ls command
│   ├── agent_get.py     # get command (plan-based cloning)
│   ├── agent_set.py     # set command
│   ├── agent_rm.py      # rm command (with --tree flag)
│   ├── agent_tree.py    # tree command
│   ├── agent_doctor.py  # doctor command
│   ├── agent_chat.py    # chat command (SSE + WebSocket)
│   ├── auth.py          # auth command
│   ├── tool.py          # stub
│   └── feature.py       # stub
├── storage/             # StorageManager, serialization, validation
└── utils/               # auth.py, platform.py

tests/
├── unit/commands/       # Command tests
├── unit/storage/        # Storage tests
└── integration/         # E2E tests
```

## Chat Implementation

Key files for chat functionality:
- `commands/agent_chat.py` - Main chat loop, UI boxes, SSE streaming
- `commands/_websocket.py` - WebSocket client, event parsing

Features:
- Session box (agent info, model, session ID, timestamp)
- Real-time WebSocket events (tool calls, memory, artifacts)
- SSE streaming for responses
- Metrics footer (latency, tokens)
- prompt_toolkit for keyboard shortcuts

## Sub-agent Features

- **Cycle detection** - Prevents circular dependencies (A → B → A)
- **Dependency plan** - Shows all agents to create before confirmation
- **Tree view** - `lk tree` shows dependency graph
- **Doctor** - `lk doctor` validates all local agents
- **Recursive delete** - `lk rm --tree` deletes agent + sub-agents

## Build Commands

```bash
pip install -e .        # Install dev mode
pytest tests/ -v        # Run tests
ruff check src/         # Lint
mypy src/               # Type check
```

## Phases

| Phase | Focus | Status |
|-------|-------|--------|
| 1 | Agents, CLI, storage | ✅ Done |
| 2 | Chat experience, WebSocket | ✅ Done |
| 3 | Sub-agents | ✅ Done |
| 4 | Tools | Stub |
| 5 | Features | Stub |

## Specs

- `specs/concepts/` - Entity definitions
- `specs/implementation/` - Technical details
- `specs/phases/` - Roadmap
