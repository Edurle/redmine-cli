"""Time entry commands for the Redmine CLI."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Annotated, Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from redmine_cli.users import get_client, print_json, resolve_user_id

console = Console()
err_console = Console(stderr=True)

time_app = typer.Typer(help="Manage time entries")


def expand_period(period: str) -> tuple[date, date]:
    """Expand a predefined period name to (from_date, to_date)."""
    today = date.today()
    if period == "today":
        return today, today
    elif period == "yesterday":
        d = today - timedelta(days=1)
        return d, d
    elif period == "this_week":
        start = today - timedelta(days=today.weekday())
        return start, start + timedelta(days=6)
    elif period == "last_week":
        start = today - timedelta(days=today.weekday() + 7)
        return start, start + timedelta(days=6)
    elif period == "this_month":
        start = today.replace(day=1)
        if today.month == 12:
            end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        return start, end
    else:
        raise typer.BadParameter(f"Unknown period: {period}")


def _build_time_entry_table(items: list[dict[str, Any]]) -> Table:
    """Build a Rich table for time entries."""
    table = Table(show_header=True, header_style="bold")
    table.add_column("Date", style="cyan")
    table.add_column("Issue", justify="right")
    table.add_column("Project")
    table.add_column("User")
    table.add_column("Hours", justify="right")
    table.add_column("Activity")
    table.add_column("Comment", max_width=40)

    for item in items:
        issue = item.get("issue") or {}
        issue_label = f"#{issue.get('id', '')}" if issue else "-"
        project = item.get("project") or {}
        user = item.get("user") or {}
        activity = item.get("activity") or {}
        table.add_row(
            str(item.get("spent_on", "")),
            issue_label,
            project.get("name", ""),
            user.get("name", ""),
            str(item.get("hours", "")),
            activity.get("name", ""),
            item.get("comments", "") or "",
        )
    return table


@time_app.command("list")
def list_time_entries(
    user: Annotated[str, typer.Option("--user", "-u", help="User ID or 'me'")] = "me",
    project: Annotated[str | None, typer.Option("--project", "-p", help="Project identifier")] = None,
    issue: Annotated[int | None, typer.Option("--issue", "-i", help="Issue ID")] = None,
    from_date: Annotated[str | None, typer.Option("--from", help="From date (YYYY-MM-DD)")] = None,
    to_date: Annotated[str | None, typer.Option("--to", help="To date (YYYY-MM-DD)")] = None,
    period: Annotated[
        str | None,
        typer.Option("--period", help="Predefined period: today, yesterday, this_week, last_week, this_month"),
    ] = None,
    limit: Annotated[int, typer.Option("--limit", "-l", help="Results per page")] = 25,
    fmt: Annotated[str, typer.Option("--format", "-f", help="Output format")] = "table",
) -> None:
    """List time entries with filters."""
    client = get_client()

    # Expand period if set
    if period is not None:
        p_from, p_to = expand_period(period)
        from_date = p_from.isoformat()
        to_date = p_to.isoformat()

    params: dict[str, Any] = {}
    if user is not None and user != "*":
        params["user_id"] = resolve_user_id(client, user)
    if project is not None:
        params["project_id"] = project
    if issue is not None:
        params["issue_id"] = issue
    if from_date is not None:
        params["from"] = from_date
    if to_date is not None:
        params["to"] = to_date

    try:
        items, total = client.list_time_entries(limit=limit, **params)
    except Exception as e:
        err_console.print(f"[red]Error listing time entries:[/red] {e}")
        raise typer.Exit(1) from e

    if fmt == "json":
        print_json(items)
    else:
        table = _build_time_entry_table(items)
        console.print(table)
        console.print(f"[dim]Showing {len(items)} of {total} entries[/dim]")


@time_app.command("log")
def log_time(
    issue_id: Annotated[int, typer.Option("--issue", "-i", help="Issue ID", prompt=True)],
    hours: Annotated[float, typer.Option("--hours", "-h", help="Hours spent", prompt=True)],
    activity: Annotated[int, typer.Option("--activity", "-a", help="Activity ID (default: 9=development)")] = 9,
    comment: Annotated[str | None, typer.Option("--comment", "-c", help="Comment")] = None,
    spent_on: Annotated[
        str | None, typer.Option("--date", "-d", help="Date (YYYY-MM-DD, default: today)")
    ] = None,
    fmt: Annotated[str, typer.Option("--format", "-f", help="Output format")] = "table",
) -> None:
    """Log time to an issue. Defaults to today and development activity."""
    client = get_client()

    entry_date = date.fromisoformat(spent_on) if spent_on else date.today()

    data: dict[str, Any] = {
        "issue_id": issue_id,
        "hours": hours,
        "activity_id": activity,
        "spent_on": entry_date.isoformat(),
    }
    if comment is not None:
        data["comments"] = comment

    try:
        created = client.create_time_entry(data)
    except Exception as e:
        err_console.print(f"[red]Error logging time:[/red] {e}")
        raise typer.Exit(1) from e

    if fmt == "json":
        print_json(created)
    else:
        lines = [
            f"[bold]Issue:[/bold]    #{created.get('issue', {}).get('id', issue_id)}",
            f"[bold]Hours:[/bold]    {created.get('hours', hours)}",
            f"[bold]Activity:[/bold] {(created.get('activity') or {}).get('name', '')}",
            f"[bold]Date:[/bold]     {created.get('spent_on', entry_date)}",
            f"[bold]Comment:[/bold]  {created.get('comments', '') or '-'}",
        ]
        console.print(Panel("\n".join(lines), title="Time Entry Logged", border_style="green"))


@time_app.command("activities")
def list_activities(
    fmt: Annotated[str, typer.Option("--format", "-f", help="Output format")] = "table",
) -> None:
    """List available time entry activities."""
    client = get_client()

    try:
        activities = client.list_time_entry_activities()
    except Exception as e:
        err_console.print(f"[red]Error fetching activities:[/red] {e}")
        raise typer.Exit(1) from e

    if fmt == "json":
        print_json(activities)
    else:
        table = Table(show_header=True, header_style="bold")
        table.add_column("ID", style="cyan", justify="right")
        table.add_column("Name")
        table.add_column("Default", justify="center")
        table.add_column("Active", justify="center")

        for act in activities:
            table.add_row(
                str(act.get("id", "")),
                str(act.get("name", "")),
                "Yes" if act.get("is_default") else "",
                "Yes" if act.get("active", True) else "No",
            )
        console.print(table)
