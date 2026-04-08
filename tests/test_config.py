"""Tests for config module."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.exceptions import Exit

from redmine_cli.config import load_config


class TestLoadConfig:
    """Test configuration loading with env var override."""

    def test_env_vars_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Environment variables take priority over config file."""
        monkeypatch.setenv("REDMINE_URL", "http://env.redmine.test")
        monkeypatch.setenv("REDMINE_API_KEY", "env_key_123")

        config = load_config()
        assert config.url == "http://env.redmine.test"
        assert config.api_key == "env_key_123"

    def test_config_file_loading(self, tmp_config: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Load config from TOML file when env vars are not set."""
        monkeypatch.delenv("REDMINE_URL", raising=False)
        monkeypatch.delenv("REDMINE_API_KEY", raising=False)

        config = load_config()
        assert config.url == "http://redmine.test"
        assert config.api_key == "testkey123"

    def test_missing_config_exits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Exit with error when no config file and no env vars."""
        monkeypatch.delenv("REDMINE_URL", raising=False)
        monkeypatch.delenv("REDMINE_API_KEY", raising=False)
        monkeypatch.setattr("redmine_cli.config.get_config_dir", lambda: Path("/nonexistent"))

        with pytest.raises(Exit) as exc_info:
            load_config()
        assert exc_info.value.exit_code == 1

    def test_missing_env_url_keeps_config(self, tmp_config: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """If only REDMINE_API_KEY is set (no URL), use config file."""
        monkeypatch.delenv("REDMINE_URL", raising=False)
        monkeypatch.setenv("REDMINE_API_KEY", "partial_env_key")

        config = load_config()
        assert config.url == "http://redmine.test"  # Falls back to file

    def test_profile_selection(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Select a specific profile from config."""
        config_dir = tmp_path / ".redmine-cli"
        config_dir.mkdir()
        config_file = config_dir / "config.toml"
        config_file.write_text(
            'default_profile = "work"\n\n'
            '[profiles.work]\n'
            'url = "http://work.redmine.test"\n'
            'api_key = "workkey"\n\n'
            '[profiles.personal]\n'
            'url = "http://personal.redmine.test"\n'
            'api_key = "personalkey"\n'
        )
        monkeypatch.delenv("REDMINE_URL", raising=False)
        monkeypatch.delenv("REDMINE_API_KEY", raising=False)
        monkeypatch.setattr("redmine_cli.config.get_config_dir", lambda: config_dir)

        # Default profile
        config = load_config()
        assert config.url == "http://work.redmine.test"

        # Explicit profile
        config = load_config("personal")
        assert config.url == "http://personal.redmine.test"

    def test_unknown_profile_exits(self, tmp_config: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Exit with error for unknown profile name."""
        monkeypatch.delenv("REDMINE_URL", raising=False)
        monkeypatch.delenv("REDMINE_API_KEY", raising=False)

        with pytest.raises(Exit) as exc_info:
            load_config("nonexistent")
        assert exc_info.value.exit_code == 1
