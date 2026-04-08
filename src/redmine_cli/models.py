"""Pydantic data models for Redmine API resources."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# --- Nested reference models ---


class NamedRef(BaseModel):
    """A named reference to another resource (project, tracker, user, etc.)."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str


class StatusRef(BaseModel):
    """Issue status reference."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str
    is_closed: bool = False


class ParentRef(BaseModel):
    """Parent issue reference."""

    id: int


class CustomField(BaseModel):
    """Custom field value."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str
    value: str | list[str] | None = None
    multiple: bool = False


class JournalDetail(BaseModel):
    """Detail of a journal entry change."""

    model_config = ConfigDict(populate_by_name=True)

    property: str
    name: str
    old_value: str | None = None
    new_value: str | None = None


class Journal(BaseModel):
    """Issue journal (comment/history entry)."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    user: NamedRef
    notes: str = ""
    created_on: datetime | None = None
    private_notes: bool = False
    details: list[JournalDetail] = Field(default_factory=list)


class Attachment(BaseModel):
    """File attachment."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    filename: str
    filesize: int
    content_type: str | None = None
    description: str | None = None
    content_url: str | None = None
    author: NamedRef | None = None
    created_on: datetime | None = None


class ChildRef(BaseModel):
    """Child issue reference."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    tracker: NamedRef | None = None
    subject: str | None = None


# --- Main resource models ---


class Issue(BaseModel):
    """Redmine issue."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    project: NamedRef
    tracker: NamedRef
    status: StatusRef
    priority: NamedRef
    author: NamedRef
    assigned_to: NamedRef | None = None
    parent: ParentRef | None = None
    subject: str
    description: str | None = None
    start_date: date | None = None
    due_date: date | None = None
    done_ratio: int = 0
    estimated_hours: float | None = None
    spent_hours: float = 0.0
    created_on: datetime | None = None
    updated_on: datetime | None = None
    closed_on: datetime | None = None
    custom_fields: list[CustomField] = Field(default_factory=list)
    journals: list[Journal] | None = None
    children: list[ChildRef] | None = None
    attachments: list[Attachment] | None = None


class Project(BaseModel):
    """Redmine project."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str
    identifier: str
    description: str | None = None
    status: int = 1
    is_public: bool = False
    parent: NamedRef | None = None
    created_on: datetime | None = None
    updated_on: datetime | None = None
    custom_fields: list[CustomField] = Field(default_factory=list)


class Membership(BaseModel):
    """Project membership."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    project: NamedRef | None = None
    user: NamedRef | None = None
    group: NamedRef | None = None
    roles: list[NamedRef] = Field(default_factory=list)


class User(BaseModel):
    """Redmine user."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    login: str | None = None
    firstname: str = ""
    lastname: str = ""
    mail: str | None = None
    api_key: str | None = None
    created_on: datetime | None = None
    last_login_on: datetime | None = None
    custom_fields: list[CustomField] = Field(default_factory=list)

    @property
    def full_name(self) -> str:
        return f"{self.lastname}{self.firstname}"


class TimeEntry(BaseModel):
    """Time entry."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    project: NamedRef
    issue: NamedRef | None = None
    user: NamedRef
    activity: NamedRef
    hours: float
    comments: str | None = None
    spent_on: date
    created_on: datetime | None = None
    updated_on: datetime | None = None
    custom_fields: list[CustomField] = Field(default_factory=list)


class Enumeration(BaseModel):
    """Enumeration (issue priorities, time entry activities, etc.)."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str
    is_default: bool = False
    active: bool = True


class Tracker(BaseModel):
    """Tracker type."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str
    is_in_chlog: bool = False
    is_in_roadmap: bool = False


# --- Request models ---


class IssueCreate(BaseModel):
    """Request body for creating an issue."""

    model_config = ConfigDict(populate_by_name=True)

    project_id: str | int
    tracker_id: int = 12
    subject: str
    description: str | None = None
    assigned_to_id: int | None = None
    parent_issue_id: int | None = None
    priority_id: int = 2
    status_id: int = 1
    start_date: date | None = None
    due_date: date | None = None
    estimated_hours: float | None = None
    custom_fields: list[dict[str, Any]] | None = None


class IssueUpdate(BaseModel):
    """Request body for updating an issue."""

    model_config = ConfigDict(populate_by_name=True)

    subject: str | None = None
    description: str | None = None
    assigned_to_id: int | None = None
    status_id: int | None = None
    done_ratio: int | None = None
    priority_id: int | None = None
    start_date: date | None = None
    due_date: date | None = None
    estimated_hours: float | None = None
    notes: str | None = None
    custom_fields: list[dict[str, Any]] | None = None


class TimeEntryCreate(BaseModel):
    """Request body for creating a time entry."""

    model_config = ConfigDict(populate_by_name=True)

    issue_id: int
    hours: float
    activity_id: int = 9
    comments: str | None = None
    spent_on: date | None = None
    custom_fields: list[dict[str, Any]] | None = None
