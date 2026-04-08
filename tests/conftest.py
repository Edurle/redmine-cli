"""Shared test fixtures."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner



@pytest.fixture
def runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


@pytest.fixture
def sample_user_json() -> dict[str, Any]:
    return {
        "id": 731,
        "login": "testuser",
        "firstname": "Test",
        "lastname": "User",
        "mail": "test@example.com",
        "api_key": "abc123def456",
        "created_on": "2024-01-01T00:00:00Z",
        "last_login_on": "2026-04-01T12:00:00Z",
    }


@pytest.fixture
def sample_issue_json() -> dict[str, Any]:
    return {
        "id": 1234,
        "project": {"id": 1, "name": "Test Project"},
        "tracker": {"id": 12, "name": "Program Development"},
        "status": {"id": 1, "name": "New", "is_closed": False},
        "priority": {"id": 2, "name": "Normal"},
        "author": {"id": 731, "name": "User Test"},
        "assigned_to": {"id": 731, "name": "User Test"},
        "subject": "Test issue subject",
        "description": "Test issue description",
        "start_date": "2026-04-01",
        "due_date": "2026-04-10",
        "done_ratio": 30,
        "estimated_hours": 8.0,
        "spent_hours": 2.5,
        "created_on": "2026-04-01T10:00:00Z",
        "updated_on": "2026-04-05T15:30:00Z",
    }


@pytest.fixture
def sample_issues_list_json() -> dict[str, Any]:
    return {
        "issues": [
            {
                "id": 1,
                "project": {"id": 1, "name": "P1"},
                "tracker": {"id": 12, "name": "Dev"},
                "status": {"id": 1, "name": "New", "is_closed": False},
                "priority": {"id": 2, "name": "Normal"},
                "author": {"id": 1, "name": "Admin"},
                "subject": "First issue",
                "done_ratio": 0,
            },
            {
                "id": 2,
                "project": {"id": 1, "name": "P1"},
                "tracker": {"id": 12, "name": "Dev"},
                "status": {"id": 2, "name": "In Progress", "is_closed": False},
                "priority": {"id": 3, "name": "High"},
                "author": {"id": 1, "name": "Admin"},
                "assigned_to": {"id": 731, "name": "User Test"},
                "subject": "Second issue",
                "done_ratio": 50,
            },
        ],
        "total_count": 2,
        "offset": 0,
        "limit": 25,
    }


@pytest.fixture
def sample_project_json() -> dict[str, Any]:
    return {
        "id": 1,
        "name": "Test Project",
        "identifier": "test-project",
        "description": "A test project",
        "status": 1,
        "is_public": False,
        "created_on": "2024-01-01T00:00:00Z",
        "updated_on": "2026-04-01T00:00:00Z",
    }


@pytest.fixture
def sample_time_entry_json() -> dict[str, Any]:
    return {
        "id": 100,
        "project": {"id": 1, "name": "Test Project"},
        "issue": {"id": 1234, "name": "#1234"},
        "user": {"id": 731, "name": "User Test"},
        "activity": {"id": 9, "name": "Development"},
        "hours": 2.5,
        "comments": "Test comment",
        "spent_on": "2026-04-07",
    }


@pytest.fixture
def tmp_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a temp config dir with test config and patch home dir."""
    config_dir = tmp_path / ".redmine-cli"
    config_dir.mkdir()
    config_file = config_dir / "config.toml"
    config_file.write_text(
        '[profiles.default]\n'
        'url = "http://redmine.test"\n'
        'api_key = "testkey123"\n'
    )
    # Patch get_config_dir to return our temp dir
    monkeypatch.setattr("redmine_cli.config.get_config_dir", lambda: config_dir)
    return config_dir


@pytest.fixture
def env_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set environment variables for config."""
    monkeypatch.setenv("REDMINE_URL", "http://redmine.env.test")
    monkeypatch.setenv("REDMINE_API_KEY", "envkey123")
