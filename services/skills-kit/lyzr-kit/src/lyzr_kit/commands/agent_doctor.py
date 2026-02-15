"""Agent doctor command implementation - validate all local agents."""

from dataclasses import dataclass, field

import typer
from rich.table import Table

from lyzr_kit.commands._console import console
from lyzr_kit.storage import (
    StorageManager,
    detect_cycle,
    validate_agents_folder,
    validate_sub_agents,
)


@dataclass
class AgentIssue:
    """An issue found during agent validation."""

    agent_id: str
    issue_type: str  # "missing_sub_agent", "circular_dependency", "not_active", "no_platform_id"
    message: str
    fix_hint: str


@dataclass
class DoctorReport:
    """Report from running doctor validation."""

    folder_issues: list[str] = field(default_factory=list)
    agent_issues: list[AgentIssue] = field(default_factory=list)
    healthy_count: int = 0
    total_count: int = 0

    @property
    def is_healthy(self) -> bool:
        return len(self.folder_issues) == 0 and len(self.agent_issues) == 0


def _run_doctor(storage: StorageManager) -> DoctorReport:
    """Run comprehensive validation on all local agents.

    Args:
        storage: StorageManager instance.

    Returns:
        DoctorReport with all issues found.
    """
    report = DoctorReport()

    # 1. Validate folder structure
    folder_result = validate_agents_folder(storage.local_path)
    if not folder_result.is_valid:
        for issue in folder_result.issues:
            report.folder_issues.append(f"{issue.message}")

    # 2. Validate each agent
    local_agents = storage.list_local_agents()
    report.total_count = len(local_agents)

    for agent in local_agents:
        agent_healthy = True

        # Check sub-agents exist
        if agent.sub_agents:
            missing = validate_sub_agents(agent.sub_agents, storage)
            if missing:
                agent_healthy = False
                for sub_id in missing:
                    report.agent_issues.append(
                        AgentIssue(
                            agent_id=agent.id,
                            issue_type="missing_sub_agent",
                            message=f"Sub-agent '{sub_id}' not found",
                            fix_hint=f"Run 'lk agent get {sub_id}' or remove from sub_agents",
                        )
                    )

            # Check for cycles
            cycle = detect_cycle(agent.id, agent.sub_agents, storage)
            if cycle:
                agent_healthy = False
                cycle_path = " → ".join(cycle)
                report.agent_issues.append(
                    AgentIssue(
                        agent_id=agent.id,
                        issue_type="circular_dependency",
                        message=f"Circular dependency: {cycle_path}",
                        fix_hint="Remove one of the references in sub_agents",
                    )
                )

        # Check platform deployment
        if not agent.platform_agent_id:
            agent_healthy = False
            report.agent_issues.append(
                AgentIssue(
                    agent_id=agent.id,
                    issue_type="no_platform_id",
                    message="Not deployed to platform",
                    fix_hint=f"Run 'lk agent set {agent.id}' to deploy",
                )
            )

        # Check active status
        if not agent.is_active:
            agent_healthy = False
            report.agent_issues.append(
                AgentIssue(
                    agent_id=agent.id,
                    issue_type="not_active",
                    message="Agent is not active",
                    fix_hint=f"Run 'lk agent set {agent.id}' to activate",
                )
            )

        if agent_healthy:
            report.healthy_count += 1

    return report


def doctor_agents() -> None:
    """Validate all local agents and report issues."""
    storage = StorageManager()

    console.print("\n[bold]Running agent doctor...[/bold]\n")

    report = _run_doctor(storage)

    # Display folder issues
    if report.folder_issues:
        console.print("[red]Folder structure issues:[/red]")
        for folder_issue in report.folder_issues:
            console.print(f"  • {folder_issue}")
        console.print()

    # Display agent issues
    if report.agent_issues:
        table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
        table.add_column("AGENT", style="cyan")
        table.add_column("ISSUE", style="yellow")
        table.add_column("FIX", style="dim")

        for issue in report.agent_issues:
            table.add_row(issue.agent_id, issue.message, issue.fix_hint)

        console.print(table)
        console.print()

    # Summary
    if report.is_healthy:
        if report.total_count == 0:
            console.print("[dim]No local agents found.[/dim]")
        else:
            console.print(f"[green]✓ All {report.total_count} agent(s) are healthy![/green]")
    else:
        issue_count = len(report.folder_issues) + len(report.agent_issues)
        console.print(
            f"[red]Found {issue_count} issue(s)[/red] "
            f"({report.healthy_count}/{report.total_count} agents healthy)"
        )
        raise typer.Exit(1)
