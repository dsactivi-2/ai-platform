# Lyzr Kit

Python SDK for managing AI agents via the Lyzr platform.

## Installation

```bash
pip install lyzr-kit
```

## Quick Start

```bash
# 1. Authenticate
lk auth

# 2. List agents (two tables: Built-in + Your Agents)
lk ls

# 3. Deploy an agent (creates copy-of-<name>)
lk get chat-agent

# 4. Chat with your agent
lk chat copy-of-chat-agent

# 5. Modify and update
# Edit agents/copy-of-chat-agent.yaml (change id field), then:
lk set copy-of-chat-agent
```

## Chat Experience

- **Session box** - Shows agent name, model, session ID, timestamp
- **Real-time activity** - WebSocket events stream inline (tool calls, memory, artifacts)
- **Streaming responses** - Live markdown-rendered output
- **Metrics footer** - Latency and token usage per response
- **Keyboard shortcuts** - Full readline support (Option/Ctrl + arrows, history)
- **Exit** - Type `/exit` or press `Ctrl+C`

## CLI Commands

| Command | Description |
|---------|-------------|
| `lk auth` | Configure API credentials |
| `lk ls` | List all agents |
| `lk get <source>` | Clone and deploy agent (creates `copy-of-<name>`) |
| `lk set <id>` | Update agent on platform |
| `lk chat <id>` | Interactive chat session |
| `lk rm <id>` | Delete local agent |
| `lk tree [id]` | Show agent dependency tree |
| `lk doctor` | Validate all local agents |

**Note**: `agent` resource is optional. `lk ls` = `lk agent ls` = `lk a ls`

**Serial numbers**: Context-aware lookup
- `get` → Built-in agents (`lk get 1`)
- `set`/`chat`/`rm` → Your agents (`lk chat 1`)

## Agent Get Flow

When you run `lk get`, the CLI shows a dependency plan and asks for confirmation:

```
$ lk get project-manager

Creating 'copy-of-project-manager' with 3 sub-agent(s):

  AGENT                        ACTION         FROM
  copy-of-task-planner         create         task-planner
  copy-of-data-analyst         create         data-analyst
  copy-of-summarizer           create         summarizer
  copy-of-project-manager      create         project-manager

Proceed? [Y/n]: y
```

To rename an agent, edit the YAML file and run `lk set`.

## Sub-agent Management

| Command | Description |
|---------|-------------|
| `lk tree` | Show all agent trees |
| `lk tree <id>` | Show specific agent tree |
| `lk doctor` | Validate all agents (missing subs, cycles, etc.) |
| `lk rm <id> --tree` | Delete agent and all its sub-agents |
| `lk rm <id> --force` | Delete even if used by other agents |

## Built-in Agents

| # | ID | Category | Sub-agents |
|---|-----|----------|------------|
| 1 | `chat-agent` | chat | - |
| 2 | `qa-agent` | qa | - |
| 3 | `summarizer` | qa | - |
| ... | ... | ... | ... |
| 13 | `project-manager` | chat | task-planner, data-analyst, summarizer |
| 14 | `dev-lead` | chat | code-reviewer, research-assistant |
| 15 | `tech-director` | chat | dev-lead, project-manager |

## Environment Variables

| Variable | Required |
|----------|----------|
| `LYZR_API_KEY` | Yes |
| `LYZR_USER_ID` | No |
| `LYZR_ORG_ID` | No |
| `LYZR_MEMBERSTACK_TOKEN` | No |

## Storage

- `agents/` - Your deployed agent configs
- `.env` - API credentials

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
ruff check src/
mypy src/
```

## Roadmap

| Phase | Focus | Status |
|-------|-------|--------|
| 1 | Agents, CLI, storage | ✅ Done |
| 2 | Chat experience, WebSocket events | ✅ Done |
| 3 | Sub-agents | ✅ Done |
| 4 | Tools | Pending |
| 5 | Features | Pending |

## License

MIT
