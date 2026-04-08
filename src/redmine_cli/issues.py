"""Typer sub-app for managing Redmine issues."""

from __future__ import annotations

from datetime import date
from typing import Annotated, Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from redmine_cli.users import get_client, print_json, resolve_user_id

console = Console()
err_console = Console(stderr=True)

issue_app = typer.Typer(help="Manage Redmine issues")


def _build_issue_table(items: list[dict[str, Any]]) -> Table:
    """Build a Rich table for a list of issues."""
    table = Table(show_header=True, header_style="bold")
    table.add_column("ID", style="cyan", justify="right")
    table.add_column("Tracker")
    table.add_column("Status")
    table.add_column("Priority")
    table.add_column("Subject", max_width=50)
    table.add_column("Assignee")
    table.add_column("Due Date")
    table.add_column("Done%", justify="right")

    for item in items:
        assigned = item.get("assigned_to", {})
        assignee_name = assigned.get("name", "-") if assigned else "-"
        due = item.get("due_date", "-") or "-"
        table.add_row(
            str(item.get("id", "")),
            (item.get("tracker") or {}).get("name", ""),
            (item.get("status") or {}).get("name", ""),
            (item.get("priority") or {}).get("name", ""),
            str(item.get("subject", "")),
            assignee_name,
            str(due),
            f"{item.get('done_ratio', 0)}%",
        )
    return table


def _build_issue_detail_panel(issue_data: dict[str, Any]) -> Panel:
    """Build a Rich Panel with full issue details."""
    lines: list[str] = []
    lines.append(f"[bold]ID:[/bold]          {issue_data.get('id', '')}")
    lines.append(f"[bold]Subject:[/bold]    {issue_data.get('subject', '')}")
    lines.append(
        f"[bold]Project:[/bold]    {(issue_data.get('project') or {}).get('name', '')}"
    )
    lines.append(
        f"[bold]Tracker:[/bold]    {(issue_data.get('tracker') or {}).get('name', '')}"
    )
    lines.append(
        f"[bold]Status:[/bold]     {(issue_data.get('status') or {}).get('name', '')}"
    )
    lines.append(
        f"[bold]Priority:[/bold]   {(issue_data.get('priority') or {}).get('name', '')}"
    )
    lines.append(
        f"[bold]Author:[/bold]     {(issue_data.get('author') or {}).get('name', '')}"
    )
    assigned = issue_data.get("assigned_to")
    lines.append(
        f"[bold]Assignee:[/bold]   {assigned.get('name', '') if assigned else '-'}"
    )
    lines.append(f"[bold]Done:[/bold]       {issue_data.get('done_ratio', 0)}%")
    lines.append(f"[bold]Start Date:[/bold] {issue_data.get('start_date', '-') or '-'}")
    lines.append(f"[bold]Due Date:[/bold]   {issue_data.get('due_date', '-') or '-'}")
    estimated = issue_data.get("estimated_hours")
    lines.append(
        f"[bold]Est. Hours:[/bold] {estimated if estimated is not None else '-'}"
    )
    lines.append(f"[bold]Created:[/bold]    {issue_data.get('created_on', '-') or '-'}")
    lines.append(f"[bold]Updated:[/bold]    {issue_data.get('updated_on', '-') or '-'}")

    description = issue_data.get("description")
    if description:
        lines.append(f"\n[bold]Description:[/bold]\n{description}")

    return Panel("\n".join(lines), title=f"Issue #{issue_data.get('id')}", border_style="green")


def _build_journals_panel(journals: list[dict[str, Any]]) -> Panel | None:
    """Build a Rich Panel showing issue journals as a timeline."""
    if not journals:
        return None

    lines: list[str] = []
    for idx, entry in enumerate(journals):
        user = (entry.get("user") or {}).get("name", "Unknown")
        created = entry.get("created_on", "")
        notes = entry.get("notes", "")
        details = entry.get("details", [])

        lines.append(f"[bold cyan]{user}[/bold cyan]  [dim]{created}[/dim]")
        if notes:
            lines.append(f"  {notes}")
        for detail in details:
            prop = detail.get("name", "")
            old = detail.get("old_value", "")
            new = detail.get("new_value", "")
            lines.append(f"  [dim]- {prop}: {old} -> {new}[/dim]")
        if idx < len(journals) - 1:
            lines.append("")

    return Panel("\n".join(lines), title="History / Journals", border_style="blue")


@issue_app.command("list")
def list_issues(
    project: Annotated[str | None, typer.Option("--project", "-p", help="Project identifier")] = None,
    assignee: Annotated[str | None, typer.Option("--assignee", "-a", help="Assignee: 'me', '*', or user ID")] = None,
    status: Annotated[str | None, typer.Option("--status", "-s", help="Status: 'open', 'closed', '*', or status ID")] = None,
    tracker: Annotated[int | None, typer.Option("--tracker", "-t", help="Tracker ID")] = None,
    parent: Annotated[int | None, typer.Option("--parent", help="Parent issue ID")] = None,
    limit: Annotated[int, typer.Option("--limit", "-l", help="Number of results per page")] = 25,
    offset: Annotated[int, typer.Option("--offset", help="Offset for pagination")] = 0,
    fetch_all: Annotated[bool, typer.Option("--all", help="Fetch all pages")] = False,
    sort: Annotated[str, typer.Option("--sort", help="Sort clause (e.g. updated_on:desc)")] = "updated_on:desc",
    fmt: Annotated[str, typer.Option("--format", "-f", help="Output format: table or json")] = "table",
) -> None:
    """List issues with filters."""
    client = get_client()

    params: dict[str, Any] = {"sort": sort}

    if project is not None:
        params["project_id"] = project

    # Resolve assignee
    if assignee is not None:
        if assignee == "me":
            params["assigned_to_id"] = resolve_user_id(client, "me")
        elif assignee == "*":
            pass  # No filter
        else:
            try:
                params["assigned_to_id"] = int(assignee)
            except ValueError:
                err_console.print(f"[red]Error:[/red] Invalid assignee value: {assignee!r}")
                raise typer.Exit(1) from None

    # Resolve status
    if status is not None:
        if status == "open":
            params["status_id"] = "open"
        elif status == "closed":
            params["status_id"] = "closed"
        elif status == "*":
            pass  # No filter
        else:
            try:
                params["status_id"] = int(status)
            except ValueError:
                err_console.print(f"[red]Error:[/red] Invalid status value: {status!r}")
                raise typer.Exit(1) from None

    if tracker is not None:
        params["tracker_id"] = tracker
    if parent is not None:
        params["parent_id"] = parent

    try:
        items, total = client.list_issues(
            limit=limit, offset=offset, all_pages=fetch_all, **params
        )
    except Exception as e:
        err_console.print(f"[red]Error listing issues:[/red] {e}")
        raise typer.Exit(1) from e

    if fmt == "json":
        print_json(items)
    else:
        table = _build_issue_table(items)
        console.print(table)
        console.print(f"[dim]Showing {len(items)} of {total} issues[/dim]")


@issue_app.command("show")
def show_issue(
    issue_id: Annotated[int, typer.Argument(help="Issue ID")],
    include: Annotated[str, typer.Option("--include", help="Comma-separated related data to include")] = "journals",
    fmt: Annotated[str, typer.Option("--format", "-f", help="Output format: table or json")] = "table",
) -> None:
    """Show issue details."""
    client = get_client()

    try:
        issue_data = client.get_issue(issue_id, include=include)
    except Exception as e:
        err_console.print(f"[red]Error fetching issue #{issue_id}:[/red] {e}")
        raise typer.Exit(1) from e

    if fmt == "json":
        print_json(issue_data)
    else:
        panel = _build_issue_detail_panel(issue_data)
        console.print(panel)

        journals = issue_data.get("journals", [])
        journals_panel = _build_journals_panel(journals)
        if journals_panel is not None:
            console.print(journals_panel)


@issue_app.command("create")
def create_issue(
    subject: Annotated[str, typer.Option("--subject", "-s", help="Issue subject")] = ...,
    project: Annotated[str, typer.Option("--project", "-p", help="Project identifier")] = ...,
    tracker: Annotated[int, typer.Option("--tracker", "-t", help="Tracker ID")] = 12,
    priority: Annotated[int, typer.Option("--priority", help="Priority ID")] = 2,
    assignee: Annotated[int | None, typer.Option("--assignee", "-a", help="Assignee user ID")] = None,
    parent: Annotated[int | None, typer.Option("--parent", help="Parent issue ID")] = None,
    description: Annotated[str | None, typer.Option("--description", "-d", help="Issue description")] = None,
    start_date: Annotated[str | None, typer.Option("--start-date", help="Start date (YYYY-MM-DD)")] = None,
    due_date: Annotated[str | None, typer.Option("--due-date", help="Due date (YYYY-MM-DD)")] = None,
    estimated_hours: Annotated[float | None, typer.Option("--estimated-hours", "-e", help="Estimated hours")] = None,
    fmt: Annotated[str, typer.Option("--format", "-f", help="Output format: table or json")] = "table",
) -> None:
    """Create a new issue."""
    client = get_client()

    data: dict[str, Any] = {
        "subject": subject,
        "project_id": project,
        "tracker_id": tracker,
        "priority_id": priority,
    }

    if assignee is not None:
        data["assigned_to_id"] = assignee
    if parent is not None:
        data["parent_issue_id"] = parent
    if description is not None:
        data["description"] = description
    if start_date is not None:
        try:
            data["start_date"] = date.fromisoformat(start_date).isoformat()
        except ValueError:
            err_console.print(f"[red]Error:[/red] Invalid start date: {start_date!r}")
            raise typer.Exit(1) from None
    if due_date is not None:
        try:
            data["due_date"] = date.fromisoformat(due_date).isoformat()
        except ValueError:
            err_console.print(f"[red]Error:[/red] Invalid due date: {due_date!r}")
            raise typer.Exit(1) from None
    if estimated_hours is not None:
        data["estimated_hours"] = estimated_hours

    try:
        created = client.create_issue(data)
    except Exception as e:
        err_console.print(f"[red]Error creating issue:[/red] {e}")
        raise typer.Exit(1) from e

    if fmt == "json":
        print_json(created)
    else:
        panel = _build_issue_detail_panel(created)
        console.print(panel)
        console.print(f"[green]Issue #{created.get('id')} created successfully.[/green]")


@issue_app.command("update")
def update_issue(
    issue_id: Annotated[int, typer.Argument(help="Issue ID")],
    subject: Annotated[str | None, typer.Option("--subject", "-s", help="New subject")] = None,
    status: Annotated[int | None, typer.Option("--status", help="New status ID")] = None,
    assignee: Annotated[int | None, typer.Option("--assignee", "-a", help="New assignee user ID")] = None,
    done_ratio: Annotated[int | None, typer.Option("--done-ratio", help="Completion percentage (0-100)")] = None,
    priority: Annotated[int | None, typer.Option("--priority", help="New priority ID")] = None,
    description: Annotated[str | None, typer.Option("--description", "-d", help="New description")] = None,
    start_date: Annotated[str | None, typer.Option("--start-date", help="New start date (YYYY-MM-DD)")] = None,
    due_date: Annotated[str | None, typer.Option("--due-date", help="New due date (YYYY-MM-DD)")] = None,
    estimated_hours: Annotated[float | None, typer.Option("--estimated-hours", "-e", help="New estimated hours")] = None,
    comment: Annotated[str | None, typer.Option("--comment", "-c", help="Comment / notes to add")] = None,
    fmt: Annotated[str, typer.Option("--format", "-f", help="Output format: table or json")] = "table",
) -> None:
    """Update an existing issue."""
    client = get_client()

    data: dict[str, Any] = {}

    if subject is not None:
        data["subject"] = subject
    if status is not None:
        data["status_id"] = status
    if assignee is not None:
        data["assigned_to_id"] = assignee
    if done_ratio is not None:
        data["done_ratio"] = done_ratio
    if priority is not None:
        data["priority_id"] = priority
    if description is not None:
        data["description"] = description
    if start_date is not None:
        try:
            data["start_date"] = date.fromisoformat(start_date).isoformat()
        except ValueError:
            err_console.print(f"[red]Error:[/red] Invalid start date: {start_date!r}")
            raise typer.Exit(1) from None
    if due_date is not None:
        try:
            data["due_date"] = date.fromisoformat(due_date).isoformat()
        except ValueError:
            err_console.print(f"[red]Error:[/red] Invalid due date: {due_date!r}")
            raise typer.Exit(1) from None
    if estimated_hours is not None:
        data["estimated_hours"] = estimated_hours
    if comment is not None:
        data["notes"] = comment

    if not data:
        err_console.print("[red]Error:[/red] No fields specified for update.")
        raise typer.Exit(1)

    try:
        client.update_issue(issue_id, data)
    except Exception as e:
        err_console.print(f"[red]Error updating issue #{issue_id}:[/red] {e}")
        raise typer.Exit(1) from e

    if fmt == "json":
        print_json({"ok": True, "issue_id": issue_id, "updated_fields": list(data.keys())})
    else:
        console.print(f"[green]Issue #{issue_id} updated successfully.[/green]")


@issue_app.command("comment")
def comment_issue(
    issue_id: Annotated[int, typer.Argument(help="Issue ID")],
    comment: Annotated[str, typer.Option("--comment", "-c", help="Comment text to add")] = ...,
) -> None:
    """Add a comment to an issue."""
    client = get_client()

    try:
        client.update_issue(issue_id, {"notes": comment})
    except Exception as e:
        err_console.print(f"[red]Error commenting on issue #{issue_id}:[/red] {e}")
        raise typer.Exit(1) from e

    console.print(f"[green]Comment added to issue #{issue_id}.[/green]")


@issue_app.command("delete")
def delete_issue(
    issue_id: Annotated[int, typer.Argument(help="Issue ID")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation prompt")] = False,
) -> None:
    """Delete an issue."""
    if not yes:
        confirmed = typer.confirm(f"Are you sure you want to delete issue #{issue_id}?")
        if not confirmed:
            console.print("Aborted.")
            raise typer.Exit(0)

    client = get_client()

    try:
        client.delete_issue(issue_id)
    except Exception as e:
        err_console.print(f"[red]Error deleting issue #{issue_id}:[/red] {e}")
        raise typer.Exit(1) from e

    console.print(f"[green]Issue #{issue_id} deleted successfully.[/green]")
