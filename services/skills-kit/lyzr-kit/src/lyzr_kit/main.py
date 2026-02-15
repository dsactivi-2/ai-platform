"""Main CLI entry point for lyzr-kit."""

import typer

from lyzr_kit.commands.agent import app as agent_app
from lyzr_kit.commands.agent_chat import chat_with_agent
from lyzr_kit.commands.agent_doctor import doctor_agents
from lyzr_kit.commands.agent_get import get_agent
from lyzr_kit.commands.agent_list import list_agents
from lyzr_kit.commands.agent_rm import rm_agent
from lyzr_kit.commands.agent_set import set_agent
from lyzr_kit.commands.agent_tree import tree_agent
from lyzr_kit.commands.auth import auth as auth_command
from lyzr_kit.commands.feature import app as feature_app
from lyzr_kit.commands.tool import app as tool_app

app = typer.Typer(
    name="lk",
    help="Deploy and manage AI agents with sub-agent orchestration.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

# Register subcommands
app.add_typer(agent_app, name="agent", help="Manage agents")
app.add_typer(agent_app, name="a", hidden=True)  # Shorthand

app.add_typer(tool_app, name="tool", help="Manage tools")
app.add_typer(tool_app, name="t", hidden=True)  # Shorthand

app.add_typer(feature_app, name="feature", help="Manage features")
app.add_typer(feature_app, name="f", hidden=True)  # Shorthand

app.command(name="auth")(auth_command)


# Default agent commands at root level (agent resource is optional)
@app.command("ls")
@app.command("list", hidden=True)
def ls() -> None:
    """List built-in and local agents."""
    list_agents()


@app.command("get")
def get(
    source_id: str = typer.Argument(..., help="Built-in agent ID or serial (#)"),
) -> None:
    """Clone a built-in agent (with sub-agents)."""
    get_agent(source_id)


@app.command("set")
def set_cmd(
    identifier: str = typer.Argument(..., help="Your agent ID or serial (#)"),
) -> None:
    """Sync local YAML changes to platform."""
    set_agent(identifier)


@app.command("chat")
def chat(
    identifier: str = typer.Argument(..., help="Your agent ID or serial (#)"),
) -> None:
    """Start interactive chat with an agent."""
    chat_with_agent(identifier)


@app.command("rm")
@app.command("delete", hidden=True)
def rm(
    identifier: str = typer.Argument(..., help="Your agent ID or serial (#)"),
    force: bool = typer.Option(False, "--force", "-f", help="Remove from parent agents and delete"),
    tree: bool = typer.Option(False, "--tree", "-t", help="Also delete all sub-agents recursively"),
) -> None:
    """Delete a local agent (--tree for sub-agents)."""
    rm_agent(identifier, force=force, tree=tree)


@app.command("tree")
def tree_cmd(
    identifier: str = typer.Argument(None, help="Agent ID or serial (#). Shows all if omitted."),
) -> None:
    """Visualize agent sub-agent hierarchy."""
    tree_agent(identifier)


@app.command("doctor")
def doctor() -> None:
    """Check for missing sub-agents and cycles."""
    doctor_agents()


if __name__ == "__main__":
    app()
