# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2024-12-16

### Added
- **Sub-agent orchestration** - Agents can delegate tasks via `sub_agents` array
- **Plan-based cloning** - `lk get` shows dependency plan with single confirmation
- **Default ID generation** - Uses `copy-of-<name>` format (e.g., `copy-of-chat-agent`)
- **Circular dependency detection** - Validates sub-agent relationships are acyclic
- **Tree command** (`lk tree`) - Visualize agent dependency hierarchies
- **Doctor command** (`lk doctor`) - Validate all local agents (missing subs, cycles, deployment)
- **Recursive delete** (`lk rm --tree`) - Delete agent and all sub-agents
- **Force delete** (`lk rm --force`) - Remove from parent agents and delete
- Built-in agents with sub-agents: project-manager, dev-lead, tech-director

### Changed
- `lk get` no longer prompts for agent ID - uses `copy-of-<name>` by default
- Rename agents by editing YAML `id` field and running `lk set`

### Internal
- **Codebase refactoring** - Decomposed large files into focused modules
- Split `agent_chat.py` (560→132 lines) into `_chat/` module (state, ui, streaming, keybindings)
- Split `validator.py` (342→46 lines) into `_validation/` module (models, folder, yaml, cycle, formatters)
- Organized test files by command (test_agent_ls.py, test_agent_get.py, etc.)
- Improved OOP patterns with dataclasses and dedicated validator classes

## [0.2.2] - 2024-12-08

### Changed
- Improved CLI help messages (succinct and clear)

## [0.2.1] - 2024-12-08

### Added
- **Default agent resource** - `agent` is now optional (`lk ls` = `lk agent ls`)

## [0.2.0] - 2024-12-08

### Added
- **Chat command** (`lk chat`) with full interactive experience
- **Session box** - Displays agent name, model, session ID, timestamp
- **Real-time WebSocket events** - Tool calls, memory updates, artifacts inline
- **SSE streaming** - Live markdown-rendered responses
- **Metrics footer** - Latency and token usage per response
- **Keyboard shortcuts** - Full readline support (Option/Ctrl + arrows, history)
- Built-in agents expanded: code-reviewer, content-writer, customer-support, data-analyst, email-composer, research-assistant, sql-expert, summarizer, task-planner, translator

### Technical
- `websockets>=12.0` dependency for WebSocket event streaming
- `prompt_toolkit>=3.0` dependency for readline input
- Daemon thread for graceful WebSocket shutdown
- Context-aware serial number resolution

## [0.1.0] - 2024-12-02

### Added
- Initial release of lyzr-kit SDK
- CLI tool (`lk`) for managing agents
- Commands: `lk agent ls`, `lk agent get`, `lk agent set`
- Auth command: `lk auth`
- Built-in agents: `chat-agent`, `qa-agent`
- Pydantic schemas, StorageManager, YAML configs

### Technical
- Python 3.10+
- Typer + Rich CLI
- uv package manager support

[Unreleased]: https://github.com/LyzrCore/lyzr-kit/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/LyzrCore/lyzr-kit/compare/v0.2.2...v0.3.0
[0.2.2]: https://github.com/LyzrCore/lyzr-kit/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/LyzrCore/lyzr-kit/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/LyzrCore/lyzr-kit/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/LyzrCore/lyzr-kit/releases/tag/v0.1.0
