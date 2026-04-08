"""Project commands for the Redmine CLI."""

from __future__ import annotations

from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from redmine_cli.models import Membership, Project
from redmine_cli.users import get_client, print_json

console = Console()
err_console = Console(stderr=True)

project_app = typer.Typer(help="Manage Redmine projects")


@project_app.command("list")
def list_projects(
    status: Annotated[
        int,
        typer.Option("--status", help="1=active, 5=closed, 9=archived"),
    ] = 1,
    limit: Annotated[
        int,
        typer.Option("--limit", "-l", help="Maximum number of projects to return"),
    ] = 25,
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
    """List projects."""
    client = get_client()
    try:
        items, total_count = client.list_projects(status=status, limit=limit)
    except Exception as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e

    if format == "json":
        print_json(items)
        return

    status_labels: dict[int, str] = {1: "Active", 5: "Closed", 9: "Archived"}

    table = Table(title="Projects")
    table.add_column("ID", justify="right", style="cyan")
    table.add_column("Identifier", style="green")
    table.add_column("Name")
    table.add_column("Status")
    table.add_column("Public", justify="center")

    for raw in items:
        project = Project(**raw)
        label = status_labels.get(project.status, str(project.status))
        public_mark = "Yes" if project.is_public else "No"
        table.add_row(
            str(project.id),
            project.identifier,
            project.name,
            label,
            public_mark,
        )

    console.print(table)
    console.print(f"[dim]Showing {len(items)} of {total_count} projects[/dim]")


@project_app.command("show")
def show_project(
    project_id: Annotated[
        str,
        typer.Argument(help="Project identifier or ID"),
    ],
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
    """Show project details."""
    client = get_client()
    try:
        data = client.get_project(project_id)
    except Exception as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e

    if format == "json":
        print_json(data)
        return

    project = Project(**data)

    status_labels: dict[int, str] = {1: "Active", 5: "Closed", 9: "Archived"}
    status_text = status_labels.get(project.status, str(project.status))
    public_text = "Yes" if project.is_public else "No"
    parent_text = project.parent.name if project.parent else "None"
    created_text = f"{project.created_on:%Y-%m-%d %H:%M:%S}" if project.created_on else "N/A"
    updated_text = f"{project.updated_on:%Y-%m-%d %H:%M:%S}" if project.updated_on else "N/A"
    description_text = project.description or "N/A"

    lines = [
        f"[bold]ID:[/bold]          {project.id}",
        f"[bold]Identifier:[/bold]  {project.identifier}",
        f"[bold]Name:[/bold]        {project.name}",
        f"[bold]Status:[/bold]      {status_text}",
        f"[bold]Public:[/bold]      {public_text}",
        f"[bold]Parent:[/bold]      {parent_text}",
        f"[bold]Created:[/bold]     {created_text}",
        f"[bold]Updated:[/bold]     {updated_text}",
        f"[bold]Description:[/bold] {description_text}",
    ]

    console.print(
        Panel("\n".join(lines), title=f"Project: {project.name}", border_style="blue")
    )


@project_app.command("members")
def list_members(
    project_id: Annotated[
        str,
        typer.Argument(help="Project identifier or ID"),
    ],
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
    """List project members."""
    client = get_client()
    try:
        items, total_count = client.get_project_memberships(project_id, limit=100)
    except Exception as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e

    if format == "json":
        print_json(items)
        return

    table = Table(title="Project Members")
    table.add_column("Name", style="cyan")
    table.add_column("Roles")

    for raw in items:
        membership = Membership(**raw)
        name = ""
        if membership.user:
            name = membership.user.name
        elif membership.group:
            name = membership.group.name

        roles = ", ".join(role.name for role in membership.roles) if membership.roles else "N/A"
        table.add_row(name, roles)

    console.print(table)
    console.print(f"[dim]Showing {len(items)} of {total_count} members[/dim]")
