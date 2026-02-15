# CLI Commands Specification

## Command Structure

```
lk [resource] <action> [args...]
```

`agent` resource is optional (default). All equivalent:
- `lk ls` = `lk agent ls` = `lk a ls`

| Resource | Short | Actions |
|----------|-------|---------|
| `agent` | `a` | `ls`, `get`, `set`, `chat` (default) |
| `tool` | `t` | stub (Phase 4) |
| `feature` | `f` | stub (Phase 5) |

## Agent Commands

| Command | Description |
|---------|-------------|
| `lk ls` | List agents in two tables |
| `lk get <source>` | Clone and deploy to platform (creates `copy-of-<name>`) |
| `lk set <id>` | Update from local YAML |
| `lk chat <id>` | Interactive chat session |
| `lk rm <id>` | Delete local agent |
| `lk rm <id> --tree` | Delete agent and all sub-agents recursively |
| `lk rm <id> --force` | Remove from parent agents and delete |
| `lk tree [id]` | Show agent dependency tree |
| `lk doctor` | Validate all local agents |

### Serial Number Context

| Command | Context |
|---------|---------|
| `get` | Built-in agents |
| `set`/`chat` | Local agents |

## Chat Command

### Features
- **Session box** - Agent name, model, session ID, timestamp
- **WebSocket events** - Real-time activity (tool calls, memory, artifacts)
- **SSE streaming** - Live response rendering
- **Metrics footer** - Latency, token usage
- **Keyboard shortcuts** - Full readline (Option/Ctrl + arrows, history)
- **Exit** - `/exit` or `Ctrl+C`

### Display Format

```
╭─ Session ────────────────────────────────────────╮
│ Agent: My Assistant        Model: gpt-4         │
│ Session: abc123            Started: 14:32:15    │
╰──────────────────────────────────────────────────╯

You: What is the capital of France?

╭─ Agent ──────────────────────────────────────────╮
│ [Tool] Calling search_web...                    │
│ [Tool] search_web → {"results": [...]}          │
│ [Memory] Context updated                        │
│                                                  │
│ The capital of France is Paris.                 │
│──────────────────────────────────────────────────│
│ 1.23s                              45 → 128 tok │
╰──────────────────────────────────────────────────╯
```

### Event Types

| Event | Display |
|-------|---------|
| `tool_call_prepare` | `[Tool] Calling {name}...` |
| `tool_response` | `[Tool] {name} → {response}` |
| `context_memory_updated` | `[Memory] Context updated` |
| `artifact_create_success` | `[Artifact] Created: {name}` |
| `messages_retrieved` | `[Memory] Retrieved {count} messages` |

## Auth Command

```bash
lk auth
```

Prompts for:
- API key (required)
- User ID, Org ID, Memberstack token (optional)

Saves to `.env` and initializes `agents/` directory.

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

To rename an agent, edit the YAML file (change `id` field) and run `lk set`.

## Agent Tree Command

```bash
# Show all agent trees
$ lk tree

copy-of-project-manager
├── copy-of-task-planner
├── copy-of-data-analyst
└── copy-of-summarizer

# Show specific agent tree
$ lk tree copy-of-project-manager
```

## Agent Doctor Command

```bash
$ lk doctor

Running agent doctor...

  AGENT              ISSUE                        FIX
  broken-agent       Sub-agent 'helper' not found Run 'lk agent get helper'
  old-agent          Not deployed to platform     Run 'lk agent set old-agent'

Found 2 issue(s) (1/3 agents healthy)
```

Validates:
- Sub-agents exist locally
- No circular dependencies
- Agent is deployed to platform
- Agent is active

## Error Handling

| Error | Resolution |
|-------|------------|
| Serial not found | Shows agent list |
| ID exists | Use different ID |
| Not authenticated | Run `lk auth` |
| Agent not active | Run `lk agent get` first |
| Circular dependency | Remove one of the sub-agent references |
| Missing sub-agent | Run `lk get <sub-agent>` first |
