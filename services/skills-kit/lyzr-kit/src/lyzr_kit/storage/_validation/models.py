"""Data models for validation results."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ValidationIssue:
    """Represents a validation issue found during folder/file validation."""

    issue_type: str  # "nested_folder", "invalid_extension", "invalid_yaml", "invalid_schema"
    path: Path
    message: str
    hint: str


@dataclass
class ValidationResult:
    """Result of validating a resource folder."""

    is_valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)

    # Categorized issues for easy access
    nested_folders: list[Path] = field(default_factory=list)
    invalid_extensions: list[Path] = field(default_factory=list)
    invalid_yaml_files: list[Path] = field(default_factory=list)
    invalid_schema_files: list[Path] = field(default_factory=list)
