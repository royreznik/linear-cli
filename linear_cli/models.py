"""
Pydantic models for Linear entities.

This module defines the data models used to represent Linear entities such as
users, projects, issues, etc. These models are used to parse and validate
responses from the Linear GraphQL API.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional, Union

from pydantic import BaseModel, Field


class IssueState(str, Enum):
    """Enum representing possible issue states in Linear."""

    BACKLOG = "backlog"
    UNSTARTED = "unstarted"
    STARTED = "started"
    COMPLETED = "completed"
    CANCELED = "canceled"


class User(BaseModel):
    """Model representing a Linear user."""

    id: str
    name: str
    email: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    active: bool = True
    created_at: datetime
    updated_at: datetime


class Team(BaseModel):
    """Model representing a Linear team."""

    id: str
    name: str
    key: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class Project(BaseModel):
    """Model representing a Linear project."""

    id: str
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    state: str
    created_at: datetime
    updated_at: datetime
    team_ids: list[str] = Field(default_factory=list)
    lead_id: Optional[str] = None
    members_ids: list[str] = Field(default_factory=list)
    
    # Computed fields for convenience
    url: Optional[str] = None


class Issue(BaseModel):
    """Model representing a Linear issue."""

    id: str
    title: str
    description: Optional[str] = None
    priority: int = 0
    state_id: str
    state_name: Optional[str] = None
    team_id: str
    project_id: Optional[str] = None
    assignee_id: Optional[str] = None
    creator_id: str
    created_at: datetime
    updated_at: datetime
    
    # Computed fields for convenience
    url: Optional[str] = None


class IssueConnection(BaseModel):
    """Model representing a paginated connection of issues."""

    nodes: list[Issue] = Field(default_factory=list)
    page_info: dict[str, Any] = Field(default_factory=dict)


class ProjectConnection(BaseModel):
    """Model representing a paginated connection of projects."""

    nodes: list[Project] = Field(default_factory=list)
    page_info: dict[str, Any] = Field(default_factory=dict)


class AuthResponse(BaseModel):
    """Model representing an authentication response from Linear."""

    access_token: str
    user: User


class GraphQLError(BaseModel):
    """Model representing a GraphQL error."""

    message: str
    locations: Optional[list[dict[str, int]]] = None
    path: Optional[list[Union[str, int]]] = None
    extensions: Optional[dict[str, Any]] = None


class GraphQLResponse(BaseModel):
    """Model representing a GraphQL response."""

    data: Optional[dict[str, Any]] = None
    errors: Optional[list[GraphQLError]] = None
