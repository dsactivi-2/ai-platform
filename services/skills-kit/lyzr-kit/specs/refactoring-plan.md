# Codebase Refactoring Plan

## Executive Summary

This plan addresses three key concerns:
1. **Large files** - Some files exceed 500 lines with multiple responsibilities
2. **Test organization** - Test files mirror source but are monolithic
3. **OOP utilization** - Opportunities for better encapsulation and design patterns

**Current State:**
- Source: 3,575 lines across 30 files
- Tests: 3,285 lines across 14 files
- Largest source file: `agent_chat.py` (560 lines)
- Largest test file: `test_agent.py` (1,117 lines)

---

## Part 1: Source Code Decomposition

### 1.1 agent_chat.py (560 lines → 4 files)

**Problem:** This file handles UI rendering, SSE streaming, WebSocket events, keyboard bindings, and state management all in one place.

**Current Structure:**
```
agent_chat.py
├── StreamState (dataclass)           # State management
├── _format_timestamp()               # Utility
├── _build_session_box()              # UI rendering
├── _build_user_box()                 # UI rendering
├── _decode_sse_data()                # Streaming
├── _separate_thinking_content()      # Streaming
├── _build_agent_box()                # UI rendering
├── _stream_chat_message()            # Core streaming + WS + threading
└── chat_with_agent()                 # Main entry + prompt_toolkit setup
```

**Proposed Structure:**
```
commands/
├── agent_chat.py              # Main entry point only (~80 lines)
├── _chat/
│   ├── __init__.py            # Exports
│   ├── state.py               # StreamState dataclass (~50 lines)
│   ├── ui.py                  # UI box builders (~120 lines)
│   ├── streaming.py           # SSE streaming logic (~150 lines)
│   └── keybindings.py         # prompt_toolkit bindings (~60 lines)
```

**Refactored Classes:**

```python
# state.py
@dataclass
class StreamState:
    """Immutable state container for streaming chat."""
    content: str = ""
    events: list[ChatEvent] = field(default_factory=list)
    # ... existing fields

# ui.py
class ChatUIBuilder:
    """Builds Rich UI components for chat display."""

    @staticmethod
    def session_box(agent: Agent, session_id: str, start_time: str) -> Panel:
        ...

    @staticmethod
    def user_box(message: str, timestamp: str) -> Panel:
        ...

    @staticmethod
    def agent_box(state: StreamState, timestamp: str) -> Panel:
        ...

# streaming.py
class ChatStreamer:
    """Handles SSE streaming with WebSocket event integration."""

    def __init__(self, auth: AuthConfig, agent: Agent, session_id: str):
        self.auth = auth
        self.agent = agent
        self.session_id = session_id
        self._state = StreamState()

    def stream_message(self, message: str) -> StreamState:
        """Stream a message and return final state."""
        ...

    def _connect_websocket(self) -> None:
        """Start WebSocket in background thread."""
        ...
```

**Benefits:**
- Single responsibility per file
- Testable in isolation
- Easier to extend (add new UI styles, streaming protocols)

---

### 1.2 validator.py (342 lines → 4 files)

**Problem:** Mixes folder validation, YAML parsing, schema validation, cycle detection, and error formatting.

**Current Structure:**
```
validator.py
├── ValidationIssue (dataclass)
├── ValidationResult (dataclass)
├── validate_agents_folder()          # Folder structure
├── _validate_agent_yaml()            # YAML + Schema
├── validate_agent_yaml_file()        # YAML + Schema
├── format_schema_errors()            # Formatting
├── format_validation_errors()        # Formatting
├── validate_sub_agents()             # Sub-agent validation
├── detect_cycle()                    # Graph algorithm
├── format_subagent_errors()          # Formatting
└── format_cycle_error()              # Formatting
```

**Proposed Structure:**
```
storage/
├── validator.py               # Public API + orchestrator (~60 lines)
├── _validation/
│   ├── __init__.py            # Exports
│   ├── models.py              # ValidationIssue, ValidationResult (~40 lines)
│   ├── folder.py              # FolderValidator class (~80 lines)
│   ├── yaml_validator.py      # YamlValidator class (~80 lines)
│   ├── cycle.py               # CycleDetector class (~60 lines)
│   └── formatters.py          # ErrorFormatter class (~80 lines)
```

**Refactored Classes with OOP Patterns:**

```python
# models.py
from abc import ABC, abstractmethod

@dataclass
class ValidationIssue:
    issue_type: str
    path: Path
    message: str
    hint: str

@dataclass
class ValidationResult:
    is_valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)

# Base validator protocol
class Validator(Protocol):
    """Protocol for all validators."""
    def validate(self) -> ValidationResult: ...

# folder.py
class FolderValidator:
    """Validates agents folder structure (flat, no nested dirs)."""

    def __init__(self, agents_dir: Path):
        self.agents_dir = agents_dir

    def validate(self) -> ValidationResult:
        """Check for nested folders and invalid extensions."""
        ...

    def _check_nested_folders(self) -> list[ValidationIssue]:
        ...

    def _check_file_extensions(self) -> list[ValidationIssue]:
        ...

# yaml_validator.py
class YamlValidator:
    """Validates YAML files against Agent schema."""

    def __init__(self, yaml_path: Path):
        self.yaml_path = yaml_path

    def validate(self) -> tuple[Agent | None, ValidationError | None, str | None]:
        """Parse and validate YAML against Agent schema."""
        ...

# cycle.py
class CycleDetector:
    """Detects circular dependencies in sub-agent graph using DFS."""

    def __init__(self, storage: StorageManager):
        self.storage = storage

    def detect(self, agent_id: str, sub_agents: list[str]) -> list[str] | None:
        """Returns cycle path if found, None if acyclic."""
        ...

    def _dfs(self, current: str, visiting: set, path: list) -> list[str] | None:
        ...

# formatters.py
class ErrorFormatter:
    """Formats validation errors for Rich console display."""

    @staticmethod
    def format_schema_errors(error: ValidationError, agent_id: str) -> str:
        ...

    @staticmethod
    def format_folder_errors(result: ValidationResult) -> str:
        ...

    @staticmethod
    def format_cycle_error(cycle_path: list[str]) -> str:
        ...
```

**Benefits:**
- Each validator is independently testable
- Easy to add new validation types
- Clear separation of validation logic from formatting

---

### 1.3 manager.py (283 lines → 3 files)

**Problem:** StorageManager handles file I/O, agent operations, and path management.

**Proposed Structure:**
```
storage/
├── manager.py                 # StorageManager facade (~100 lines)
├── _storage/
│   ├── __init__.py
│   ├── file_io.py             # YamlFileHandler class (~80 lines)
│   └── repository.py          # AgentRepository class (~100 lines)
```

**Refactored Classes:**

```python
# file_io.py
class YamlFileHandler:
    """Low-level YAML file operations."""

    def __init__(self, base_path: Path):
        self.base_path = base_path

    def read(self, filename: str) -> dict:
        ...

    def write(self, filename: str, data: dict) -> None:
        ...

    def delete(self, filename: str) -> bool:
        ...

    def exists(self, filename: str) -> bool:
        ...

    def list_files(self, pattern: str = "*.yaml") -> list[Path]:
        ...

# repository.py
class AgentRepository:
    """Agent-specific storage operations."""

    def __init__(self, file_handler: YamlFileHandler):
        self.file_handler = file_handler

    def get(self, agent_id: str) -> Agent | None:
        ...

    def save(self, agent: Agent) -> None:
        ...

    def delete(self, agent_id: str) -> bool:
        ...

    def list_all(self) -> list[Agent]:
        ...

    def exists(self, agent_id: str) -> bool:
        ...

# manager.py (facade)
class StorageManager:
    """High-level storage facade combining all storage operations."""

    def __init__(self, local_path: Path | None = None):
        self.local_path = local_path or Path.cwd()
        self._file_handler = YamlFileHandler(self.local_path / "agents")
        self._agent_repo = AgentRepository(self._file_handler)

    # Delegate to repository
    def get_agent(self, agent_id: str) -> Agent | None:
        return self._agent_repo.get(agent_id)

    # ... other methods delegate to appropriate handler
```

**Benefits:**
- Repository pattern for data access
- File I/O isolated for easy mocking
- Facade pattern maintains backward compatibility

---

## Part 2: Test File Decomposition

### 2.1 test_agent.py (1,117 lines → 6 files)

**Current Test Classes:**
```
TestAgentLs              (~130 lines) → test_agent_ls.py
TestAgentHelp            (~30 lines)  → test_agent_help.py
TestAgentGetSerialNumbers (~60 lines)  → test_agent_get.py
TestAgentSetSerialNumbers (~30 lines)  → test_agent_set.py
TestAgentChatSerialNumbers (~40 lines) → test_agent_chat.py
TestAgentGetErrors       (~100 lines) → test_agent_get.py
TestAgentSetErrors       (~200 lines) → test_agent_set.py
TestAgentChat            (~120 lines) → test_agent_chat.py
TestStreamingHelpers     (~90 lines)  → test_chat_streaming.py
TestWebSocketHelpers     (~100 lines) → test_chat_websocket.py
TestChatUIBoxes          (~150 lines) → test_chat_ui.py
```

**Proposed Structure:**
```
tests/unit/commands/
├── test_agent_ls.py           # List command tests
├── test_agent_get.py          # Get command tests
├── test_agent_set.py          # Set command tests
├── test_agent_rm.py           # Remove command tests (already exists)
├── test_agent_chat.py         # Chat command tests
├── test_agent_tree.py         # Tree command tests
├── test_agent_doctor.py       # Doctor command tests
├── _chat/
│   ├── test_streaming.py      # SSE streaming tests
│   ├── test_websocket.py      # WebSocket event tests
│   └── test_ui.py             # UI component tests
```

**Benefits:**
- Each command has its own test file
- Easier to find and maintain tests
- Parallel test execution potential

---

### 2.2 test_validator.py (590 lines → 4 files)

**Proposed Structure:**
```
tests/unit/storage/
├── test_validator.py          # Integration tests (~50 lines)
├── _validation/
│   ├── test_folder.py         # FolderValidator tests
│   ├── test_yaml.py           # YamlValidator tests
│   ├── test_cycle.py          # CycleDetector tests
│   └── test_formatters.py     # ErrorFormatter tests
```

---

### 2.3 test_subagents.py (573 lines → 3 files)

**Proposed Structure:**
```
tests/unit/commands/
├── _subagents/
│   ├── test_clone_plan.py     # Plan building tests
│   ├── test_recursive_ops.py  # Recursive delete, tree tests
│   └── test_copy_id.py        # ID generation tests
```

---

## Part 3: OOP Improvements

### 3.1 Design Patterns to Apply

| Pattern | Where | Benefit |
|---------|-------|---------|
| **Strategy** | Validators | Swap validation strategies |
| **Builder** | Rich UI panels | Fluent API for complex panels |
| **Repository** | Agent storage | Data access abstraction |
| **Facade** | StorageManager | Simplified API |
| **Observer** | WebSocket events | Event subscription model |
| **State** | StreamState | Cleaner state transitions |

### 3.2 Protocol-Based Design

```python
# protocols.py
from typing import Protocol

class AgentStorage(Protocol):
    """Protocol for agent storage implementations."""
    def get(self, agent_id: str) -> Agent | None: ...
    def save(self, agent: Agent) -> None: ...
    def delete(self, agent_id: str) -> bool: ...
    def list_all(self) -> list[Agent]: ...
    def exists(self, agent_id: str) -> bool: ...

class Validator(Protocol):
    """Protocol for validation implementations."""
    def validate(self) -> ValidationResult: ...

class UIBuilder(Protocol):
    """Protocol for UI component builders."""
    def build(self) -> Panel: ...
```

**Benefits:**
- Enables dependency injection
- Easier mocking in tests
- Supports multiple implementations (e.g., JSON storage, DB storage)

### 3.3 Dataclass Improvements

```python
# Use frozen dataclasses for immutability where appropriate
@dataclass(frozen=True)
class ChatEvent:
    event_type: str
    timestamp: datetime
    function_name: str | None = None
    response: str | None = None
    arguments: dict | None = None

# Use slots for memory efficiency
@dataclass(slots=True)
class ValidationIssue:
    issue_type: str
    path: Path
    message: str
    hint: str
```

---

## Part 4: Implementation Priority

### Phase 1: High Impact, Low Risk (Week 1)

| Task | Files Affected | Lines Reduced |
|------|----------------|---------------|
| Split test_agent.py | 1 → 6 files | Better organization |
| Extract _chat/ module | agent_chat.py | 560 → ~80 lines |
| Extract _validation/ module | validator.py | 342 → ~60 lines |

### Phase 2: Moderate Impact (Week 2)

| Task | Files Affected | Lines Reduced |
|------|----------------|---------------|
| Split test_validator.py | 1 → 4 files | Better organization |
| Split test_subagents.py | 1 → 3 files | Better organization |
| Add Protocol definitions | New file | Better typing |

### Phase 3: Architecture Improvements (Week 3)

| Task | Files Affected | Benefit |
|------|----------------|---------|
| Extract storage/_storage/ | manager.py | Repository pattern |
| Add Builder for UI | _chat/ui.py | Fluent API |
| Add Observer for WS events | _websocket.py | Event system |

---

## Part 5: Migration Strategy

### 5.1 Backward Compatibility

All refactoring maintains backward compatibility:

```python
# Old import still works
from lyzr_kit.storage import validate_agents_folder

# Implementation delegates to new structure
def validate_agents_folder(local_path: Path) -> ValidationResult:
    from lyzr_kit.storage._validation.folder import FolderValidator
    return FolderValidator(local_path / "agents").validate()
```

### 5.2 Test Migration

1. Create new test files with skeleton
2. Move test classes one at a time
3. Run tests after each move
4. Delete old file when empty

### 5.3 Verification

After each phase:
```bash
pytest tests/ -v              # All tests pass
ruff check src/               # No lint errors
mypy src/                     # No type errors
```

---

## Summary

| Metric | Current | After Refactoring |
|--------|---------|-------------------|
| Largest source file | 560 lines | ~150 lines |
| Largest test file | 1,117 lines | ~200 lines |
| Files with 300+ lines | 4 | 0 |
| Test files | 14 | ~25 |
| Source files | 30 | ~40 |
| Design patterns used | 1 (Dataclass) | 5+ |

**Key Outcomes:**
1. No file exceeds 200 lines
2. Single responsibility per file
3. OOP patterns for extensibility
4. Tests organized by feature
5. Full backward compatibility
