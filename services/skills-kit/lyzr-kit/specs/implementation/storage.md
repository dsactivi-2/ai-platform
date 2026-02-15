# Storage Specification

## Overview

Lyzr Kit uses a two-location storage system:

| Location | Purpose | Contents |
|----------|---------|----------|
| `src/lyzr_kit/collection/` | Built-in resources | SDK-provided agents, tools, features |
| `agents/` | Cloned resources | User agents created via `lk agent get` |

## Directory Structure

```
project/
├── agents/                          # Cloned agents (via `lk agent get`)
│   ├── my-assistant.yaml
│   └── my-qa-bot.yaml
├── tools/                           # Cloned tools (Phase 4)
├── features/                        # Cloned features (Phase 5)
├── .env                             # API keys and credentials
├── .gitignore                       # Git ignore (excludes .env)
└── README.md                        # Project README

# Inside the lyzr-kit package:
src/lyzr_kit/collection/
├── agents/                          # Built-in agents
│   ├── chat-agent.yaml
│   ├── qa-agent.yaml
│   ├── code-reviewer.yaml
│   └── ...
├── tools/                           # Built-in tools (Phase 4)
└── features/                        # Built-in features (Phase 5)
```

## Resource Paths

| Resource | Built-in Path | Cloned Path |
|----------|---------------|-------------|
| Agent | `src/lyzr_kit/collection/agents/<id>.yaml` | `agents/<id>.yaml` |
| Tool | `src/lyzr_kit/collection/tools/<id>.yaml` | `tools/<id>.yaml` |
| Feature | `src/lyzr_kit/collection/features/<id>.yaml` | `features/<id>.yaml` |

## Serial Numbers

Both built-in and local agents use positive serial numbers:

| Type | Serial Range | Display Format |
|------|--------------|----------------|
| Built-in | 1, 2, 3... | `#1`, `#2`, `#3`... |
| Local | 1, 2, 3... | `@1`, `@2`, `@3`... |

Serial numbers are:
- Stored in the `serial` field in YAML files
- Auto-assigned by `lk agent get` for local agents
- Used for quick reference in CLI commands

## Project Initialization

Running `lk auth` initializes the project structure:

1. Creates `agents/` directory
2. Creates `README.md` with project info
3. Creates `.gitignore` (excludes `.env`)
4. Saves credentials to `.env`

## File Formats

| File | Format | Description |
|------|--------|-------------|
| `<agent-id>.yaml` | YAML | Agent definition with all config |
| `.env` | dotenv | API keys and credentials |
| `README.md` | Markdown | Project documentation |
| `.gitignore` | Git | Files to exclude from version control |

## YAML Validation

The storage system validates YAML files:

| Check | Error |
|-------|-------|
| Syntax | "Invalid YAML syntax" with details |
| Empty file | "Empty YAML file" |
| Missing required fields | Schema error with expected fields |
| Invalid field types | Schema error with field requirements |

### Folder Validation

The `agents/` folder is validated for:

| Issue | Error |
|-------|-------|
| Nested folders | "Nested folders not allowed" |
| Non-YAML files | "Invalid file extension" |
| Invalid YAML | "Invalid YAML syntax" |
| Invalid schema | "Invalid agent schema" |

## Environment Variables

Stored in `.env` file:

| Variable | Required | Description |
|----------|----------|-------------|
| `LYZR_API_KEY` | Yes | API key for Lyzr platform |
| `LYZR_USER_ID` | No | User ID for agent ownership |
| `LYZR_ORG_ID` | No | Organization ID |
| `LYZR_MEMBERSTACK_TOKEN` | No | Token for marketplace features |

## Security

| Aspect | Implementation |
|--------|----------------|
| Secrets | Stored in `.env`, never in YAML |
| Git exclusion | `.env` added to `.gitignore` |
| API key input | Hidden during `lk auth` prompt |

## StorageManager

The `StorageManager` class provides:

| Method | Description |
|--------|-------------|
| `list_agents()` | Returns all agents (built-in + local) with source |
| `get_agent(id)` | Get agent by ID from any collection |
| `save_agent(agent)` | Save agent to `agents/<id>.yaml` |
| `agent_exists(id)` | Check if agent ID exists anywhere |

## Design Principles

1. **Package-Bundled Built-ins**: Built-in agents ship with the package
2. **Root-Level Locals**: User agents in project root `agents/` folder
3. **Human-Readable**: YAML config files are easy to edit
4. **Secure**: Sensitive data via env vars, excluded from git
5. **Validated**: YAML syntax and schema validation on load
6. **Prefixed Serials**: Clear distinction between `#N` and `@N`
