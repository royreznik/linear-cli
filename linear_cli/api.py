"""
API wrapper for the Linear GraphQL API.

This module provides a thin wrapper around the Linear GraphQL API, handling
authentication, error handling, and response parsing.
"""

import asyncio
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

import httpx
from pydantic import ValidationError

from linear_cli import config, models

# Constants
LINEAR_API_URL = "https://api.linear.app/graphql"
LINEAR_AUTH_URL = "https://api.linear.app/oauth/token"

# Type variables for generic functions
T = TypeVar("T")
R = TypeVar("R")


class LinearAPIError(Exception):
    """Exception raised for Linear API errors."""

    def __init__(self, message: str, errors: Optional[list[models.GraphQLError]] = None) -> None:
        self.message = message
        self.errors = errors or []
        super().__init__(message)


class AuthenticationError(LinearAPIError):
    """Exception raised for authentication errors."""

    pass


class NetworkError(LinearAPIError):
    """Exception raised for network errors."""

    pass


def _require_auth(func: Callable[..., R]) -> Callable[..., R]:
    """
    Decorator to ensure a function has an auth token.

    Args:
        func: The function to decorate

    Returns:
        The decorated function
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> R:
        if "token" not in kwargs or not kwargs["token"]:
            token = config.get_token()
            if not token:
                raise AuthenticationError(
                    "Authentication required. Please run 'linear auth login'."
                )
            kwargs["token"] = token
        return func(*args, **kwargs)

    return wrapper


async def _execute_query_async(
    query: str,
    variables: Optional[dict[str, Any]] = None,
    token: Optional[str] = None,
    timeout: Optional[float] = None,
) -> dict[str, Any]:
    """
    Execute a GraphQL query against the Linear API asynchronously.

    Args:
        query: The GraphQL query to execute
        variables: Variables for the GraphQL query
        token: The authentication token
        timeout: Request timeout in seconds

    Returns:
        The response data

    Raises:
        LinearAPIError: If the API returns an error
        NetworkError: If there's a network error
    """
    headers = {
        "Content-Type": "application/json",
    }

    if token:
        # Try without the "Bearer " prefix for API keys
        # Linear API might expect the API key directly
        if token.startswith("lin_api_"):
            headers["Authorization"] = token
        else:
            headers["Authorization"] = f"Bearer {token}"

    timeout_value = timeout or config.DEFAULT_TIMEOUT

    try:
        async with httpx.AsyncClient(timeout=timeout_value) as client:
            response = await client.post(
                LINEAR_API_URL,
                json={"query": query, "variables": variables or {}},
                headers=headers,
            )

            response.raise_for_status()
            result = response.json()

            if "errors" in result and result["errors"]:
                errors = [models.GraphQLError(**error) for error in result["errors"]]
                error_message = "; ".join(error.message for error in errors)
                raise LinearAPIError(f"GraphQL Error: {error_message}", errors)

            # Ensure we return a dictionary
            if not isinstance(result, dict):
                raise LinearAPIError(f"Expected a dictionary response, got {type(result)}")

            return result
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise AuthenticationError("Authentication failed. Please login again.") from e
        try:
            error_data = e.response.json()
            error_message = error_data.get("message", str(e))

            # Add more detailed error information for 400 errors
            if e.response.status_code == 400:
                # Include the request variables in the error message for debugging
                error_detail = f"Request variables: {variables}"
                error_message = f"{error_message}. {error_detail}"
        except Exception:
            error_message = str(e)
        raise LinearAPIError(f"HTTP Error: {error_message}") from e
    except httpx.RequestError as e:
        raise NetworkError(f"Network Error: {str(e)}") from e
    except Exception as e:
        raise LinearAPIError(f"Unexpected Error: {str(e)}") from e


def _execute_query(
    query: str,
    variables: Optional[dict[str, Any]] = None,
    token: Optional[str] = None,
    timeout: Optional[float] = None,
) -> dict[str, Any]:
    """
    Execute a GraphQL query against the Linear API synchronously.

    Args:
        query: The GraphQL query to execute
        variables: Variables for the GraphQL query
        token: The authentication token
        timeout: Request timeout in seconds

    Returns:
        The response data

    Raises:
        LinearAPIError: If the API returns an error
        NetworkError: If there's a network error
    """
    return asyncio.run(_execute_query_async(query, variables, token, timeout))


async def authenticate_async(email: str, password: str) -> models.AuthResponse:
    """
    Authenticate with Linear using email and password asynchronously.

    Args:
        email: The user's email
        password: The user's password

    Returns:
        An AuthResponse containing the access token and user info

    Raises:
        AuthenticationError: If authentication fails
    """
    try:
        async with httpx.AsyncClient(timeout=config.DEFAULT_TIMEOUT) as client:
            response = await client.post(
                LINEAR_AUTH_URL,
                json={
                    "grant_type": "password",
                    "username": email,
                    "password": password,
                },
                headers={"Content-Type": "application/json"},
            )

            response.raise_for_status()
            data = response.json()

            if "access_token" not in data:
                raise AuthenticationError("Authentication failed: No access token received")

            # Get user info
            user_query = """
            query Me {
                viewer {
                    id
                    name
                    email
                    displayName
                    avatarUrl
                    createdAt
                    updatedAt
                }
            }
            """

            user_response = await _execute_query_async(user_query, token=data["access_token"])
            user_data = user_response["data"]["viewer"]

            return models.AuthResponse(
                access_token=data["access_token"],
                user=models.User(
                    id=user_data["id"],
                    name=user_data["name"],
                    email=user_data["email"],
                    display_name=user_data.get("displayName"),
                    avatar_url=user_data.get("avatarUrl"),
                    created_at=user_data["createdAt"],
                    updated_at=user_data["updatedAt"],
                ),
            )
    except httpx.HTTPStatusError as e:
        try:
            error_data = e.response.json()
            error_message = error_data.get("message", str(e))
        except Exception:
            error_message = str(e)
        raise AuthenticationError(f"Authentication failed: {error_message}") from e
    except httpx.RequestError as e:
        raise NetworkError(f"Network Error: {str(e)}") from e
    except Exception as e:
        raise AuthenticationError(f"Authentication failed: {str(e)}") from e


def authenticate(email: str, password: str) -> models.AuthResponse:
    """
    Authenticate with Linear using email and password synchronously.

    Args:
        email: The user's email
        password: The user's password

    Returns:
        An AuthResponse containing the access token and user info

    Raises:
        AuthenticationError: If authentication fails
    """
    return asyncio.run(authenticate_async(email, password))


async def authenticate_with_api_key_async(api_key: str) -> models.AuthResponse:
    """
    Authenticate with Linear using an API key asynchronously.

    Args:
        api_key: The Linear API key

    Returns:
        An AuthResponse containing the access token and user info

    Raises:
        AuthenticationError: If authentication fails
    """
    try:
        # Get user info using the API key as the token
        user_query = """
        query Me {
            viewer {
                id
                name
                email
                displayName
                avatarUrl
                createdAt
                updatedAt
            }
        }
        """

        user_response = await _execute_query_async(user_query, token=api_key)
        user_data = user_response["data"]["viewer"]

        return models.AuthResponse(
            access_token=api_key,  # The API key is the access token
            user=models.User(
                id=user_data["id"],
                name=user_data["name"],
                email=user_data["email"],
                display_name=user_data.get("displayName"),
                avatar_url=user_data.get("avatarUrl"),
                created_at=user_data["createdAt"],
                updated_at=user_data["updatedAt"],
            ),
        )
    except httpx.HTTPStatusError as e:
        try:
            error_data = e.response.json()
            error_message = error_data.get("message", str(e))
        except Exception:
            error_message = str(e)
        raise AuthenticationError(f"Authentication failed: {error_message}") from e
    except httpx.RequestError as e:
        raise NetworkError(f"Network Error: {str(e)}") from e
    except Exception as e:
        raise AuthenticationError(f"Authentication failed: {str(e)}") from e


def authenticate_with_api_key(api_key: str) -> models.AuthResponse:
    """
    Authenticate with Linear using an API key synchronously.

    Args:
        api_key: The Linear API key

    Returns:
        An AuthResponse containing the access token and user info

    Raises:
        AuthenticationError: If authentication fails
    """
    return asyncio.run(authenticate_with_api_key_async(api_key))


@_require_auth
async def get_me_async(
    *, token: Optional[str] = None, timeout: Optional[float] = None
) -> models.User:
    """
    Get the authenticated user's profile asynchronously.

    Args:
        token: The authentication token
        timeout: Request timeout in seconds

    Returns:
        The user's profile

    Raises:
        LinearAPIError: If the API returns an error
    """
    query = """
    query Me {
        viewer {
            id
            name
            email
            displayName
            avatarUrl
            active
            createdAt
            updatedAt
        }
    }
    """

    response = await _execute_query_async(query, token=token, timeout=timeout)

    try:
        user_data = response["data"]["viewer"]
        return models.User(
            id=user_data["id"],
            name=user_data["name"],
            email=user_data["email"],
            display_name=user_data.get("displayName"),
            avatar_url=user_data.get("avatarUrl"),
            active=user_data.get("active", True),
            created_at=user_data["createdAt"],
            updated_at=user_data["updatedAt"],
        )
    except (KeyError, ValidationError) as e:
        raise LinearAPIError(f"Failed to parse user data: {str(e)}") from e


@_require_auth
def get_me(*, token: Optional[str] = None, timeout: Optional[float] = None) -> models.User:
    """
    Get the authenticated user's profile synchronously.

    Args:
        token: The authentication token
        timeout: Request timeout in seconds

    Returns:
        The user's profile

    Raises:
        LinearAPIError: If the API returns an error
    """
    return asyncio.run(get_me_async(token=token, timeout=timeout))


@_require_auth
async def list_projects_async(
    *, token: Optional[str] = None, timeout: Optional[float] = None
) -> models.ProjectConnection:
    """
    List projects asynchronously.

    Args:
        token: The authentication token
        timeout: Request timeout in seconds

    Returns:
        A connection of projects

    Raises:
        LinearAPIError: If the API returns an error
    """
    # First, get the viewer's information to confirm the API is working
    viewer_query = """
    query {
        viewer {
            id
            name
            email
        }
    }
    """

    await _execute_query_async(viewer_query, variables={}, token=token, timeout=timeout)

    # If we get here, the API is working, so now try to get the projects
    query = """
    query {
        projects {
            nodes {
                id
                name
                description
                state
                createdAt
                updatedAt
            }
        }
    }
    """

    response = await _execute_query_async(query, variables={}, token=token, timeout=timeout)

    try:
        projects_data = response["data"]["projects"]["nodes"]
        projects = []

        for project_data in projects_data:
            projects.append(models.Project(
                id=project_data["id"],
                name=project_data["name"],
                description=project_data.get("description"),
                icon=None,
                color=None,
                state=project_data["state"],
                created_at=project_data["createdAt"],
                updated_at=project_data["updatedAt"],
                team_ids=[],
                lead_id=None,
                members_ids=[],
                url=None,
            ))

        return models.ProjectConnection(
            nodes=projects,
            page_info={},
        )
    except (KeyError, ValidationError) as e:
        raise LinearAPIError(f"Failed to parse projects data: {str(e)}") from e


@_require_auth
def list_projects(
    *, token: Optional[str] = None, timeout: Optional[float] = None
) -> models.ProjectConnection:
    """
    List projects synchronously.

    Args:
        token: The authentication token
        timeout: Request timeout in seconds

    Returns:
        A connection of projects

    Raises:
        LinearAPIError: If the API returns an error
    """
    return asyncio.run(list_projects_async(token=token, timeout=timeout))


@_require_auth
async def list_issues_async(
    *,
    project_id: Optional[str] = None,
    token: Optional[str] = None,
    timeout: Optional[float] = None,
) -> models.IssueConnection:
    """
    List issues asynchronously.

    Args:
        project_id: Optional project ID, slug, or name to filter issues
        token: The authentication token
        timeout: Request timeout in seconds

    Returns:
        A connection of issues

    Raises:
        LinearAPIError: If the API returns an error
    """
    # If project_id is provided, first try to get the actual project ID
    actual_project_id = None
    if project_id:
        # First try to get the project by ID or slug
        project_query = """
        query Project($id: String!) {
            project(id: $id) {
                id
            }
        }
        """

        try:
            project_response = await _execute_query_async(
                project_query,
                variables={"id": project_id},
                token=token,
                timeout=timeout,
            )

            # Extract the actual project ID
            try:
                actual_project_id = project_response["data"]["project"]["id"]
            except (KeyError, IndexError):
                # If we can't get the project by ID or slug, try to find it by name
                projects_query = """
                query {
                    projects {
                        nodes {
                            id
                            name
                        }
                    }
                }
                """

                try:
                    projects_response = await _execute_query_async(
                        projects_query,
                        token=token,
                        timeout=timeout,
                    )

                    # Find the project with the matching name
                    projects_data = projects_response["data"]["projects"]["nodes"]
                    for project_data in projects_data:
                        if project_data["name"].lower() == project_id.lower():
                            actual_project_id = project_data["id"]
                            break

                    # If we still can't find the project, use the original project_id
                    if not actual_project_id:
                        actual_project_id = project_id
                except LinearAPIError:
                    # If we can't get the projects, use the original project_id
                    actual_project_id = project_id
        except LinearAPIError:
            # If we can't get the project, try to find it by name
            projects_query = """
            query {
                projects {
                    nodes {
                        id
                        name
                    }
                }
            }
            """

            try:
                projects_response = await _execute_query_async(
                    projects_query,
                    token=token,
                    timeout=timeout,
                )

                # Find the project with the matching name
                projects_data = projects_response["data"]["projects"]["nodes"]
                for project_data in projects_data:
                    if project_data["name"].lower() == project_id.lower():
                        actual_project_id = project_data["id"]
                        break

                # If we still can't find the project, use the original project_id
                if not actual_project_id:
                    actual_project_id = project_id
            except LinearAPIError:
                # If we can't get the projects, use the original project_id
                actual_project_id = project_id

    query = """
    query Issues($filter: IssueFilter) {
        issues(filter: $filter) {
            nodes {
                id
                title
                description
                priority
                state {
                    id
                    name
                }
                team {
                    id
                }
                project {
                    id
                }
                assignee {
                    id
                }
                creator {
                    id
                }
                createdAt
                updatedAt
                url
            }
            pageInfo {
                hasNextPage
                endCursor
            }
        }
    }
    """

    variables = {}
    if actual_project_id:
        variables["filter"] = {"project": {"id": {"eq": actual_project_id}}}

    response = await _execute_query_async(query, variables=variables, token=token, timeout=timeout)

    try:
        issues_data = response["data"]["issues"]
        issues = []

        for issue_data in issues_data["nodes"]:
            issues.append(models.Issue(
                id=issue_data["id"],
                title=issue_data["title"],
                description=issue_data.get("description"),
                priority=issue_data.get("priority", 0),
                state_id=issue_data["state"]["id"],
                state_name=issue_data["state"]["name"],
                team_id=issue_data["team"]["id"],
                project_id=issue_data["project"]["id"] if issue_data.get("project") else None,
                assignee_id=issue_data["assignee"]["id"] if issue_data.get("assignee") else None,
                creator_id=issue_data["creator"]["id"],
                created_at=issue_data["createdAt"],
                updated_at=issue_data["updatedAt"],
                url=issue_data.get("url"),
            ))

        return models.IssueConnection(
            nodes=issues,
            page_info=issues_data.get("pageInfo", {}),
        )
    except (KeyError, ValidationError) as e:
        raise LinearAPIError(f"Failed to parse issues data: {str(e)}") from e


@_require_auth
def list_issues(
    *,
    project_id: Optional[str] = None,
    token: Optional[str] = None,
    timeout: Optional[float] = None,
) -> models.IssueConnection:
    """
    List issues synchronously.

    Args:
        project_id: Optional project ID or slug to filter issues
        token: The authentication token
        timeout: Request timeout in seconds

    Returns:
        A connection of issues

    Raises:
        LinearAPIError: If the API returns an error
    """
    return asyncio.run(list_issues_async(project_id=project_id, token=token, timeout=timeout))


@_require_auth
async def create_issue_async(
    *,
    title: str,
    description: Optional[str] = None,
    project_id: str,
    team_id: Optional[str] = None,
    token: Optional[str] = None,
    timeout: Optional[float] = None,
) -> models.Issue:
    """
    Create an issue asynchronously.

    Args:
        title: The issue title
        description: The issue description
        project_id: The project ID, slug, or name
        team_id: The team ID (optional if the project belongs to only one team)
        token: The authentication token
        timeout: Request timeout in seconds

    Returns:
        The created issue

    Raises:
        LinearAPIError: If the API returns an error
    """
    # First, try to get the project by ID or slug to ensure it exists and get its actual ID
    project_query = """
    query Project($id: String!) {
        project(id: $id) {
            id
            teamIds
        }
    }
    """

    actual_project_id = None

    try:
        project_response = await _execute_query_async(
            project_query,
            variables={"id": project_id},
            token=token,
            timeout=timeout,
        )

        # Extract the actual project ID and team IDs
        try:
            actual_project_id = project_response["data"]["project"]["id"]
            team_ids = project_response["data"]["project"].get("teamIds", [])

            # If team_id is not provided and the project belongs to multiple teams, raise an error
            if not team_id and len(team_ids) > 1:
                raise LinearAPIError("Project belongs to multiple teams. Please specify a team ID.")
            # If team_id is not provided and the project belongs to one team, use that team
            if not team_id and len(team_ids) == 1:
                team_id = team_ids[0]
        except (KeyError, IndexError):
            # If we can't get the project by ID or slug, try to find it by name
            projects_query = """
            query {
                projects {
                    nodes {
                        id
                        name
                    }
                }
            }
            """

            try:
                projects_response = await _execute_query_async(
                    projects_query,
                    token=token,
                    timeout=timeout,
                )

                # Find the project with the matching name
                projects_data = projects_response["data"]["projects"]["nodes"]
                for project_data in projects_data:
                    if project_data["name"].lower() == project_id.lower():
                        actual_project_id = project_data["id"]
                        break

                # If we still can't find the project, use the original project_id
                if not actual_project_id:
                    actual_project_id = project_id
            except LinearAPIError:
                # If we can't get the projects, use the original project_id
                actual_project_id = project_id
    except LinearAPIError:
        # If we can't get the project by ID or slug, try to find it by name
        projects_query = """
        query {
            projects {
                nodes {
                    id
                    name
                }
            }
        }
        """

        try:
            projects_response = await _execute_query_async(
                projects_query,
                token=token,
                timeout=timeout,
            )

            # Find the project with the matching name
            projects_data = projects_response["data"]["projects"]["nodes"]
            for project_data in projects_data:
                if project_data["name"].lower() == project_id.lower():
                    actual_project_id = project_data["id"]
                    break

            # If we still can't find the project, use the original project_id
            if not actual_project_id:
                actual_project_id = project_id
        except LinearAPIError:
            # If we can't get the projects, use the original project_id
            actual_project_id = project_id

    # Use the actual project ID
    project_id = actual_project_id

    # If team_id is not provided, we need to get it
    if not team_id:
        # Query the project to get its teams
        project_teams_query = """
        query Project($id: String!) {
            project(id: $id) {
                teams {
                    nodes {
                        id
                        name
                    }
                }
            }
        }
        """
        try:
            project_teams_response = await _execute_query_async(
                project_teams_query,
                variables={"id": project_id},
                token=token,
                timeout=timeout,
            )

            # Get the first team ID
            teams = project_teams_response["data"]["project"]["teams"]["nodes"]
            # If no teams are found, raise an error
            if not teams:
                raise LinearAPIError("No teams found for the project. Please specify a team ID.")
            team_id = teams[0]["id"]
        except Exception as e:
            # If there's an error getting the team ID, raise an error
            raise LinearAPIError(f"Failed to determine team ID: {str(e)}") from e

    mutation = """
    mutation CreateIssue($input: IssueCreateInput!) {
        issueCreate(input: $input) {
            success
            issue {
                id
                title
                description
                priority
                state {
                    id
                    name
                }
                team {
                    id
                }
                project {
                    id
                }
                assignee {
                    id
                }
                creator {
                    id
                }
                createdAt
                updatedAt
                url
            }
        }
    }
    """

    variables = {
        "input": {
            "title": title,
            "description": description,
            "teamId": team_id,
            "projectId": project_id,
        }
    }

    response = await _execute_query_async(
        mutation, variables=variables, token=token, timeout=timeout
    )

    try:
        result = response["data"]["issueCreate"]
        if not result["success"]:
            raise LinearAPIError("Failed to create issue")

        issue_data = result["issue"]
        return models.Issue(
            id=issue_data["id"],
            title=issue_data["title"],
            description=issue_data.get("description"),
            priority=issue_data.get("priority", 0),
            state_id=issue_data["state"]["id"],
            state_name=issue_data["state"]["name"],
            team_id=issue_data["team"]["id"],
            project_id=issue_data["project"]["id"] if issue_data.get("project") else None,
            assignee_id=issue_data["assignee"]["id"] if issue_data.get("assignee") else None,
            creator_id=issue_data["creator"]["id"],
            created_at=issue_data["createdAt"],
            updated_at=issue_data["updatedAt"],
            url=issue_data.get("url"),
        )
    except (KeyError, ValidationError) as e:
        raise LinearAPIError(f"Failed to parse issue data: {str(e)}") from e


@_require_auth
def create_issue(
    *,
    title: str,
    description: Optional[str] = None,
    project_id: str,
    team_id: Optional[str] = None,
    token: Optional[str] = None,
    timeout: Optional[float] = None,
) -> models.Issue:
    """
    Create an issue synchronously.

    Args:
        title: The issue title
        description: The issue description
        project_id: The project ID or slug
        team_id: The team ID (optional if the project belongs to only one team)
        token: The authentication token
        timeout: Request timeout in seconds

    Returns:
        The created issue

    Raises:
        LinearAPIError: If the API returns an error
    """
    return asyncio.run(
        create_issue_async(
            title=title,
            description=description,
            project_id=project_id,
            team_id=team_id,
            token=token,
            timeout=timeout,
        )
    )
