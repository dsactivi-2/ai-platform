"""Folder structure validation for agents directory."""

from pathlib import Path

from lyzr_kit.storage._validation.models import ValidationIssue, ValidationResult
from lyzr_kit.storage._validation.yaml_validator import validate_agent_yaml


class FolderValidator:
    """Validates agents folder structure (flat, no nested dirs)."""

    def __init__(self, agents_dir: Path):
        """Initialize the folder validator.

        Args:
            agents_dir: Path to the agents directory.
        """
        self.agents_dir = agents_dir

    def validate(self) -> ValidationResult:
        """Validate the agents folder structure and files.

        Performs three checks:
        1. Folder structure - no nested folders allowed (flat structure only)
        2. File extensions - only .yaml files allowed
        3. Schema validation - all YAML files must follow the Agent schema

        Returns:
            ValidationResult with all issues found.
        """
        result = ValidationResult(is_valid=True)

        # If agents folder doesn't exist or isn't a directory, nothing to validate
        if not self.agents_dir.exists() or not self.agents_dir.is_dir():
            return result

        try:
            # Check 1: Detect nested folders
            self._check_nested_folders(result)

            # Check 2: Detect non-YAML files
            self._check_file_extensions(result)

            # Check 3: Validate YAML files against Agent schema
            self._check_yaml_schemas(result)

        except OSError:
            # Handle filesystem errors gracefully
            return result

        result.is_valid = len(result.issues) == 0
        return result

    def _check_nested_folders(self, result: ValidationResult) -> None:
        """Check for nested folders (flat structure required)."""
        for item in self.agents_dir.iterdir():
            if item.is_dir():
                issue = ValidationIssue(
                    issue_type="nested_folder",
                    path=item,
                    message=f"Nested folder detected: {item.name}/",
                    hint=f"Remove or move the folder '{item.name}' outside of agents/",
                )
                result.issues.append(issue)
                result.nested_folders.append(item)

    def _check_file_extensions(self, result: ValidationResult) -> None:
        """Check for non-YAML files."""
        for item in self.agents_dir.iterdir():
            if item.is_file() and not item.name.endswith(".yaml"):
                issue = ValidationIssue(
                    issue_type="invalid_extension",
                    path=item,
                    message=f"Invalid file extension: {item.name}",
                    hint=f"Remove '{item.name}' - only .yaml files are allowed in agents/",
                )
                result.issues.append(issue)
                result.invalid_extensions.append(item)

    def _check_yaml_schemas(self, result: ValidationResult) -> None:
        """Validate YAML files against Agent schema."""
        for yaml_file in self.agents_dir.glob("*.yaml"):
            validation_issue = validate_agent_yaml(yaml_file)
            if validation_issue:
                result.issues.append(validation_issue)
                if validation_issue.issue_type == "invalid_yaml":
                    result.invalid_yaml_files.append(yaml_file)
                elif validation_issue.issue_type == "invalid_schema":
                    result.invalid_schema_files.append(yaml_file)


def validate_agents_folder(local_path: Path) -> ValidationResult:
    """Validate the agents folder structure and files.

    Args:
        local_path: Path to the project directory.

    Returns:
        ValidationResult with all issues found.
    """
    validator = FolderValidator(local_path / "agents")
    return validator.validate()
