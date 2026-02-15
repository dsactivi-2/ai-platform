# Agent Specification

## Overview

An **Agent** is the core entity in Lyzr Kit. It represents an AI-powered assistant that can process prompts, use tools, and generate responses.

## Categories

| Category | Description | Examples |
|----------|-------------|----------|
| `chat` | Conversational agent with multi-turn context | Interactive assistants, customer support bots |
| `qa` | Single-turn question-answering agent | Document Q&A, knowledge base queries |

## Built-in Agents

| Serial | ID | Category | Sub-agents |
|--------|-----|----------|------------|
| #1 | `chat-agent` | chat | - |
| #2 | `qa-agent` | qa | - |
| #3 | `code-reviewer` | qa | - |
| #4 | `content-writer` | chat | - |
| #5 | `customer-support` | chat | - |
| #6 | `data-analyst` | qa | - |
| #7 | `email-composer` | chat | - |
| #8 | `research-assistant` | chat | - |
| #9 | `sql-expert` | qa | - |
| #10 | `summarizer` | qa | - |
| #11 | `task-planner` | chat | - |
| #12 | `translator` | qa | - |
| #13 | `project-manager` | chat | task-planner, data-analyst, summarizer |
| #14 | `dev-lead` | chat | code-reviewer, research-assistant |
| #15 | `tech-director` | chat | dev-lead, project-manager |

## Schema

### YAML Definition

```yaml
# agents/<agent-id>.yaml

# ============ META ============
id: "my-agent"                    # Unique identifier (kebab-case)
serial: 1                         # Serial number (auto-assigned for local)
name: "My Assistant"              # Display name
description: "A helpful AI assistant"
category: "chat"                  # chat | qa

owner: "user-123"                 # Owner ID
share: "private"                  # private | org | public
tags: ["assistant", "general"]    # Searchable tags

created_at: "2024-01-01T00:00:00Z"
updated_at: "2024-01-01T00:00:00Z"

is_active: true                   # Set by 'lk agent get'
endpoint: "https://agent.api.lyzr.app/v3/agent/abc123"  # Populated by 'get'
platform_agent_id: "abc123"       # Platform agent ID
platform_env_id: "env456"         # Platform environment ID
marketplace_app_id: "app789"      # Marketplace app ID (optional)

# ============ MODEL ============
model:
  provider: "openai"              # Provider via Lyzr platform
  name: "gpt-4"                   # Model name
  credential_id: "lyzr_openai"    # Credential ID
  temperature: 0.7                # 0.0-2.0 (default: 0.7)
  top_p: 0.9                      # 0.0-1.0 (default: 0.9)
  max_tokens: 4096                # Max response tokens

# ============ CONFIG ============
config:
  role: "assistant"               # Agent's role
  goal: "Help users with their questions"
  instructions: |                 # System instructions
    You are a helpful assistant.
    Always be concise and accurate.

# ============ VARS ============
vars:
  - "CUSTOM_VAR"                  # Loaded from .env
  - "SECRET_KEY"                  # Loaded from .env

# ============ TOOLS ============
tools:
  - "file_reader"
  - "calculator"

# ============ SUB-AGENTS ============
sub_agents:
  - "research-agent"
  - "summarizer-agent"

# ============ FEATURES ============
features:
  - "memory"
  - "pii_detector"
```

### Minimal Valid

```yaml
id: "my-agent"
name: "My Agent"
category: "chat"
model:
  provider: "openai"
  name: "gpt-4"
  credential_id: "lyzr_openai"
```

### Field Reference

#### Meta Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | string | Yes | - | Unique identifier (3-50 chars, kebab-case) |
| `serial` | int | No | auto | Serial number (auto-assigned for local agents) |
| `name` | string | Yes | - | Display name (1-100 chars) |
| `description` | string | No | `""` | Agent description (max 1000 chars) |
| `category` | enum | Yes | - | Agent category: chat, qa |
| `owner` | string | No | `null` | Owner user/org ID |
| `share` | enum | No | `"private"` | Sharing level: private, org, public |
| `tags` | string[] | No | `[]` | Searchable tags |
| `created_at` | datetime | No | `null` | Creation timestamp |
| `updated_at` | datetime | No | `null` | Last update timestamp |
| `is_active` | bool | No | `false` | Set to true by `lk agent get` |
| `endpoint` | string | No | `null` | Inference URL (populated by `get`) |
| `platform_agent_id` | string | No | `null` | Platform agent ID |
| `platform_env_id` | string | No | `null` | Platform environment ID |
| `marketplace_app_id` | string | No | `null` | Marketplace app ID |

#### Model Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `model.provider` | string | Yes | - | LLM provider ID |
| `model.name` | string | Yes | - | Model name |
| `model.credential_id` | string | Yes | - | Credential ID |
| `model.temperature` | float | No | `0.7` | Sampling temperature (0.0-2.0) |
| `model.top_p` | float | No | `0.9` | Nucleus sampling (0.0-1.0) |
| `model.max_tokens` | int | No | `4096` | Max response tokens |

#### Config Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `config.role` | string | No | `"assistant"` | Agent's role identity |
| `config.goal` | string | No | `""` | Agent's primary goal |
| `config.instructions` | string | No | `""` | System instructions/prompt |

#### References

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `vars` | string[] | No | `[]` | Variable names to load from .env |
| `tools` | string[] | No | `[]` | Tool IDs (validated against registry) |
| `sub_agents` | string[] | No | `[]` | Agent IDs for delegation (must be acyclic) |
| `features` | string[] | No | `[]` | Feature IDs |

## Operations

| Operation | Description | CLI Command |
|-----------|-------------|-------------|
| **ls** | List all agents with prefixed serials | `lk agent ls` |
| **get** | Clone and deploy agent (creates `copy-of-<name>`) | `lk agent get #1` |
| **set** | Update agent on platform | `lk agent set @1` |
| **chat** | Interactive chat session | `lk agent chat @1` |
| **rm** | Delete local agent | `lk agent rm @1` |
| **tree** | Show agent dependency tree | `lk agent tree @1` |
| **doctor** | Validate all local agents | `lk agent doctor` |

## Serial Numbers

| Type | Format | Example |
|------|--------|---------|
| Built-in | `#N` | `#1`, `#2`, `#3` |
| Local | `@N` | `@1`, `@2`, `@3` |

Serial numbers provide quick reference in CLI commands:
- `lk agent get #1` - Clone built-in agent #1
- `lk agent chat @1` - Chat with local agent @1

## Design Principles

1. **ID References**: Tools, features, and sub-agents are referenced by ID
2. **Endpoint-Based**: Agents execute via inference endpoints
3. **Env-Based Vars**: All variables loaded from .env file
4. **Platform-First**: Agents activated on Lyzr platform via `get`
5. **Prefixed Serials**: `#N` for built-in, `@N` for local agents
