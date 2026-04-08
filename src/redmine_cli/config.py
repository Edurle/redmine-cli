"""Configuration management for Redmine CLI.

Supports TOML config file (~/.redmine-cli/config.toml) with multi-profile
and environment variable override (REDMINE_URL, REDMINE_API_KEY).
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

import typer
from pydantic import BaseModel
from rich.console import Console

console = Console()
err_console = Console(stderr=True)


class ProfileConfig(BaseModel):
    """Configuration for a single Redmine profile."""

    url: str
    api_key: str
    default_project: str | None = None


class AppConfig(BaseModel):
    """Top-level application configuration."""

    default_profile: str = "default"
    profiles: dict[str, ProfileConfig]


def get_config_dir() -> Path:
    """Return the config directory path."""
    return Path.home() / ".redmine-cli"


def get_config_path() -> Path:
    """Return the config file path."""
    return get_config_dir() / "config.toml"


def load_config(profile: str | None = None) -> ProfileConfig:
    """Load configuration with env var override and profile selection.

    Priority: environment variables > config file > error.
    """
    # Step 1: Check environment variables (highest priority)
    env_url = os.environ.get("REDMINE_URL")
    env_key = os.environ.get("REDMINE_API_KEY")
    if env_url and env_key:
        return ProfileConfig(url=env_url, api_key=env_key)

    # Step 2: Load config file
    config_path = get_config_path()
    if not config_path.exists():
        err_console.print(
            "[red]Error:[/red] No configuration found.\n"
            "Run [bold]redmine config init[/bold] to create one, or set "
            "[bold]REDMINE_URL[/bold] and [bold]REDMINE_API_KEY[/bold] environment variables."
        )
        raise typer.Exit(1)

    try:
        with open(config_path, "rb") as f:
            raw = tomllib.load(f)
    except Exception as e:
        err_console.print(f"[red]Error:[/red] Failed to parse config file: {e}")
        raise typer.Exit(1) from e

    # Step 3: Parse profiles
    profiles: dict[str, ProfileConfig] = {}
    for name, data in raw.get("profiles", {}).items():
        profiles[name] = ProfileConfig(**data)

    if not profiles:
        err_console.print("[red]Error:[/red] No profiles defined in config file.")
        raise typer.Exit(1)

    # Step 4: Resolve profile name
    profile_name = profile or raw.get("default_profile", "default")
    if profile_name not in profiles:
        err_console.print(
            f"[red]Error:[/red] Profile '{profile_name}' not found. "
            f"Available: {', '.join(profiles.keys())}"
        )
        raise typer.Exit(1)

    return profiles[profile_name]


def init_config() -> None:
    """Create config directory and write a template config file."""
    config_dir = get_config_dir()
    config_path = get_config_path()

    if config_path.exists():
        console.print(f"Config file already exists at [bold]{config_path}[/bold]")
        overwrite = typer.confirm("Overwrite?")
        if not overwrite:
            raise typer.Exit(0)

    config_dir.mkdir(parents=True, exist_ok=True)

    template = """\
# Redmine CLI Configuration
# Run `redmine config test` to verify your settings.

default_profile = "default"

[profiles.default]
url = "http://your-redmine-server.example.com"
api_key = "your-api-key-here"
# default_project = "project-identifier"
"""
    config_path.write_text(template)
    console.print(f"Config file created at [bold]{config_path}[/bold]")
    console.print("Edit it with your Redmine URL and API key, then run [bold]redmine config test[/bold]")


def show_config(profile: str | None = None) -> None:
    """Display current configuration."""
    config = load_config(profile)
    console.print("[bold]Current configuration:[/bold]")
    console.print(f"  URL:           {config.url}")
    console.print(f"  API Key:       {config.api_key[:8]}{'*' * (len(config.api_key) - 8)}")
    if config.default_project:
        console.print(f"  Default Project: {config.default_project}")
    console.print(f"\nConfig file: {get_config_path()}")


def test_config(profile: str | None = None) -> None:
    """Test connection to Redmine server."""
    from redmine_cli.client import RedmineClient

    config = load_config(profile)
    client = RedmineClient(config)

    try:
        user = client.get_current_user()
        console.print("[green]Connection successful![/green]")
        console.print(f"  Logged in as: {user.get('lastname', '')}{user.get('firstname', '')} ({user.get('login', '')})")
        console.print(f"  User ID:      {user.get('id')}")
        console.print(f"  Email:        {user.get('mail', 'N/A')}")
    except Exception as e:
        err_console.print(f"[red]Connection failed:[/red] {e}")
        raise typer.Exit(1) from e
