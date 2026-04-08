"""Redmine CLI - Main entry point."""

from __future__ import annotations

from typing import Annotated

import typer
from rich.console import Console

from redmine_cli.config import init_config, show_config, test_config
from redmine_cli.issues import issue_app
from redmine_cli.projects import project_app
from redmine_cli.time_entries import time_app
from redmine_cli.users import get_client, print_json, user_app

console = Console()
err_console = Console(stderr=True)

app = typer.Typer(
    name="redmine",
    help="Redmine CLI - Manage issues, projects, time entries from the command line.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

# Register sub-apps
app.add_typer(issue_app, name="issues")
app.add_typer(project_app, name="projects")
app.add_typer(user_app, name="users")
app.add_typer(time_app, name="time")


@app.command("config")
def config_cmd(
    action: Annotated[str, typer.Argument(help="Action: show, init, test")] = "show",
    profile: Annotated[str | None, typer.Option("--profile", "-P", help="Config profile")] = None,
) -> None:
    """Manage configuration: show current config, initialize, or test connection."""
    if action == "init":
        init_config()
    elif action == "test":
        test_config(profile)
    elif action == "show":
        show_config(profile)
    else:
        err_console.print(f"[red]Error:[/red] Unknown action '{action}'. Use: show, init, test")
        raise typer.Exit(1)


@app.command("my-issues")
def my_issues(
    status: Annotated[str, typer.Option("--status", "-s", help="Status filter: open, closed, *")] = "open",
    project: Annotated[str | None, typer.Option("--project", "-p", help="Project identifier")] = None,
    fmt: Annotated[str, typer.Option("--format", "-f", help="Output format")] = "table",
    limit: Annotated[int, typer.Option("--limit", "-l", help="Results per page")] = 25,
) -> None:
    """Shortcut: list issues assigned to me."""
    client = get_client()

    from redmine_cli.users import resolve_user_id

    try:
        my_id = resolve_user_id(client, "me")
    except Exception as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e

    params: dict = {"assigned_to_id": my_id, "sort": "updated_on:desc"}
    if project:
        params["project_id"] = project

    if status == "open":
        params["status_id"] = "open"
    elif status == "closed":
        params["status_id"] = "closed"
    elif status != "*":
        params["status_id"] = status

    try:
        items, total = client.list_issues(limit=limit, **params)
    except Exception as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e

    if fmt == "json":
        print_json(items)
    else:
        from rich.table import Table

        table = Table(show_header=True, header_style="bold")
        table.add_column("ID", style="cyan", justify="right")
        table.add_column("Tracker")
        table.add_column("Status")
        table.add_column("Priority")
        table.add_column("Subject", max_width=50)
        table.add_column("Due Date")
        table.add_column("Done%", justify="right")

        for item in items:
            due = item.get("due_date", "-") or "-"
            table.add_row(
                str(item.get("id", "")),
                (item.get("tracker") or {}).get("name", ""),
                (item.get("status") or {}).get("name", ""),
                (item.get("priority") or {}).get("name", ""),
                str(item.get("subject", "")),
                str(due),
                f"{item.get('done_ratio', 0)}%",
            )
        console.print(table)
        console.print(f"[dim]Showing {len(items)} of {total} issues[/dim]")
