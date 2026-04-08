"""Tests for the Redmine API client."""

from __future__ import annotations


import httpx
import pytest

from redmine_cli.client import RedmineAPIError, RedmineClient, RedmineConnectionError
from redmine_cli.config import ProfileConfig


@pytest.fixture
def config() -> ProfileConfig:
    return ProfileConfig(url="http://redmine.test", api_key="testkey123")


@pytest.fixture
def mock_transport(config: ProfileConfig) -> tuple[RedmineClient, list[httpx.Request]]:
    """Create a client with a mock transport that records requests."""
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"_mock": True})

    transport = httpx.MockTransport(handler)
    client = RedmineClient(config)
    client._client = httpx.Client(
        transport=transport,
        base_url=config.url,
        headers={"X-Redmine-API-Key": config.api_key, "Content-Type": "application/json"},
    )
    return client, requests


class TestClientBasics:
    def test_api_key_header(self, mock_transport: tuple) -> None:
        client, requests = mock_transport
        client.get("/test.json")
        assert len(requests) == 1
        assert requests[0].headers["X-Redmine-API-Key"] == "testkey123"

    def test_delete_returns_empty(self, mock_transport: tuple) -> None:
        client, _ = mock_transport
        # 204 response
        transport_204 = httpx.MockTransport(lambda r: httpx.Response(204))
        client._client = httpx.Client(transport=transport_204, base_url="http://redmine.test")
        client.delete("/issues/1.json")  # Should not raise


class TestErrorHandling:
    def test_401_raises_api_error(self, config: ProfileConfig) -> None:
        transport = httpx.MockTransport(lambda r: httpx.Response(401))
        client = RedmineClient(config)
        client._client = httpx.Client(transport=transport, base_url=config.url)

        with pytest.raises(RedmineAPIError) as exc_info:
            client.get("/test.json")
        assert exc_info.value.status_code == 401

    def test_422_extracts_errors(self, config: ProfileConfig) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(422, json={"errors": ["Subject can't be blank", "Invalid date"]})

        transport = httpx.MockTransport(handler)
        client = RedmineClient(config)
        client._client = httpx.Client(transport=transport, base_url=config.url)

        with pytest.raises(RedmineAPIError) as exc_info:
            client.post("/issues.json", json_data={"issue": {}})
        assert "Subject can't be blank" in str(exc_info.value)

    def test_connection_error(self, config: ProfileConfig) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("Connection refused")

        transport = httpx.MockTransport(handler)
        client = RedmineClient(config)
        client._client = httpx.Client(transport=transport, base_url=config.url)

        with pytest.raises(RedmineConnectionError):
            client.get("/test.json")


class TestPagination:
    def test_single_page(self, config: ProfileConfig) -> None:
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(200, json={
                "issues": [{"id": 1}, {"id": 2}],
                "total_count": 2,
                "offset": 0,
                "limit": 25,
            })

        transport = httpx.MockTransport(handler)
        client = RedmineClient(config)
        client._client = httpx.Client(transport=transport, base_url=config.url)

        items, total = client.get_paginated("/issues.json", "issues")
        assert len(items) == 2
        assert total == 2
        assert call_count == 1

    def test_all_pages(self, config: ProfileConfig) -> None:
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            offset = int(request.url.params.get("offset", "0"))

            if offset == 0:
                return httpx.Response(200, json={
                    "issues": [{"id": i} for i in range(1, 26)],
                    "total_count": 30,
                    "offset": 0,
                    "limit": 25,
                })
            else:
                return httpx.Response(200, json={
                    "issues": [{"id": i} for i in range(26, 31)],
                    "total_count": 30,
                    "offset": 25,
                    "limit": 5,
                })

        transport = httpx.MockTransport(handler)
        client = RedmineClient(config)
        client._client = httpx.Client(transport=transport, base_url=config.url)

        items, total = client.get_paginated("/issues.json", "issues", all_pages=True)
        assert len(items) == 30
        assert total == 30
        assert call_count == 2
