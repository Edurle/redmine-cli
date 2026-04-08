"""Tests for Pydantic data models."""

from __future__ import annotations

from datetime import date, datetime


from redmine_cli.models import (
    Issue,
    IssueCreate,
    Journal,
    NamedRef,
    Project,
    TimeEntry,
    TimeEntryCreate,
    User,
)


class TestUser:
    def test_full_name(self, sample_user_json: dict) -> None:
        user = User(**sample_user_json)
        assert user.full_name == "UserTest"

    def test_optional_fields(self) -> None:
        user = User(id=1, firstname="A", lastname="B")
        assert user.login is None
        assert user.mail is None
        assert user.api_key is None


class TestIssue:
    def test_parse_issue(self, sample_issue_json: dict) -> None:
        issue = Issue(**sample_issue_json)
        assert issue.id == 1234
        assert issue.subject == "Test issue subject"
        assert issue.done_ratio == 30
        assert issue.assigned_to is not None
        assert issue.assigned_to.name == "User Test"

    def test_optional_assigned_to(self) -> None:
        data = {
            "id": 1,
            "project": {"id": 1, "name": "P"},
            "tracker": {"id": 1, "name": "T"},
            "status": {"id": 1, "name": "S"},
            "priority": {"id": 1, "name": "P"},
            "author": {"id": 1, "name": "A"},
            "subject": "Test",
        }
        issue = Issue(**data)
        assert issue.assigned_to is None


class TestProject:
    def test_parse_project(self, sample_project_json: dict) -> None:
        project = Project(**sample_project_json)
        assert project.identifier == "test-project"
        assert project.status == 1
        assert not project.is_public


class TestTimeEntry:
    def test_parse_time_entry(self, sample_time_entry_json: dict) -> None:
        entry = TimeEntry(**sample_time_entry_json)
        assert entry.hours == 2.5
        assert entry.spent_on == date(2026, 4, 7)


class TestJournal:
    def test_parse_journal(self) -> None:
        journal = Journal(
            id=1,
            user=NamedRef(id=1, name="Admin"),
            notes="Test note",
            created_on=datetime(2026, 4, 1, 12, 0),
        )
        assert journal.notes == "Test note"
        assert journal.details == []


class TestRequestModels:
    def test_issue_create_defaults(self) -> None:
        model = IssueCreate(project_id="test", subject="Sub")
        assert model.tracker_id == 12
        assert model.priority_id == 2
        assert model.status_id == 1

    def test_time_entry_create(self) -> None:
        model = TimeEntryCreate(issue_id=100, hours=2.5)
        assert model.activity_id == 9  # Default: development
        assert model.spent_on is None  # Defaults to today at CLI level
