# Schema Specification

## Overview

The SDK manages schema evolution without requiring version fields in YAML files. The SDK is the **source of truth** for schemas - it detects legacy patterns structurally and handles migrations automatically.

## Design Principles

| Principle | Description |
|-----------|-------------|
| SDK is Source of Truth | Schema definitions live in code (Pydantic models) |
| Structural Detection | Legacy patterns detected by structure, not version numbers |
| In-Memory Migration | Old files work immediately, migrated on load |
| Explicit File Updates | Files only change via `upgrade` command |
| No Version Fields | YAML files are clean |

## How It Works

```
YAML File → Pattern Detection → In-Memory Migration → Pydantic Validation → Runtime Model
```

1. Load raw YAML data
2. Check for known legacy patterns
3. Transform data in-memory if patterns found
4. Validate against current Pydantic model
5. Return validated instance

## Legacy Patterns

Legacy patterns define how to detect and transform old schema formats:

```python
@dataclass
class LegacyPattern:
    name: str                              # Pattern identifier
    description: str                       # Human-readable description
    detect: Callable[[dict], bool]         # Returns True if pattern found
    transform: Callable[[dict], dict]      # Transforms to current format
```

## Automatic Migration

When the SDK is upgraded (`pip install --upgrade lyzr-kit`):
1. Old YAML files load without errors
2. Legacy patterns detected and migrated in-memory
3. No user action required

Files on disk remain unchanged until explicitly saved via `lk set`.
