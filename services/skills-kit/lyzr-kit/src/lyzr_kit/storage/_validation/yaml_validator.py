"""YAML file validation against Agent schema."""

from pathlib import Path

import yaml
from pydantic import ValidationError

from lyzr_kit.schemas.agent import Agent
from lyzr_kit.storage._validation.models import ValidationIssue


def validate_agent_yaml(yaml_file: Path) -> ValidationIssue | None:
    """Validate a single YAML file against the Agent schema.

    Args:
        yaml_file: Path to the YAML file.

    Returns:
        ValidationIssue if invalid, None if valid.
    """
    try:
        with open(yaml_file) as f:
            data = yaml.safe_load(f)

        if data is None:
            return ValidationIssue(
                issue_type="invalid_yaml",
                path=yaml_file,
                message=f"Empty YAML file: {yaml_file.name}",
                hint=f"Delete '{yaml_file.name}' or add valid agent configuration",
            )

        Agent.model_validate(data)
        return None

    except yaml.YAMLError as e:
        return ValidationIssue(
            issue_type="invalid_yaml",
            path=yaml_file,
            message=f"Invalid YAML syntax in {yaml_file.name}: {e}",
            hint=f"Fix YAML syntax in '{yaml_file.name}' or delete and re-clone",
        )

    except ValidationError as e:
        error_fields = [err["loc"][0] for err in e.errors() if err.get("loc")]
        error_summary = ", ".join(str(f) for f in error_fields[:3])
        if len(error_fields) > 3:
            error_summary += f" (+{len(error_fields) - 3} more)"

        return ValidationIssue(
            issue_type="invalid_schema",
            path=yaml_file,
            message=f"Schema validation failed for {yaml_file.name}: {error_summary}",
            hint=f"Delete '{yaml_file.name}' and re-clone with 'lk agent get'",
        )


def validate_agent_yaml_file(
    yaml_path: Path,
) -> tuple[Agent | None, ValidationError | None, str | None]:
    """Validate an agent YAML file and return the agent or errors.

    Returns:
        Tuple of (agent, validation_error, yaml_error_message).
        - If valid: (Agent, None, None)
        - If schema invalid: (None, ValidationError, None)
        - If YAML invalid: (None, None, error_message)
    """
    try:
        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        if data is None:
            return None, None, f"Empty YAML file: {yaml_path.name}"

        agent = Agent.model_validate(data)
        return agent, None, None

    except yaml.YAMLError as e:
        return None, None, f"Invalid YAML syntax: {e}"

    except ValidationError as e:
        return None, e, None
