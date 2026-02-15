"""Authentication helper for CLI commands."""

import typer

from lyzr_kit.commands._console import console
from lyzr_kit.utils.auth import AuthConfig, AuthError, load_auth, validate_auth


def require_auth() -> AuthConfig:
    """Check authentication before running commands.

    Returns:
        AuthConfig if authentication is valid.

    Raises:
        typer.Exit: If authentication fails.
    """
    try:
        auth = load_auth()
        validate_auth(auth)
        return auth
    except AuthError as e:
        console.print(f"[red]Authentication Error:[/red]\n{e}")
        raise typer.Exit(1) from None
