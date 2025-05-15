"""
Tests for the authentication module.
"""

from collections.abc import Generator
from typing import Any
from unittest import mock

import httpx
import pytest
from pytest_httpx import HTTPXMock

from linear_cli import auth


@pytest.fixture
def mock_config_get_token() -> Generator[mock.MagicMock, None, None]:
    """Mock config.get_token to return a test token."""
    with mock.patch("linear_cli.config.get_token") as mock_get_token:
        mock_get_token.return_value = "test-token"
        yield mock_get_token


@pytest.fixture
def mock_config_save_token() -> Generator[mock.MagicMock, None, None]:
    """Mock config.save_token."""
    with mock.patch("linear_cli.config.save_token") as mock_save_token:
        yield mock_save_token


@pytest.fixture
def mock_config_clear_token() -> Generator[mock.MagicMock, None, None]:
    """Mock config.clear_token."""
    with mock.patch("linear_cli.config.clear_token") as mock_clear_token:
        yield mock_clear_token


@pytest.fixture
def mock_get_credentials() -> Generator[mock.MagicMock, None, None]:
    """Mock _get_credentials to return test credentials."""
    with mock.patch("linear_cli.auth._get_credentials") as mock_get_creds:
        mock_get_creds.return_value = ("test@example.com", "password123")
        yield mock_get_creds


@pytest.fixture
def auth_response() -> dict[str, Any]:
    """Return a mock authentication response."""
    return {
        "access_token": "test-token",
        "token_type": "Bearer",
        "expires_in": 3600,
    }


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
                "createdAt": "2023-01-01T00:00:00.000Z",
                "updatedAt": "2023-01-01T00:00:00.000Z",
                "active": True,
            }
        }
    }


def test_login_success(
    httpx_mock: HTTPXMock,
    mock_get_credentials: mock.MagicMock,  # noqa: ARG001
    mock_config_save_token: mock.MagicMock,
    auth_response: dict[str, Any],
    user_response: dict[str, Any],
) -> None:
    """Test successful login."""
    # Mock the authentication request
    httpx_mock.add_response(
        url="https://api.linear.app/oauth/token",
        method="POST",
        json=auth_response,
    )

    # Mock the user info request
    httpx_mock.add_response(
        url="https://api.linear.app/graphql",
        method="POST",
        json=user_response,
    )

    # Call the login function
    user = auth.login()

    # Verify the result
    assert user.id == "user-id-123"
    assert user.name == "Test User"
    assert user.email == "test@example.com"

    # Verify the token was saved
    mock_config_save_token.assert_called_once_with("test-token")


def test_login_auth_failure(httpx_mock: HTTPXMock, mock_get_credentials: mock.MagicMock) -> None:  # noqa: ARG001
    """Test login with authentication failure."""
    # Mock the authentication request to fail
    httpx_mock.add_response(
        url="https://api.linear.app/oauth/token",
        method="POST",
        status_code=401,
        json={"error": "invalid_grant", "error_description": "Invalid credentials"},
    )

    # Call the login function and expect an exception
    with pytest.raises(auth.AuthenticationError):
        auth.login()


def test_login_network_error(httpx_mock: HTTPXMock, mock_get_credentials: mock.MagicMock) -> None:  # noqa: ARG001
    """Test login with network error."""
    # Mock a network error
    httpx_mock.add_exception(
        url="https://api.linear.app/oauth/token",
        method="POST",
        exception=httpx.RequestError("Connection error"),
    )

    # Call the login function and expect an exception
    with pytest.raises(auth.AuthenticationError):
        auth.login()


def test_logout_success(mock_config_clear_token: mock.MagicMock) -> None:
    """Test successful logout."""
    # Call the logout function
    auth.logout()

    # Verify the token was cleared
    mock_config_clear_token.assert_called_once()


def test_logout_failure(mock_config_clear_token: mock.MagicMock) -> None:
    """Test logout with an error."""
    # Mock clear_token to raise an exception
    mock_config_clear_token.side_effect = Exception("Failed to clear token")

    # Call the logout function and expect an exception
    with pytest.raises(auth.AuthenticationError):
        auth.logout()


def test_get_current_user_success(
    httpx_mock: HTTPXMock, mock_config_get_token: mock.MagicMock, user_response: dict[str, Any]
) -> None:  # noqa: ARG001
    """Test getting the current user successfully."""
    # Mock the user info request
    httpx_mock.add_response(
        url="https://api.linear.app/graphql",
        method="POST",
        json=user_response,
    )

    # Call the get_current_user function
    user = auth.get_current_user()

    # Verify the result
    assert user.id == "user-id-123"
    assert user.name == "Test User"
    assert user.email == "test@example.com"


def test_get_current_user_not_authenticated(mock_config_get_token: mock.MagicMock) -> None:
    """Test getting the current user when not authenticated."""
    # Mock get_token to return None
    mock_config_get_token.return_value = None

    # Call the get_current_user function and expect an exception
    with pytest.raises(auth.AuthenticationError):
        auth.get_current_user()


def test_get_current_user_auth_failure(
    httpx_mock: HTTPXMock, mock_config_get_token: mock.MagicMock, mock_config_clear_token: mock.MagicMock
) -> None:
    """Test getting the current user with an authentication failure."""
    # Mock the user info request to fail with 401
    httpx_mock.add_response(
        url="https://api.linear.app/graphql",
        method="POST",
        status_code=401,
        json={"errors": [{"message": "Unauthorized"}]},
    )

    # Call the get_current_user function and expect an exception
    with pytest.raises(auth.AuthenticationError):
        auth.get_current_user()

    # Verify the token was cleared
    mock_config_clear_token.assert_called_once()


def test_get_current_user_api_error(httpx_mock: HTTPXMock, mock_config_get_token: mock.MagicMock) -> None:
    """Test getting the current user with an API error."""
    # Mock the user info request to fail with a GraphQL error
    httpx_mock.add_response(
        url="https://api.linear.app/graphql",
        method="POST",
        json={"errors": [{"message": "Something went wrong"}]},
    )

    # Call the get_current_user function and expect an exception
    with pytest.raises(auth.AuthenticationError):
        auth.get_current_user()


def test_is_authenticated_true(mock_config_get_token: mock.MagicMock) -> None:
    """Test is_authenticated when authenticated."""
    # Call the is_authenticated function
    result = auth.is_authenticated()

    # Verify the result
    assert result is True


def test_is_authenticated_false(mock_config_get_token: mock.MagicMock) -> None:
    """Test is_authenticated when not authenticated."""
    # Mock get_token to return None
    mock_config_get_token.return_value = None

    # Call the is_authenticated function
    result = auth.is_authenticated()

    # Verify the result
    assert result is False


def test_get_credentials_with_values() -> None:
    """Test _get_credentials with provided values."""
    # Call the _get_credentials function with values
    email, password = auth._get_credentials("test@example.com", "password123")

    # Verify the result
    assert email == "test@example.com"
    assert password == "password123"


def test_get_credentials_with_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _get_credentials with prompting."""
    # Mock typer.prompt and getpass.getpass
    monkeypatch.setattr("typer.prompt", lambda x: "test@example.com")
    monkeypatch.setattr("getpass.getpass", lambda x: "password123")

    # Call the _get_credentials function without values
    email, password = auth._get_credentials()

    # Verify the result
    assert email == "test@example.com"
    assert password == "password123"
