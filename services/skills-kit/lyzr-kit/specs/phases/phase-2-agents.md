# Phase 2: Schema Evolution

## Overview

Phase 2 implements schema versioning and migration system for handling backward compatibility when schemas change.

## Goals

- Implement structural pattern detection for legacy schemas
- Build in-memory migration system
- Add CLI upgrade command
- Ensure zero-friction upgrades

## Deliverables

### 1. Legacy Pattern Definition

```python
@dataclass
class LegacyPattern:
    name: str                              # Pattern identifier
    description: str                       # Human-readable description
    detect: Callable[[dict], bool]         # Returns True if pattern found
    transform: Callable[[dict], dict]      # Transforms to current format
```

### 2. Schema Loader

```python
class SchemaLoader:
    def __init__(self, model: type[T], legacy_patterns: list[LegacyPattern]):
        self.model = model
        self.legacy_patterns = legacy_patterns

    def load(self, path: Path) -> T:
        """Load YAML, detect patterns, migrate in-memory, validate."""
        raw = yaml.safe_load(path.read_text())

        for pattern in self.legacy_patterns:
            if pattern.detect(raw):
                raw = pattern.transform(raw)

        return self.model.model_validate(raw)

    def needs_upgrade(self, path: Path) -> bool:
        """Check if file has legacy patterns."""
        ...

    def upgrade(self, path: Path) -> list[str]:
        """Upgrade file to current schema, return migrated patterns."""
        ...
```

### 3. Example Patterns

```python
AGENT_LEGACY_PATTERNS = [
    LegacyPattern(
        name="llm_to_model",
        description="'llm' section renamed to 'model'",
        detect=lambda d: "llm" in d and "model" not in d,
        transform=lambda d: _rename_field(d, "llm", "model"),
    ),
    LegacyPattern(
        name="type_to_category",
        description="'type' field renamed to 'category'",
        detect=lambda d: "type" in d and "category" not in d,
        transform=lambda d: _rename_field(d, "type", "category"),
    ),
]
```

## Design Principles

1. **SDK is Source of Truth**: Schema definitions live in code
2. **Structural Detection**: Patterns detected by structure, not version numbers
3. **In-Memory Migration**: Old files work immediately on SDK upgrade
4. **No Version Fields**: YAML files are clean

## Success Criteria

- Old YAML files load without errors after SDK upgrade
- In-memory migration is transparent to users
- Adding new patterns is straightforward

## Dependencies

Requires Phase 1 completion
