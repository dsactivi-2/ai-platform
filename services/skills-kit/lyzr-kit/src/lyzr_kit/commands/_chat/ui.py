"""UI component builders for chat display."""

from datetime import datetime

from rich.box import ROUNDED
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from lyzr_kit.commands._chat.state import StreamState
from lyzr_kit.schemas.agent import Agent


def format_timestamp(dt: datetime | None = None) -> str:
    """Format timestamp for display."""
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%H:%M:%S")


def build_session_box(agent: Agent, session_id: str, start_time: str) -> Panel:
    """Build the session header box displayed at chat start."""
    info_table = Table.grid(padding=(0, 2))
    info_table.add_column(style="dim", justify="right")
    info_table.add_column(style="bold")

    model_name = "default"
    if agent.model:
        model_name = agent.model.name if hasattr(agent.model, "name") else str(agent.model)

    info_table.add_row("Agent", agent.name)
    info_table.add_row("Model", model_name)
    info_table.add_row("Session", session_id[:8])
    info_table.add_row("Started", start_time)

    return Panel(
        info_table,
        title="[bold]Session[/bold]",
        title_align="center",
        border_style="blue",
        box=ROUNDED,
        padding=(0, 1),
    )


def build_user_box(message: str, timestamp: str) -> Panel:
    """Build the user message box."""
    return Panel(
        Text(message),
        title="[cyan]You[/cyan]",
        title_align="left",
        subtitle=f"[dim]{timestamp}[/dim]",
        subtitle_align="right",
        border_style="cyan",
        box=ROUNDED,
        padding=(0, 1),
    )


def build_agent_box(state: StreamState, timestamp: str) -> Panel:
    """Build the agent response box with 4-corner layout.

    Layout:
    - Top-left: "Agent" label
    - Top-right: Timestamp (shown via title formatting)
    - Bottom-left: Latency
    - Bottom-right: Token usage
    """
    content_parts = []

    # Events section (if any)
    if state.events:
        events_text = Text()
        for i, event in enumerate(state.events):
            prefix = "└─" if i == len(state.events) - 1 and not state.content else "├─"
            events_text.append(f"{prefix} ", style="dim")
            events_text.append(event.format_display(), style="dim cyan")
            if i < len(state.events) - 1 or state.content:
                events_text.append("\n")
        content_parts.append(events_text)

    # Response content
    if state.content:
        response_text = Text()
        if state.events:
            response_text.append("\n\n")
        response_text.append(state.content)
        content_parts.append(response_text)
    elif state.is_streaming and not state.events:
        content_parts.append(Text("Waiting for response...", style="dim italic"))

    # Error display (inside content area)
    if state.error:
        error_text = Text()
        if content_parts:
            error_text.append("\n\n")
        error_text.append(f"Error: {state.error}", style="bold red")
        content_parts.append(error_text)

    # Combine all parts
    combined: Group | Text = Group(*content_parts) if content_parts else Text("...", style="dim")

    # Determine border style based on error state
    is_error_only = state.error and not state.content
    border_style = "red" if is_error_only else "green"
    title_label = "Error" if is_error_only else "Agent"
    title_style = "red" if is_error_only else "green"

    # Build title: "Agent" on left, timestamp on right
    title = f"[{title_style}]{title_label}[/{title_style}] [dim]{timestamp}[/dim]"

    # Build subtitle with metrics (bottom edge) - only after streaming completes
    if not state.is_streaming and (state.content or state.error):
        # Format latency
        if state.total_time_ms > 0:
            latency_sec = state.total_time_ms / 1000
            latency_str = f"[bold]{latency_sec:.2f}s[/bold]"
        else:
            latency_str = "[dim]-[/dim]"

        # Format token usage
        if state.tokens_in > 0 or state.tokens_out > 0:
            tokens_str = f"[dim]{state.tokens_in} → {state.tokens_out} tokens[/dim]"
            subtitle = f"{latency_str}                                        {tokens_str}"
        else:
            subtitle = latency_str
    else:
        subtitle = None

    return Panel(
        combined,
        title=title,
        title_align="left",
        subtitle=subtitle,
        subtitle_align="left",
        border_style=border_style,
        box=ROUNDED,
        padding=(0, 1),
    )
