"""Error formatters for validation errors."""

from pydantic import ValidationError

from lyzr_kit.storage._validation.models import ValidationResult


class ErrorFormatter:
    """Formats validation errors for Rich console display."""

    @staticmethod
    def format_schema_errors(error: ValidationError, agent_id: str) -> str:
        """Format Pydantic validation errors for detailed user display.

        Args:
            error: The Pydantic ValidationError.
            agent_id: The agent ID being validated.

        Returns:
            Formatted error message string with Rich markup.
        """
        lines = [f"[red]Error: Agent '{agent_id}' has invalid schema.[/red]", ""]

        lines.append("[yellow]Expected fields:[/yellow]")
        lines.append("  - id (required): string, 3-50 chars")
        lines.append("  - name (required): string, 1-100 chars")
        lines.append('  - category (required): "chat" or "qa"')
        lines.append("  - model (required): object with provider, name, credential_id")
        lines.append("")

        lines.append("[yellow]Your file is missing or has invalid:[/yellow]")
        for err in error.errors():
            loc = ".".join(str(x) for x in err["loc"])
            msg = err["msg"]
            err_type = err["type"]

            if err_type == "missing":
                lines.append(f"  - {loc}: field required")
            else:
                lines.append(f"  - {loc}: {msg}")

        lines.append("")
        lines.append(f"[dim]Fix the YAML file and re-run 'lk agent set {agent_id}'[/dim]")

        return "\n".join(lines)

    @staticmethod
    def format_validation_errors(result: ValidationResult) -> str:
        """Format validation errors for display to the user.

        Args:
            result: The ValidationResult containing issues.

        Returns:
            Formatted error message string with Rich markup.
        """
        if result.is_valid:
            return ""

        lines = ["[red]Validation errors found in agents/:[/red]", ""]

        if result.nested_folders:
            lines.append("[yellow]Nested folders (flat structure required):[/yellow]")
            for folder in result.nested_folders:
                lines.append(f"  - {folder.name}/")
            lines.append("[dim]Hint: Remove these folders from agents/[/dim]")
            lines.append("")

        if result.invalid_extensions:
            lines.append("[yellow]Invalid file extensions (only .yaml allowed):[/yellow]")
            for file in result.invalid_extensions:
                lines.append(f"  - {file.name}")
            lines.append("[dim]Hint: Remove these files from agents/[/dim]")
            lines.append("")

        if result.invalid_yaml_files:
            lines.append("[yellow]Invalid YAML syntax:[/yellow]")
            for file in result.invalid_yaml_files:
                lines.append(f"  - {file.name}")
            lines.append("[dim]Hint: Fix syntax or delete and re-clone with 'lk agent get'[/dim]")
            lines.append("")

        if result.invalid_schema_files:
            lines.append("[yellow]Invalid agent schema:[/yellow]")
            for file in result.invalid_schema_files:
                lines.append(f"  - {file.name}")
            lines.append(
                "[dim]Hint: Delete and re-clone with 'lk agent get <source> <new-id>'[/dim]"
            )
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def format_subagent_errors(missing_ids: list[str]) -> str:
        """Format sub-agent validation errors for display.

        Args:
            missing_ids: List of invalid sub-agent IDs.

        Returns:
            Formatted error message string with Rich markup.
        """
        lines = ["[red]Error: Invalid sub-agent IDs[/red]", ""]
        for agent_id in missing_ids:
            lines.append(f"  - '{agent_id}' not found in local agents")
        lines.append("")
        lines.append(
            "[dim]Sub-agents must be local agents. Run 'lk agent ls' to see available agents.[/dim]"
        )
        return "\n".join(lines)

    @staticmethod
    def format_cycle_error(cycle_path: list[str]) -> str:
        """Format cycle detection error for display.

        Args:
            cycle_path: List of agent IDs showing the cycle (e.g., ["A", "B", "C", "A"]).

        Returns:
            Formatted error message string with Rich markup.
        """
        lines = ["[red]Error: Circular sub-agent dependency detected[/red]", ""]
        lines.append(f"  [yellow]{' → '.join(cycle_path)}[/yellow]")
        lines.append("")
        lines.append(
            "[dim]Sub-agent relationships must be acyclic. Remove one of the references.[/dim]"
        )
        return "\n".join(lines)


# Convenience functions that delegate to ErrorFormatter
def format_schema_errors(error: ValidationError, agent_id: str) -> str:
    """Format Pydantic validation errors for detailed user display."""
    return ErrorFormatter.format_schema_errors(error, agent_id)


def format_validation_errors(result: ValidationResult) -> str:
    """Format validation errors for display to the user."""
    return ErrorFormatter.format_validation_errors(result)


def format_subagent_errors(missing_ids: list[str]) -> str:
    """Format sub-agent validation errors for display."""
    return ErrorFormatter.format_subagent_errors(missing_ids)


def format_cycle_error(cycle_path: list[str]) -> str:
    """Format cycle detection error for display."""
    return ErrorFormatter.format_cycle_error(cycle_path)
