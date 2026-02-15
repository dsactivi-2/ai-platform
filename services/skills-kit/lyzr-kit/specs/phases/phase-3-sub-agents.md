# Phase 3: Sub-agents ✅

## Overview

Phase 3 implements sub-agent orchestration, enabling agents to delegate tasks to other agents via the `sub_agents` array.

## Status: Complete

All deliverables have been implemented.

## Implemented Features

### 1. Plan-Based Agent Cloning

When cloning an agent with sub-agents, the system:
1. Builds a complete dependency plan (recursive)
2. Displays the plan with a single confirmation prompt
3. Executes the plan in dependency order

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

### 2. Default ID Generation

- Format: `copy-of-<source-id>`
- Handles conflicts: `copy-of-chat-agent-2`, `-3`, etc.
- No user prompts for IDs - users rename via YAML edit + `lk set`

### 3. Circular Dependency Detection

```python
def detect_cycle(
    agent_id: str,
    sub_agents: list[str],
    storage: StorageManager,
) -> list[str] | None:
    """Detect circular dependencies in sub-agent graph.

    Returns:
        None if no cycle, or list of IDs forming the cycle.
    """
```

Error output:
```
Error: Circular sub-agent dependency detected

  agent-a → agent-b → agent-c → agent-a

Sub-agent relationships must be acyclic. Remove one of the references.
```

### 4. Agent Tree Command

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

### 5. Agent Doctor Command

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

### 6. Recursive Delete (--tree flag)

```bash
# Shows hint about sub-agents
$ lk rm copy-of-project-manager

Agent 'copy-of-project-manager' has 3 sub-agent(s):
  • copy-of-task-planner
  • copy-of-data-analyst
  • copy-of-summarizer

Delete sub-agents too? Use --tree flag.

# Deletes all recursively
$ lk rm copy-of-project-manager --tree
  ✓ copy-of-task-planner
  ✓ copy-of-data-analyst
  ✓ copy-of-summarizer

4 agent(s) deleted successfully
```

### 7. Validation on Set

When running `lk agent set`:
- Validates all referenced sub-agents exist locally
- Detects circular dependencies
- Shows clear error messages with fix hints

## CLI Commands

| Command | Description |
|---------|-------------|
| `lk get <source>` | Clone with dependency plan preview |
| `lk set <id>` | Validate sub-agents + detect cycles |
| `lk rm <id>` | Show sub-agents hint |
| `lk rm <id> --tree` | Delete agent + sub-agents recursively |
| `lk rm <id> --force` | Remove from parent agents and delete |
| `lk tree` | Show all agent dependency trees |
| `lk tree <id>` | Show specific agent tree |
| `lk doctor` | Validate all local agents |

## Agent Schema

```yaml
# Agent with sub-agents
id: "project-manager"
name: "Project Manager"
category: "chat"
model:
  provider: "openai"
  name: "gpt-4"
  credential_id: "lyzr_openai"
sub_agents:
  - "task-planner"
  - "data-analyst"
  - "summarizer"
```

## Built-in Agents with Sub-agents

| Agent | Sub-agents |
|-------|------------|
| `project-manager` | task-planner, data-analyst, summarizer |
| `dev-lead` | code-reviewer, research-assistant |
| `tech-director` | dev-lead, project-manager |

## Files

| File | Purpose |
|------|---------|
| `commands/agent_get.py` | Plan-based cloning with dependency resolution |
| `commands/agent_set.py` | Sub-agent validation + cycle detection |
| `commands/agent_rm.py` | Recursive delete with --tree flag |
| `commands/agent_tree.py` | Dependency tree visualization |
| `commands/agent_doctor.py` | Agent health validation |
| `storage/validator.py` | `detect_cycle()`, `validate_sub_agents()` |

## Success Criteria ✅

- [x] Agent with `sub_agents` array deploys successfully
- [x] Missing sub-agent shows clear error message
- [x] Circular dependencies are detected and reported
- [x] Dependency plan shows all agents before confirmation
- [x] Sub-agent validation runs on both `get` and `set`
- [x] `--tree` flag deletes sub-agents recursively
- [x] `lk tree` shows dependency graph
- [x] `lk doctor` validates all local agents

## Dependencies

Requires Phase 1 and Phase 2 completion ✅
