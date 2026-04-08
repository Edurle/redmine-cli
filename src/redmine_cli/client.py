"""Redmine REST API client."""

from __future__ import annotations

from typing import Any

import httpx
from rich.console import Console

from redmine_cli.config import ProfileConfig

err_console = Console(stderr=True)


class RedmineAPIError(Exception):
    """Error from the Redmine API."""

    def __init__(self, status_code: int, errors: list[str] | None = None, message: str = ""):
        self.status_code = status_code
        self.errors = errors or []
        if not message:
            message = f"API error {status_code}"
            if self.errors:
                message += ": " + "; ".join(self.errors)
        super().__init__(message)


class RedmineConnectionError(Exception):
    """Error connecting to the Redmine server."""


class RedmineClient:
    """Synchronous HTTP client for the Redmine REST API."""

    def __init__(self, config: ProfileConfig) -> None:
        self._config = config
        self._client = httpx.Client(
            base_url=config.url.rstrip("/"),
            headers={
                "X-Redmine-API-Key": config.api_key,
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        """Make an HTTP request and return the JSON response."""
        try:
            response = self._client.request(method, path, **kwargs)
        except httpx.ConnectError as e:
            raise RedmineConnectionError(
                f"Cannot connect to {self._config.url}. "
                f"Check the URL and network connectivity."
            ) from e
        except httpx.TimeoutException as e:
            raise RedmineConnectionError(
                f"Connection to {self._config.url} timed out."
            ) from e

        if response.status_code == 204:
            return {}

        if not response.is_success:
            errors: list[str] = []
            try:
                data = response.json()
                errors = data.get("errors", [])
                if isinstance(errors, list):
                    errors = [str(e) for e in errors]
            except Exception:
                pass
            raise RedmineAPIError(response.status_code, errors)

        return response.json()

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make a GET request."""
        return self._request("GET", path, params=params)

    def post(self, path: str, json_data: dict[str, Any]) -> dict[str, Any]:
        """Make a POST request."""
        return self._request("POST", path, json=json_data)

    def put(self, path: str, json_data: dict[str, Any]) -> dict[str, Any]:
        """Make a PUT request."""
        return self._request("PUT", path, json=json_data)

    def delete(self, path: str) -> None:
        """Make a DELETE request."""
        self._request("DELETE", path)

    def get_paginated(
        self,
        path: str,
        key: str,
        params: dict[str, Any] | None = None,
        limit: int = 25,
        offset: int = 0,
        all_pages: bool = False,
    ) -> tuple[list[dict[str, Any]], int]:
        """Fetch paginated collection resources.

        Args:
            path: API endpoint path (e.g., "/issues.json")
            key: JSON key for the items array (e.g., "issues")
            params: Additional query parameters
            limit: Items per page (max 100)
            offset: Starting offset
            all_pages: If True, fetch all pages

        Returns:
            Tuple of (items list, total count)
        """
        params = dict(params or {})
        params["limit"] = min(limit, 100)
        params["offset"] = offset

        data = self.get(path, params=params)
        items = data.get(key, [])
        total_count = data.get("total_count", len(items))

        if not all_pages or total_count <= len(items) + offset:
            return items, total_count

        # Fetch remaining pages
        all_items = list(items)
        current_offset = offset + len(items)
        max_items = 10000  # Safety limit

        while current_offset < total_count and current_offset < max_items:
            params["offset"] = current_offset
            params["limit"] = min(100, total_count - current_offset)
            data = self.get(path, params=params)
            page_items = data.get(key, [])
            if not page_items:
                break
            all_items.extend(page_items)
            current_offset += len(page_items)

        return all_items, total_count

    # --- Issues ---

    def list_issues(self, **filters: Any) -> tuple[list[dict[str, Any]], int]:
        """List issues with optional filters."""
        params: dict[str, Any] = {}
        for key, value in filters.items():
            if value is not None:
                params[key] = value
        return self.get_paginated("/issues.json", "issues", params=params)

    def get_issue(self, issue_id: int, include: str = "") -> dict[str, Any]:
        """Get a single issue with optional related data."""
        params: dict[str, Any] = {}
        if include:
            params["include"] = include
        data = self.get(f"/issues/{issue_id}.json", params=params)
        return data.get("issue", data)

    def create_issue(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new issue."""
        result = self.post("/issues.json", json_data={"issue": data})
        return result.get("issue", result)

    def update_issue(self, issue_id: int, data: dict[str, Any]) -> None:
        """Update an existing issue."""
        self.put(f"/issues/{issue_id}.json", json_data={"issue": data})

    def delete_issue(self, issue_id: int) -> None:
        """Delete an issue."""
        self.delete(f"/issues/{issue_id}.json")

    # --- Projects ---

    def list_projects(self, **params: Any) -> tuple[list[dict[str, Any]], int]:
        """List projects."""
        query: dict[str, Any] = {k: v for k, v in params.items() if v is not None}
        return self.get_paginated("/projects.json", "projects", params=query)

    def get_project(self, project_id: str | int) -> dict[str, Any]:
        """Get project details."""
        data = self.get(f"/projects/{project_id}.json")
        return data.get("project", data)

    def get_project_memberships(
        self, project_id: str | int, **params: Any
    ) -> tuple[list[dict[str, Any]], int]:
        """List project memberships."""
        query: dict[str, Any] = {k: v for k, v in params.items() if v is not None}
        return self.get_paginated(
            f"/projects/{project_id}/memberships.json", "memberships", params=query
        )

    # --- Users ---

    def get_current_user(self) -> dict[str, Any]:
        """Get current authenticated user info."""
        data = self.get("/users/current.json")
        return data.get("user", data)

    # --- Time Entries ---

    def list_time_entries(self, **params: Any) -> tuple[list[dict[str, Any]], int]:
        """List time entries."""
        query: dict[str, Any] = {k: v for k, v in params.items() if v is not None}
        return self.get_paginated("/time_entries.json", "time_entries", params=query)

    def create_time_entry(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a time entry."""
        result = self.post("/time_entries.json", json_data={"time_entry": data})
        return result.get("time_entry", result)

    # --- Enumerations ---

    def list_trackers(self) -> list[dict[str, Any]]:
        """List all trackers."""
        data = self.get("/trackers.json")
        return data.get("trackers", [])

    def list_issue_statuses(self) -> list[dict[str, Any]]:
        """List all issue statuses."""
        data = self.get("/issue_statuses.json")
        return data.get("issue_statuses", [])

    def list_time_entry_activities(self) -> list[dict[str, Any]]:
        """List time entry activities (enumerations)."""
        data = self.get("/enumerations/time_entry_activities.json")
        return data.get("time_entry_activities", [])

    def list_issue_priorities(self) -> list[dict[str, Any]]:
        """List issue priorities."""
        data = self.get("/enumerations/issue_priorities.json")
        return data.get("issue_priorities", [])

    # --- Utility ---

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> RedmineClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
