"""
Authentication module for Linear CLI.

This module handles user authentication, including prompting for credentials,
authenticating with the Linear API, and storing the access token securely.
"""

import getpass
from typing import Optional

import typer
from rich.console import Console

from linear_cli import api, config, models

console = Console()


class AuthenticationError(Exception):
    """Exception raised for authentication errors."""

    pass


def login(
    email: Optional[str] = None, 
    password: Optional[str] = None,
    api_key: Optional[str] = None
) -> models.User:
    """
    Authenticate with Linear and store the access token.

    Args:
        email: The user's email (will prompt if not provided and api_key not provided)
        password: The user's password (will prompt if not provided and api_key not provided)
        api_key: The Linear API key (if provided, email and password are ignored)

    Returns:
        The authenticated user

    Raises:
        AuthenticationError: If authentication fails
    """
    try:
        # If API key is provided, use it for authentication
        if api_key:
            # Verify the API key by making a test API call
            auth_response = api.authenticate_with_api_key(api_key)
            # Store the API key securely
            config.save_api_key(api_key)
            return auth_response.user
        # Otherwise use email/password authentication
        email, password = _get_credentials(email, password)
        auth_response = api.authenticate(email, password)
        # Store the token securely
        config.save_token(auth_response.access_token)
        return auth_response.user
    except api.AuthenticationError as e:
        raise AuthenticationError(f"Authentication failed: {str(e)}") from e
    except api.NetworkError as e:
        raise AuthenticationError(f"Network error during authentication: {str(e)}") from e
    except config.ConfigError as e:
        raise AuthenticationError(f"Failed to save authentication token: {str(e)}") from e


def logout() -> None:
    """
    Log out by clearing the stored access token and API key.

    Raises:
        AuthenticationError: If there's an error clearing the token or API key
    """
    try:
        config.clear_token()
        config.clear_api_key()
    except Exception as e:
        raise AuthenticationError(f"Failed to clear authentication data: {str(e)}") from e


def get_current_user() -> models.User:
    """
    Get the currently authenticated user.

    Returns:
        The authenticated user

    Raises:
        AuthenticationError: If not authenticated or if there's an error getting the user
    """
    token = config.get_token()
    if not token:
        raise AuthenticationError("Not authenticated. Please run 'linear auth login'.")

    try:
        return api.get_me(token=token)
    except api.AuthenticationError as e:
        # Token might be expired or invalid
        # Clear both the regular token and the API key
        config.clear_token()
        config.clear_api_key()
        raise AuthenticationError(
            "Authentication token expired or invalid. Please login again."
        ) from e
    except api.LinearAPIError as e:
        raise AuthenticationError(f"Failed to get user profile: {str(e)}") from e
    except api.NetworkError as e:
        raise AuthenticationError(f"Network error: {str(e)}") from e


def is_authenticated() -> bool:
    """
    Check if the user is authenticated.

    Returns:
        True if authenticated, False otherwise
    """
    # get_token will check for both API key and regular token
    token = config.get_token()
    return token is not None


def _get_credentials(
    email: Optional[str] = None, password: Optional[str] = None
) -> tuple[str, str]:
    """
    Get user credentials, prompting if necessary.

    Args:
        email: The user's email (will prompt if not provided)
        password: The user's password (will prompt if not provided)

    Returns:
        A tuple of (email, password)

    Raises:
        typer.Abort: If the user cancels the prompt
    """
    if not email:
        email = typer.prompt("Email")

    if not password:
        password = getpass.getpass("Password: ")

    if not email or not password:
        raise typer.Abort()

    return email, password
