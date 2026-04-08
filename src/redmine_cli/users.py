"""User commands for the Redmine CLI."""

from __future__ import annotations

import json
from typing import Annotated, Any

import typer
from rich.console import Console
from rich.panel import Panel

from redmine_cli.client import RedmineClient
from redmine_cli.config import load_config
from redmine_cli.models import User

console = Console()
err_console = Console(stderr=True)

user_app = typer.Typer(help="User information")


def get_client(profile: str | None = None) -> RedmineClient:
    """Create and return a RedmineClient from the given profile configuration."""
    config = load_config(profile)
    return RedmineClient(config)


def print_json(data: Any) -> None:
    """Print data as formatted JSON."""
    console.print_json(json.dumps(data, indent=2, ensure_ascii=False))


def resolve_user_id(client: RedmineClient, user_spec: str) -> int:
    """Resolve a user specifier to a numeric user ID.

    If user_spec is "me", fetches the current user and returns their ID.
    Otherwise parses user_spec as an integer.
    """
    if user_spec == "me":
        user = client.get_current_user()
        return int(user["id"])
    return int(user_spec)


def _mask_api_key(key: str | None) -> str:
    """Mask an API key, showing only the first 8 characters."""
    if not key:
        return "N/A"
    if len(key) <= 8:
        return "*" * len(key)
    return key[:8] + "*" * (len(key) - 8)


@user_app.command("me")
def me(
    format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format",
            case_sensitive=False,
        ),
    ] = "table",
) -> None:
    """Show current user info."""
    client = get_client()
    try:
        data = client.get_current_user()
    except Exception as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e

    if format == "json":
        print_json(data)
        return

    user = User(**data)

    lines = [
        f"[bold]ID:[/bold]       {user.id}",
        f"[bold]Name:[/bold]     {user.full_name}",
        f"[bold]Login:[/bold]    {user.login or 'N/A'}",
        f"[bold]Email:[/bold]    {user.mail or 'N/A'}",
        f"[bold]API Key:[/bold]  {_mask_api_key(user.api_key)}",
    ]
    if user.last_login_on:
        lines.append(f"[bold]Last Login:[/bold] {user.last_login_on:%Y-%m-%d %H:%M:%S}")

    console.print(Panel("\n".join(lines), title="Current User", border_style="blue"))
