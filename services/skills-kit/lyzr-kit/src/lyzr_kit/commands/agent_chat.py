"""Agent chat command implementation with real-time event streaming."""

import uuid
from pathlib import Path

import typer
from rich.status import Status

from lyzr_kit.commands._auth_helper import require_auth
from lyzr_kit.commands._chat import (
    ChatStreamer,
    build_session_box,
    create_prompt_session,
    format_timestamp,
)
from lyzr_kit.commands._chat.state import StreamState  # noqa: F401 - re-exported for tests
from lyzr_kit.commands._chat.streaming import decode_sse_data, separate_thinking_content
from lyzr_kit.commands._chat.ui import build_agent_box as _build_agent_box  # noqa: F401
from lyzr_kit.commands._chat.ui import build_session_box as _build_session_box  # noqa: F401
from lyzr_kit.commands._chat.ui import build_user_box as _build_user_box  # noqa: F401
from lyzr_kit.commands._console import console
from lyzr_kit.commands._resolver import resolve_local_agent_id
from lyzr_kit.storage import StorageManager, format_schema_errors, validate_agent_yaml_file

# Re-export for backward compatibility with tests
_format_timestamp = format_timestamp
_decode_sse_data = decode_sse_data
_separate_thinking_content = separate_thinking_content


def chat_with_agent(identifier: str) -> None:
    """Start interactive chat session with an agent.

    Args:
        identifier: Agent ID or serial number.
    """
    auth = require_auth()

    # Validate all .env tokens are present
    if not auth.user_id or not auth.memberstack_token:
        console.print("[red]Error: Missing required .env tokens[/red]")
        console.print("[dim]LYZR_USER_ID and LYZR_MEMBERSTACK_TOKEN are required for chat.[/dim]")
        console.print("[dim]Run 'lk auth' to configure all tokens.[/dim]")
        raise typer.Exit(1)

    # Initialize with loading indicator
    with Status("[bold cyan]Loading agent...[/bold cyan]", console=console):
        # Resolve identifier (could be serial number or agent ID)
        storage = StorageManager()
        agent_id = resolve_local_agent_id(identifier, storage)
        if agent_id is None:
            raise typer.Exit(1)

        # Validate agent exists
        yaml_path = Path(storage.local_path) / "agents" / f"{agent_id}.yaml"

        if not yaml_path.exists():
            console.print(f"[red]Error: Agent '{agent_id}' not found in agents/[/red]")
            console.print("[dim]Run 'lk agent get <source> <id>' first to clone the agent[/dim]")
            raise typer.Exit(1)

        # Validate YAML and schema
        agent, schema_error, yaml_error = validate_agent_yaml_file(yaml_path)

        if yaml_error:
            console.print(f"[red]Error: {yaml_error}[/red]")
            raise typer.Exit(1)

        if schema_error:
            console.print(format_schema_errors(schema_error, agent_id))
            raise typer.Exit(1)

        if not agent:
            console.print(f"[red]Error: Failed to load agent '{agent_id}'[/red]")
            raise typer.Exit(1)

        # Validate agent is active
        if not agent.is_active:
            console.print(f"[red]Error: Agent '{agent_id}' is not active[/red]")
            console.print("[dim]Run 'lk agent get <source> <id>' to deploy the agent first[/dim]")
            raise typer.Exit(1)

        # Validate platform IDs exist
        if not agent.platform_agent_id:
            console.print(f"[red]Error: Agent '{agent_id}' has no platform ID[/red]")
            console.print("[dim]Delete the agent and run 'lk agent get' again[/dim]")
            raise typer.Exit(1)

    # Generate session ID
    session_id = str(uuid.uuid4())
    streamer = ChatStreamer(auth, agent, session_id)

    # Session header box
    session_time = format_timestamp()
    console.print()
    console.print(build_session_box(agent, session_id, session_time))
    console.print("[dim]Type your message and press Enter. Use /exit to end.[/dim]\n")

    # Create prompt session with custom key bindings
    prompt_session = create_prompt_session()

    # Chat loop
    while True:
        try:
            # Get user input with full readline support
            user_input = prompt_session.prompt([("class:prompt", "> ")])

            # Record timestamp immediately on submit
            timestamp = format_timestamp()

            if user_input.strip().lower() == "/exit":
                console.print("\n[dim]Chat session ended.[/dim]")
                break

            if not user_input.strip():
                continue

            # Stream agent response
            streamer.stream_message(user_input, timestamp)

        except KeyboardInterrupt:
            console.print("\n\n[dim]Chat session ended.[/dim]")
            break
        except EOFError:
            # Ctrl+D pressed
            console.print("\n[dim]Chat session ended.[/dim]")
            break
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}\n")
