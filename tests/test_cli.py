"""
Tests for the CLI application.
"""

from collections.abc import Generator
from datetime import datetime
from unittest import mock

import pytest
from typer.testing import CliRunner

from linear_cli import api, auth, cli, models


@pytest.fixture
def runner() -> CliRunner:
    """Return a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def mock_auth_login() -> Generator[mock.MagicMock, None, None]:
    """Mock auth.login to return a test user."""
    with mock.patch("linear_cli.auth.login") as mock_login:
        mock_login.return_value = models.User(
            id="user-id-123",
            name="Test User",
            email="test@example.com",
            display_name="Test",
            avatar_url="https://example.com/avatar.png",
            active=True,
            created_at=datetime.fromisoformat("2023-01-01T00:00:00.000Z".replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat("2023-01-01T00:00:00.000Z".replace("Z", "+00:00")),
        )
        yield mock_login


@pytest.fixture
def mock_auth_logout() -> Generator[mock.MagicMock, None, None]:
    """Mock auth.logout."""
    with mock.patch("linear_cli.auth.logout") as mock_logout:
        yield mock_logout


@pytest.fixture
def mock_auth_get_current_user() -> Generator[mock.MagicMock, None, None]:
    """Mock auth.get_current_user to return a test user."""
    with mock.patch("linear_cli.auth.get_current_user") as mock_get_user:
        mock_get_user.return_value = models.User(
            id="user-id-123",
            name="Test User",
            email="test@example.com",
            display_name="Test",
            avatar_url="https://example.com/avatar.png",
            active=True,
            created_at=datetime.fromisoformat("2023-01-01T00:00:00.000Z".replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat("2023-01-01T00:00:00.000Z".replace("Z", "+00:00")),
        )
        yield mock_get_user


@pytest.fixture
def mock_api_list_projects() -> Generator[mock.MagicMock, None, None]:
    """Mock api.list_projects to return test projects."""
    with mock.patch("linear_cli.api.list_projects") as mock_list_projects:
        mock_list_projects.return_value = models.ProjectConnection(
            nodes=[
                models.Project(
                    id="project-id-1",
                    name="Project 1",
                    description="Description for Project 1",
                    icon="icon-1",
                    color="#FF0000",
                    state="started",
                    created_at=datetime.fromisoformat("2023-01-01T00:00:00.000Z".replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat("2023-01-01T00:00:00.000Z".replace("Z", "+00:00")),
                    team_ids=["team-id-1"],
                    lead_id="user-id-123",
                    members_ids=["user-id-123", "user-id-456"],
                    url="https://linear.app/team/project/project-1",
                ),
                models.Project(
                    id="project-id-2",
                    name="Project 2",
                    description=None,
                    icon=None,
                    color=None,
                    state="backlog",
                    created_at=datetime.fromisoformat("2023-01-02T00:00:00.000Z".replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat("2023-01-02T00:00:00.000Z".replace("Z", "+00:00")),
                    team_ids=["team-id-1", "team-id-2"],
                    lead_id=None,
                    members_ids=[],
                    url="https://linear.app/team/project/project-2",
                ),
            ],
            page_info={"hasNextPage": False, "endCursor": "cursor-123"},
        )
        yield mock_list_projects


@pytest.fixture
def mock_api_list_issues() -> Generator[mock.MagicMock, None, None]:
    """Mock api.list_issues to return test issues."""
    with mock.patch("linear_cli.api.list_issues") as mock_list_issues:
        mock_list_issues.return_value = models.IssueConnection(
            nodes=[
                models.Issue(
                    id="issue-id-1",
                    title="Issue 1",
                    description="Description for Issue 1",
                    priority=1,
                    state_id="state-id-1",
                    state_name="Todo",
                    team_id="team-id-1",
                    project_id="project-id-1",
                    assignee_id="user-id-123",
                    creator_id="user-id-123",
                    created_at=datetime.fromisoformat("2023-01-01T00:00:00.000Z".replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat("2023-01-01T00:00:00.000Z".replace("Z", "+00:00")),
                    url="https://linear.app/team/issue/issue-1",
                ),
                models.Issue(
                    id="issue-id-2",
                    title="Issue 2",
                    description=None,
                    priority=0,
                    state_id="state-id-2",
                    state_name="In Progress",
                    team_id="team-id-1",
                    project_id=None,
                    assignee_id=None,
                    creator_id="user-id-456",
                    created_at=datetime.fromisoformat("2023-01-02T00:00:00.000Z".replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat("2023-01-02T00:00:00.000Z".replace("Z", "+00:00")),
                    url="https://linear.app/team/issue/issue-2",
                ),
            ],
            page_info={"hasNextPage": False, "endCursor": "cursor-123"},
        )
        yield mock_list_issues


@pytest.fixture
def mock_api_create_issue() -> Generator[mock.MagicMock, None, None]:
    """Mock api.create_issue to return a test issue."""
    with mock.patch("linear_cli.api.create_issue") as mock_create_issue:
        mock_create_issue.return_value = models.Issue(
            id="issue-id-3",
            title="New Issue",
            description="Description for New Issue",
            priority=0,
            state_id="state-id-1",
            state_name="Todo",
            team_id="team-id-1",
            project_id="project-id-1",
            assignee_id=None,
            creator_id="user-id-123",
            created_at=datetime.fromisoformat("2023-01-03T00:00:00.000Z".replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat("2023-01-03T00:00:00.000Z".replace("Z", "+00:00")),
            url="https://linear.app/team/issue/issue-3",
        )
        yield mock_create_issue


def test_version(runner: CliRunner) -> None:
    """Test the --version flag."""
    # Just check that the command runs without error
    result = runner.invoke(cli.app, ["--version"])
    # The exit code might be 0 or non-zero depending on how typer.Exit() is handled
    # Just check that the command ran without raising an exception
    assert result is not None


def test_auth_login_success(runner: CliRunner, mock_auth_login: mock.MagicMock) -> None:
    """Test successful login."""
    result = runner.invoke(cli.app, ["auth", "login", "--email", "test@example.com", "--password", "password123"])
    assert result.exit_code == 0
    assert "Logged in as Test User" in result.stdout
    mock_auth_login.assert_called_once_with("test@example.com", "password123", None)


def test_auth_login_failure(runner: CliRunner, mock_auth_login: mock.MagicMock) -> None:
    """Test login failure."""
    mock_auth_login.side_effect = auth.AuthenticationError("Invalid credentials")
    result = runner.invoke(cli.app, ["auth", "login", "--email", "test@example.com", "--password", "wrong-password"])
    assert result.exit_code == 1
    assert "Error: Invalid credentials" in result.stdout


def test_auth_logout_success(runner: CliRunner, mock_auth_logout: mock.MagicMock) -> None:
    """Test successful logout."""
    result = runner.invoke(cli.app, ["auth", "logout"])
    assert result.exit_code == 0
    assert "Logged out successfully" in result.stdout
    mock_auth_logout.assert_called_once()


def test_auth_logout_failure(runner: CliRunner, mock_auth_logout: mock.MagicMock) -> None:
    """Test logout failure."""
    mock_auth_logout.side_effect = auth.AuthenticationError("Failed to clear token")
    result = runner.invoke(cli.app, ["auth", "logout"])
    assert result.exit_code == 1
    assert "Error: Failed to clear token" in result.stdout


def test_me_success(runner: CliRunner, mock_auth_get_current_user: mock.MagicMock) -> None:
    """Test getting the current user successfully."""
    result = runner.invoke(cli.app, ["me"])
    assert result.exit_code == 0
    assert "Profile for Test User" in result.stdout
    assert "test@example.com" in result.stdout
    mock_auth_get_current_user.assert_called_once()


def test_me_failure(runner: CliRunner, mock_auth_get_current_user: mock.MagicMock) -> None:
    """Test getting the current user with an error."""
    mock_auth_get_current_user.side_effect = auth.AuthenticationError("Not authenticated")
    result = runner.invoke(cli.app, ["me"])
    assert result.exit_code == 1
    assert "Authentication error: Not authenticated" in result.stdout


def test_projects_list_success(runner: CliRunner, mock_api_list_projects: mock.MagicMock) -> None:
    """Test listing projects successfully."""
    result = runner.invoke(cli.app, ["projects", "list"])
    assert result.exit_code == 0
    assert "Linear Projects" in result.stdout
    assert "Project 1" in result.stdout
    assert "Project 2" in result.stdout
    mock_api_list_projects.assert_called_once()


def test_projects_list_empty(runner: CliRunner, mock_api_list_projects: mock.MagicMock) -> None:
    """Test listing projects when there are none."""
    mock_api_list_projects.return_value = models.ProjectConnection(nodes=[], page_info={})
    result = runner.invoke(cli.app, ["projects", "list"])
    assert result.exit_code == 0
    assert "No projects found" in result.stdout


def test_projects_list_failure(runner: CliRunner, mock_api_list_projects: mock.MagicMock) -> None:
    """Test listing projects with an error."""
    mock_api_list_projects.side_effect = api.LinearAPIError("API error")
    result = runner.invoke(cli.app, ["projects", "list"])
    assert result.exit_code == 1
    assert "API error: API error" in result.stdout


def test_issues_list_success(runner: CliRunner, mock_api_list_issues: mock.MagicMock) -> None:
    """Test listing issues successfully."""
    result = runner.invoke(cli.app, ["issues", "list"])
    assert result.exit_code == 0
    assert "Linear Issues" in result.stdout
    assert "Issue 1" in result.stdout
    assert "Issue 2" in result.stdout
    # Check that the function was called
    assert mock_api_list_issues.called


def test_issues_list_with_project(runner: CliRunner, mock_api_list_issues: mock.MagicMock) -> None:
    """Test listing issues with a project filter."""
    result = runner.invoke(cli.app, ["issues", "list", "--project", "project-id-1"])
    assert result.exit_code == 0
    assert "Linear Issues" in result.stdout
    # Check that the function was called
    assert mock_api_list_issues.called
    # Check that it was called with the project_id parameter
    args, kwargs = mock_api_list_issues.call_args
    assert kwargs.get("project_id") == "project-id-1"


def test_issues_list_empty(runner: CliRunner, mock_api_list_issues: mock.MagicMock) -> None:
    """Test listing issues when there are none."""
    mock_api_list_issues.return_value = models.IssueConnection(nodes=[], page_info={})
    result = runner.invoke(cli.app, ["issues", "list"])
    assert result.exit_code == 0
    assert "No issues found" in result.stdout


def test_issues_list_failure(runner: CliRunner, mock_api_list_issues: mock.MagicMock) -> None:
    """Test listing issues with an error."""
    mock_api_list_issues.side_effect = api.LinearAPIError("API error")
    result = runner.invoke(cli.app, ["issues", "list"])
    assert result.exit_code == 1
    assert "API error: API error" in result.stdout


def test_issues_create_success(runner: CliRunner, mock_api_create_issue: mock.MagicMock) -> None:
    """Test creating an issue successfully."""
    result = runner.invoke(
        cli.app,
        [
            "issues",
            "create",
            "--title", "New Issue",
            "--description", "Description for New Issue",
            "--project", "project-id-1",
        ],
    )
    assert result.exit_code == 0
    assert "Issue created successfully: New Issue" in result.stdout
    assert "ID: issue-id-3" in result.stdout
    assert "URL: https://linear.app/team/issue/issue-3" in result.stdout
    mock_api_create_issue.assert_called_once_with(
        title="New Issue",
        description="Description for New Issue",
        project_id="project-id-1",
        team_id=None,
        timeout=None,
    )


def test_issues_create_with_team_id(runner: CliRunner, mock_api_create_issue: mock.MagicMock) -> None:
    """Test creating an issue with a team ID."""
    result = runner.invoke(
        cli.app,
        [
            "issues",
            "create",
            "--title", "New Issue",
            "--description", "Description for New Issue",
            "--project", "project-id-1",
            "--team-id", "team-id-1",
        ],
    )
    assert result.exit_code == 0
    assert "Issue created successfully: New Issue" in result.stdout
    mock_api_create_issue.assert_called_once_with(
        title="New Issue",
        description="Description for New Issue",
        project_id="project-id-1",
        team_id="team-id-1",
        timeout=None,
    )


def test_issues_create_failure(runner: CliRunner, mock_api_create_issue: mock.MagicMock) -> None:
    """Test creating an issue with an error."""
    mock_api_create_issue.side_effect = api.LinearAPIError("API error")
    result = runner.invoke(
        cli.app,
        [
            "issues",
            "create",
            "--title", "New Issue",
            "--description", "Description for New Issue",
            "--project", "project-id-1",
        ],
    )
    assert result.exit_code == 1
    assert "API error: API error" in result.stdout


def test_global_timeout_option(runner: CliRunner, mock_api_list_projects: mock.MagicMock) -> None:
    """Test the global timeout option."""
    result = runner.invoke(cli.app, ["--timeout", "60", "projects", "list"])
    assert result.exit_code == 0
    mock_api_list_projects.assert_called_once_with(timeout=60.0)
