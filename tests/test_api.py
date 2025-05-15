"""
Tests for the API wrapper module.
"""

import json
from collections.abc import Generator
from typing import Any
from unittest import mock

import httpx
import pytest
from pytest_httpx import HTTPXMock

from linear_cli import api


@pytest.fixture
def mock_config_get_token() -> Generator[mock.MagicMock, None, None]:
    """Mock config.get_token to return a test token."""
    with mock.patch("linear_cli.config.get_token") as mock_get_token:
        mock_get_token.return_value = "test-token"
        yield mock_get_token


@pytest.fixture
def user_response() -> dict[str, Any]:
    """Return a mock user response."""
    return {
        "data": {
            "viewer": {
                "id": "user-id-123",
                "name": "Test User",
                "email": "test@example.com",
                "displayName": "Test",
                "avatarUrl": "https://example.com/avatar.png",
                "active": True,
                "createdAt": "2023-01-01T00:00:00.000Z",
                "updatedAt": "2023-01-01T00:00:00.000Z",
            }
        }
    }


@pytest.fixture
def projects_response() -> dict[str, Any]:
    """Return a mock projects response."""
    return {
        "data": {
            "projects": {
                "nodes": [
                    {
                        "id": "project-id-1",
                        "name": "Project 1",
                        "description": "Description for Project 1",
                        "icon": "icon-1",
                        "color": "#FF0000",
                        "state": "started",
                        "createdAt": "2023-01-01T00:00:00.000Z",
                        "updatedAt": "2023-01-01T00:00:00.000Z",
                        "teamIds": ["team-id-1"],
                        "leadId": "user-id-123",
                        "memberIds": ["user-id-123", "user-id-456"],
                        "url": "https://linear.app/team/project/project-1",
                    },
                    {
                        "id": "project-id-2",
                        "name": "Project 2",
                        "description": None,
                        "icon": None,
                        "color": None,
                        "state": "backlog",
                        "createdAt": "2023-01-02T00:00:00.000Z",
                        "updatedAt": "2023-01-02T00:00:00.000Z",
                        "teamIds": ["team-id-1", "team-id-2"],
                        "leadId": None,
                        "memberIds": [],
                        "url": "https://linear.app/team/project/project-2",
                    },
                ],
                "pageInfo": {
                    "hasNextPage": False,
                    "endCursor": "cursor-123",
                },
            }
        }
    }


@pytest.fixture
def issues_response() -> dict[str, Any]:
    """Return a mock issues response."""
    return {
        "data": {
            "issues": {
                "nodes": [
                    {
                        "id": "issue-id-1",
                        "title": "Issue 1",
                        "description": "Description for Issue 1",
                        "priority": 1,
                        "state": {
                            "id": "state-id-1",
                            "name": "Todo",
                        },
                        "team": {
                            "id": "team-id-1",
                        },
                        "project": {
                            "id": "project-id-1",
                        },
                        "assignee": {
                            "id": "user-id-123",
                        },
                        "creator": {
                            "id": "user-id-123",
                        },
                        "createdAt": "2023-01-01T00:00:00.000Z",
                        "updatedAt": "2023-01-01T00:00:00.000Z",
                        "url": "https://linear.app/team/issue/issue-1",
                    },
                    {
                        "id": "issue-id-2",
                        "title": "Issue 2",
                        "description": None,
                        "priority": 0,
                        "state": {
                            "id": "state-id-2",
                            "name": "In Progress",
                        },
                        "team": {
                            "id": "team-id-1",
                        },
                        "project": None,
                        "assignee": None,
                        "creator": {
                            "id": "user-id-456",
                        },
                        "createdAt": "2023-01-02T00:00:00.000Z",
                        "updatedAt": "2023-01-02T00:00:00.000Z",
                        "url": "https://linear.app/team/issue/issue-2",
                    },
                ],
                "pageInfo": {
                    "hasNextPage": False,
                    "endCursor": "cursor-123",
                },
            }
        }
    }


@pytest.fixture
def project_team_response() -> dict[str, Any]:
    """Return a mock project team response."""
    return {
        "data": {
            "project": {
                "teamIds": ["team-id-1"],
            }
        }
    }


@pytest.fixture
def create_issue_response() -> dict[str, Any]:
    """Return a mock create issue response."""
    return {
        "data": {
            "issueCreate": {
                "success": True,
                "issue": {
                    "id": "issue-id-3",
                    "title": "New Issue",
                    "description": "Description for New Issue",
                    "priority": 0,
                    "state": {
                        "id": "state-id-1",
                        "name": "Todo",
                    },
                    "team": {
                        "id": "team-id-1",
                    },
                    "project": {
                        "id": "project-id-1",
                    },
                    "assignee": None,
                    "creator": {
                        "id": "user-id-123",
                    },
                    "createdAt": "2023-01-03T00:00:00.000Z",
                    "updatedAt": "2023-01-03T00:00:00.000Z",
                    "url": "https://linear.app/team/issue/issue-3",
                },
            }
        }
    }


def test_authenticate_async_success(httpx_mock: HTTPXMock) -> None:
    """Test successful authentication."""
    # Mock the authentication request
    httpx_mock.add_response(
        url="https://api.linear.app/oauth/token",
        method="POST",
        json={
            "access_token": "test-token",
            "token_type": "Bearer",
            "expires_in": 3600,
        },
    )

    # Mock the user info request
    httpx_mock.add_response(
        url="https://api.linear.app/graphql",
        method="POST",
        json={
            "data": {
                "viewer": {
                    "id": "user-id-123",
                    "name": "Test User",
                    "email": "test@example.com",
                    "displayName": "Test",
                    "avatarUrl": "https://example.com/avatar.png",
                    "createdAt": "2023-01-01T00:00:00.000Z",
                    "updatedAt": "2023-01-01T00:00:00.000Z",
                }
            }
        },
    )

    # Call the authenticate function
    auth_response = api.authenticate("test@example.com", "password123")

    # Verify the result
    assert auth_response.access_token == "test-token"  # noqa: S105
    assert auth_response.user.id == "user-id-123"
    assert auth_response.user.name == "Test User"
    assert auth_response.user.email == "test@example.com"


def test_authenticate_async_failure(httpx_mock: HTTPXMock) -> None:
    """Test authentication failure."""
    # Mock the authentication request to fail
    httpx_mock.add_response(
        url="https://api.linear.app/oauth/token",
        method="POST",
        status_code=401,
        json={"error": "invalid_grant", "error_description": "Invalid credentials"},
    )

    # Call the authenticate function and expect an exception
    with pytest.raises(api.AuthenticationError):
        api.authenticate("test@example.com", "wrong-password")


def test_get_me_async_success(
    httpx_mock: HTTPXMock, user_response: dict[str, Any], mock_config_get_token: mock.MagicMock  # noqa: ARG001
) -> None:
    """Test getting the current user successfully."""
    # Mock the user info request
    httpx_mock.add_response(
        url="https://api.linear.app/graphql",
        method="POST",
        json=user_response,
    )

    # Call the get_me function
    user = api.get_me()

    # Verify the result
    assert user.id == "user-id-123"
    assert user.name == "Test User"
    assert user.email == "test@example.com"
    assert user.display_name == "Test"
    assert user.avatar_url == "https://example.com/avatar.png"
    assert user.active is True


def test_get_me_async_no_token() -> None:
    """Test getting the current user with no token."""
    # Mock config.get_token to return None
    # Use a single with statement with multiple contexts
    with mock.patch("linear_cli.config.get_token", return_value=None), pytest.raises(api.AuthenticationError):
        # Call the get_me function and expect an exception
        api.get_me()


def test_get_me_async_api_error(
    httpx_mock: HTTPXMock, mock_config_get_token: mock.MagicMock
) -> None:  # noqa: ARG001
    """Test getting the current user with an API error."""
    # Mock the user info request to fail with a GraphQL error
    httpx_mock.add_response(
        url="https://api.linear.app/graphql",
        method="POST",
        json={"errors": [{"message": "Something went wrong"}]},
    )

    # Call the get_me function and expect an exception
    with pytest.raises(api.LinearAPIError):
        api.get_me()


def test_list_projects_async_success(
    httpx_mock: HTTPXMock, projects_response: dict[str, Any], mock_config_get_token: mock.MagicMock  # noqa: ARG001
) -> None:
    """Test listing projects successfully."""
    # Mock the viewer request that's made first
    httpx_mock.add_response(
        url="https://api.linear.app/graphql",
        method="POST",
        json={
            "data": {
                "viewer": {
                    "id": "user-id-123",
                    "name": "Test User",
                    "email": "test@example.com"
                }
            }
        },
    )

    # Mock the projects request
    httpx_mock.add_response(
        url="https://api.linear.app/graphql",
        method="POST",
        json=projects_response,
    )

    # Call the list_projects function
    projects = api.list_projects()

    # Verify the result
    assert len(projects.nodes) == 2
    assert projects.nodes[0].id == "project-id-1"
    assert projects.nodes[0].name == "Project 1"
    assert projects.nodes[0].description == "Description for Project 1"
    assert projects.nodes[1].id == "project-id-2"
    assert projects.nodes[1].name == "Project 2"
    assert projects.nodes[1].description is None


def test_list_projects_async_api_error(
    httpx_mock: HTTPXMock, mock_config_get_token: mock.MagicMock
) -> None:  # noqa: ARG001
    """Test listing projects with an API error."""
    # Mock the projects request to fail with a GraphQL error
    httpx_mock.add_response(
        url="https://api.linear.app/graphql",
        method="POST",
        json={"errors": [{"message": "Something went wrong"}]},
    )

    # Call the list_projects function and expect an exception
    with pytest.raises(api.LinearAPIError):
        api.list_projects()


def test_list_issues_async_success(
    httpx_mock: HTTPXMock, issues_response: dict[str, Any], mock_config_get_token: mock.MagicMock  # noqa: ARG001
) -> None:
    """Test listing issues successfully."""
    # Mock the issues request
    httpx_mock.add_response(
        url="https://api.linear.app/graphql",
        method="POST",
        json=issues_response,
    )

    # Call the list_issues function
    issues = api.list_issues()

    # Verify the result
    assert len(issues.nodes) == 2
    assert issues.nodes[0].id == "issue-id-1"
    assert issues.nodes[0].title == "Issue 1"
    assert issues.nodes[0].description == "Description for Issue 1"
    assert issues.nodes[0].priority == 1
    assert issues.nodes[0].state_id == "state-id-1"
    assert issues.nodes[0].state_name == "Todo"
    assert issues.nodes[0].team_id == "team-id-1"
    assert issues.nodes[0].project_id == "project-id-1"
    assert issues.nodes[0].assignee_id == "user-id-123"
    assert issues.nodes[0].creator_id == "user-id-123"

    assert issues.nodes[1].id == "issue-id-2"
    assert issues.nodes[1].title == "Issue 2"
    assert issues.nodes[1].description is None
    assert issues.nodes[1].priority == 0
    assert issues.nodes[1].state_id == "state-id-2"
    assert issues.nodes[1].state_name == "In Progress"
    assert issues.nodes[1].team_id == "team-id-1"
    assert issues.nodes[1].project_id is None
    assert issues.nodes[1].assignee_id is None
    assert issues.nodes[1].creator_id == "user-id-456"


def test_list_issues_async_with_project_id(
    httpx_mock: HTTPXMock, issues_response: dict[str, Any], mock_config_get_token: mock.MagicMock  # noqa: ARG001
) -> None:
    """Test listing issues with a project ID filter."""
    # Mock all GraphQL requests
    httpx_mock.add_response(
        url="https://api.linear.app/graphql",
        method="POST",
        json={"data": {"project": {"id": "project-id-1"}}},
    )

    httpx_mock.add_response(
        url="https://api.linear.app/graphql",
        method="POST",
        json=issues_response,
    )

    # Call the list_issues function with a project ID
    issues = api.list_issues(project_id="project-id-1")

    # Verify the result
    assert len(issues.nodes) == 2

    # Check that the request was made with the correct filter
    requests = httpx_mock.get_requests(url="https://api.linear.app/graphql", method="POST")
    assert requests, "No requests were made"
    # Get the last request which should be the one with the filter
    request = requests[-1]
    request_json = json.loads(request.content)
    assert request_json["variables"] == {"filter": {"project": {"id": {"eq": "project-id-1"}}}}


def test_list_issues_async_api_error(
    httpx_mock: HTTPXMock, mock_config_get_token: mock.MagicMock
) -> None:  # noqa: ARG001
    """Test listing issues with an API error."""
    # Mock the issues request to fail with a GraphQL error
    httpx_mock.add_response(
        url="https://api.linear.app/graphql",
        method="POST",
        json={"errors": [{"message": "Something went wrong"}]},
    )

    # Call the list_issues function and expect an exception
    with pytest.raises(api.LinearAPIError):
        api.list_issues()


def test_create_issue_async_success(
    httpx_mock: HTTPXMock,
    project_team_response: dict[str, Any],  # noqa: ARG001
    create_issue_response: dict[str, Any],
    mock_config_get_token: mock.MagicMock,  # noqa: ARG001
) -> None:
    """Test creating an issue successfully."""
    # Mock all GraphQL requests
    httpx_mock.add_response(
        url="https://api.linear.app/graphql",
        method="POST",
        json={"data": {"project": {"id": "project-id-1", "teamIds": ["team-id-1"]}}},
    )

    httpx_mock.add_response(
        url="https://api.linear.app/graphql",
        method="POST",
        json=create_issue_response,
    )

    # Call the create_issue function
    issue = api.create_issue(
        title="New Issue",
        description="Description for New Issue",
        project_id="project-id-1",
    )

    # Verify the result
    assert issue.id == "issue-id-3"
    assert issue.title == "New Issue"
    assert issue.description == "Description for New Issue"
    assert issue.state_id == "state-id-1"
    assert issue.state_name == "Todo"
    assert issue.team_id == "team-id-1"
    assert issue.project_id == "project-id-1"
    assert issue.creator_id == "user-id-123"


def test_create_issue_async_with_team_id(
    httpx_mock: HTTPXMock,
    create_issue_response: dict[str, Any],
    mock_config_get_token: mock.MagicMock,  # noqa: ARG001
) -> None:
    """Test creating an issue with a team ID."""
    # Mock all GraphQL requests
    httpx_mock.add_response(
        url="https://api.linear.app/graphql",
        method="POST",
        json={"data": {"project": {"id": "project-id-1"}}},
    )

    httpx_mock.add_response(
        url="https://api.linear.app/graphql",
        method="POST",
        json=create_issue_response,
    )

    # Call the create_issue function with a team ID
    issue = api.create_issue(
        title="New Issue",
        description="Description for New Issue",
        project_id="project-id-1",
        team_id="team-id-1",
    )

    # Verify the result
    assert issue.id == "issue-id-3"
    assert issue.title == "New Issue"
    assert issue.team_id == "team-id-1"
    assert issue.project_id == "project-id-1"

    # Check that the request was made with the correct input
    requests = httpx_mock.get_requests(url="https://api.linear.app/graphql", method="POST")
    assert requests, "No requests were made"
    # Get the last request which should be the one with the create issue mutation
    request = requests[-1]
    request_json = json.loads(request.content)
    assert request_json["variables"]["input"]["teamId"] == "team-id-1"
    assert request_json["variables"]["input"]["projectId"] == "project-id-1"


@pytest.mark.httpx_mock(assert_all_requests_were_expected=False)
def test_create_issue_async_multiple_teams_error(
    httpx_mock: HTTPXMock,
    mock_config_get_token: mock.MagicMock,  # noqa: ARG001
) -> None:
    """Test creating an issue with a project that belongs to multiple teams."""
    # Mock all GraphQL requests
    httpx_mock.add_response(
        url="https://api.linear.app/graphql",
        method="POST",
        json={"data": {"project": {"id": "project-id-1", "teamIds": ["team-id-1", "team-id-2"]}}},
    )

    # Call the create_issue function and expect an exception
    with pytest.raises(api.LinearAPIError):
        api.create_issue(
            title="New Issue",
            description="Description for New Issue",
            project_id="project-id-1",
        )


def test_create_issue_async_api_error(
    httpx_mock: HTTPXMock, mock_config_get_token: mock.MagicMock  # noqa: ARG001
) -> None:
    """Test creating an issue with an API error."""
    # Mock all GraphQL requests
    httpx_mock.add_response(
        url="https://api.linear.app/graphql",
        method="POST",
        json={"data": {"project": {"id": "project-id-1", "teamIds": ["team-id-1"]}}},
    )

    httpx_mock.add_response(
        url="https://api.linear.app/graphql",
        method="POST",
        json={"errors": [{"message": "Something went wrong"}]},
    )

    # Call the create_issue function and expect an exception
    with pytest.raises(api.LinearAPIError):
        api.create_issue(
            title="New Issue",
            description="Description for New Issue",
            project_id="project-id-1",
        )


def test_execute_query_async_network_error(httpx_mock: HTTPXMock) -> None:
    """Test executing a query with a network error."""
    # Mock a network error
    httpx_mock.add_exception(
        url="https://api.linear.app/graphql",
        method="POST",
        exception=httpx.RequestError("Connection error"),
    )

    # Call the _execute_query_async function and expect an exception
    with pytest.raises(api.NetworkError):
        api._execute_query("query { viewer { id } }")
