"""Agent get command implementation."""

from dataclasses import dataclass

import typer
from rich.status import Status
from rich.table import Table

from lyzr_kit.commands._auth_helper import require_auth
from lyzr_kit.commands._console import console
from lyzr_kit.commands._resolver import resolve_builtin_agent_id
from lyzr_kit.schemas.agent import Agent
from lyzr_kit.storage import StorageManager, get_next_local_serial
from lyzr_kit.utils.auth import AuthConfig
from lyzr_kit.utils.platform import PlatformClient, PlatformError


@dataclass
class ClonePlanItem:
    """A single item in the clone plan."""

    source_id: str  # Built-in agent ID
    target_id: str  # New local agent ID
    action: str  # "create" or "use existing"
    is_main: bool = False  # True for the main agent


def _generate_copy_id(source_id: str, storage: StorageManager) -> str:
    """Generate a copy-of-<name> ID, handling conflicts with suffixes.

    Args:
        source_id: The source agent ID to copy from.
        storage: StorageManager instance to check for conflicts.

    Returns:
        A unique ID like 'copy-of-chat-agent' or 'copy-of-chat-agent-2'.
    """
    base_id = f"copy-of-{source_id}"
    new_id = base_id
    counter = 2

    while storage.agent_exists(new_id):
        new_id = f"{base_id}-{counter}"
        counter += 1

    return new_id


def _build_clone_plan(
    source_id: str,
    storage: StorageManager,
    visiting: set[str] | None = None,
) -> list[ClonePlanItem]:
    """Build a plan of all agents to clone (main + sub-agents recursively).

    Args:
        source_id: The source agent ID to clone.
        storage: StorageManager instance.
        visiting: Set of source IDs currently being visited (for cycle detection).

    Returns:
        List of ClonePlanItem in order of creation (sub-agents first, main last).
    """
    if visiting is None:
        visiting = set()

    # Detect cycle
    if source_id in visiting:
        console.print(f"[red]Error: Circular reference detected: {source_id}[/red]")
        raise typer.Exit(1)

    visiting.add(source_id)

    # Load the source agent
    agent = storage.get_agent(source_id)
    if not agent:
        console.print(f"[red]Error: Agent '{source_id}' not found[/red]")
        raise typer.Exit(1)

    plan: list[ClonePlanItem] = []

    # First, recursively plan sub-agents
    for sub_id in agent.sub_agents:
        if storage.agent_exists_local(sub_id):
            # Sub-agent already exists locally - use it
            plan.append(
                ClonePlanItem(
                    source_id=sub_id,
                    target_id=sub_id,
                    action="use existing",
                )
            )
        else:
            # Need to clone this sub-agent and its dependencies
            sub_plan = _build_clone_plan(sub_id, storage, visiting.copy())
            plan.extend(sub_plan)

    # Finally, add the main agent
    target_id = _generate_copy_id(source_id, storage)
    plan.append(
        ClonePlanItem(
            source_id=source_id,
            target_id=target_id,
            action="create",
            is_main=True,
        )
    )

    return plan


def _display_clone_plan(plan: list[ClonePlanItem], source_id: str) -> None:
    """Display the clone plan as a table.

    Args:
        plan: List of ClonePlanItem to display.
        source_id: The original source agent ID.
    """
    # Count items to create vs use existing
    to_create = [p for p in plan if p.action == "create"]
    to_use = [p for p in plan if p.action == "use existing"]

    if len(to_create) == 1 and not to_use:
        # Simple case: just the main agent, no sub-agents
        main = to_create[0]
        console.print(f"\nCreating '[bold]{main.target_id}[/bold]' from '{main.source_id}'")
    else:
        # Complex case: show table
        sub_count = len(plan) - 1  # Exclude main agent
        if sub_count > 0:
            console.print(
                f"\nCreating '[bold]{plan[-1].target_id}[/bold]' with {sub_count} sub-agent(s):\n"
            )
        else:
            console.print(f"\nCreating '[bold]{plan[-1].target_id}[/bold]':\n")

        table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
        table.add_column("AGENT", style="cyan")
        table.add_column("ACTION")
        table.add_column("FROM", style="dim")

        for item in plan:
            if item.action == "create":
                action_text = "[green]create[/green]"
            else:
                action_text = "[dim]use existing[/dim]"

            table.add_row(item.target_id, action_text, item.source_id)

        console.print(table)

    console.print()


def _execute_clone_plan(
    plan: list[ClonePlanItem],
    storage: StorageManager,
    auth: AuthConfig,
    platform: PlatformClient,
) -> Agent:
    """Execute the clone plan, creating agents on platform and locally.

    Args:
        plan: List of ClonePlanItem to execute.
        storage: StorageManager instance.
        auth: Authentication configuration.
        platform: Platform client for API calls.

    Returns:
        The main agent that was created.
    """
    # Track mapping from source_id to actual target_id for sub-agent references
    id_mapping: dict[str, str] = {}

    main_agent: Agent | None = None

    for item in plan:
        if item.action == "use existing":
            # Just record the mapping
            id_mapping[item.source_id] = item.target_id
            continue

        # Load source agent
        agent = storage.get_agent(item.source_id)
        if not agent:
            console.print(f"[red]Error: Agent '{item.source_id}' not found[/red]")
            raise typer.Exit(1)

        # Update agent ID and serial
        agent.id = item.target_id
        agent.serial = get_next_local_serial()

        # Remap sub-agent references to their new IDs
        agent.sub_agents = [id_mapping.get(sub_id, sub_id) for sub_id in agent.sub_agents]

        # Create on platform
        try:
            status_msg = f"[bold cyan]Creating '{item.target_id}'...[/bold cyan]"
            with Status(status_msg, console=console):
                response = platform.create_agent(agent)
                agent.is_active = True
                agent.endpoint = response.endpoint
                agent.platform_agent_id = response.agent_id
                agent.platform_env_id = response.env_id
                agent.marketplace_app_id = response.app_id
        except PlatformError as e:
            console.print(f"[red]Platform Error creating '{item.target_id}':[/red] {e}")
            raise typer.Exit(1) from None

        # Save locally
        storage.save_agent(agent)

        # Record mapping
        id_mapping[item.source_id] = item.target_id

        if item.is_main:
            main_agent = agent
        else:
            console.print(f"  [green]\u2713[/green] {item.target_id}")

    if main_agent is None:
        console.print("[red]Error: No main agent created[/red]")
        raise typer.Exit(1)

    return main_agent


def get_agent(source_id: str) -> None:
    """Clone agent to agents/copy-of-<name>.yaml and create on platform.

    Args:
        source_id: Built-in agent ID or serial number.
    """
    auth = require_auth()
    storage = StorageManager()

    # Resolve source_id (could be serial number or agent ID)
    resolved_source_id = resolve_builtin_agent_id(source_id, storage)
    if resolved_source_id is None:
        raise typer.Exit(1)

    # Build the clone plan (includes all sub-agents recursively)
    plan = _build_clone_plan(resolved_source_id, storage)

    # Display the plan
    _display_clone_plan(plan, resolved_source_id)

    # Ask for confirmation
    confirm = console.input("Proceed? [Y/n]: ").strip().lower()
    if confirm and confirm not in ("y", "yes"):
        console.print("[dim]Cancelled.[/dim]")
        raise typer.Exit(0)

    # Create platform client
    platform = PlatformClient(auth)

    # Execute the plan
    console.print()
    agent = _execute_clone_plan(plan, storage, auth, platform)

    # Show success message
    console.print(f"\n[green]Agent '{agent.id}' created successfully![/green]")
    console.print(f"[dim]Local config:[/dim] agents/{agent.id}.yaml")
    if agent.platform_agent_id:
        studio_url = f"https://studio.lyzr.ai/agent-create/{agent.platform_agent_id}"
        console.print(f"[dim]Studio URL:[/dim] {studio_url}")

    console.print(f"\n[dim]To rename, edit the YAML and run:[/dim] lk agent set {agent.id}")
