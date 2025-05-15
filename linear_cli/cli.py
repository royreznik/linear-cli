"""
Command-line interface for Linear CLI.

This module provides the command-line interface for interacting with the Linear API,
including commands for authentication, listing projects and issues, and creating issues.
"""

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from linear_cli import __version__, api, auth, config

# Create Typer app
app = typer.Typer(
    name="linear",
    help="Command-line interface for Linear.app",
    add_completion=True,
)

# Create sub-commands
auth_app = typer.Typer(help="Authentication commands")
projects_app = typer.Typer(help="Project commands")
issues_app = typer.Typer(help="Issue commands")

# Add sub-commands to main app
app.add_typer(auth_app, name="auth")
app.add_typer(projects_app, name="projects")
app.add_typer(issues_app, name="issues")

# Create console for rich output
console = Console()


# Global options
class GlobalOptions:
    """Global options for all commands."""

    def __init__(self, timeout: Optional[float] = None) -> None:
        self.timeout = timeout


# Callback to handle global options
@app.callback()
def global_options(
    ctx: typer.Context,
    timeout: Optional[float] = typer.Option(
        None, "--timeout", help="Request timeout in seconds"
    ),
    version: bool = typer.Option(
        False, "--version", "-v", help="Show version and exit"
    ),
) -> None:
    """Set global options for all commands."""
    if version:
        console.print(f"Linear CLI version: {__version__}")
        raise typer.Exit()

    ctx.obj = GlobalOptions(timeout=timeout)


# Auth commands
@auth_app.command("login")
def auth_login(
    email: Optional[str] = typer.Option(None, "--email", "-e", help="Your Linear email"),
    password: Optional[str] = typer.Option(None, "--password", "-p", help="Your Linear password"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", help="Your Linear API key"),
) -> None:
    """
    Log in to Linear.

    You can log in using either:
    - Email and password (if not provided, you will be prompted for them)
    - API key (if provided, email and password are ignored)
    """
    try:
        with console.status("Logging in..."):
            user = auth.login(email, password, api_key)

        console.print(f"[green]Logged in as {user.name} ({user.email})[/green]")
    except auth.AuthenticationError as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(code=1) from e
    except Exception as e:
        console.print(f"[red]Unexpected error: {str(e)}[/red]")
        raise typer.Exit(code=1) from e


@auth_app.command("logout")
def auth_logout() -> None:
    """Log out from Linear."""
    try:
        auth.logout()
        console.print("[green]Logged out successfully[/green]")
    except auth.AuthenticationError as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(code=1) from e
    except Exception as e:
        console.print(f"[red]Unexpected error: {str(e)}[/red]")
        raise typer.Exit(code=1) from e


# User commands
@app.command("me")
def me(ctx: typer.Context) -> None:  # noqa: ARG001
    """Show your Linear profile."""
    try:
        with console.status("Fetching your profile..."):
            user = auth.get_current_user()

        table = Table(title=f"Profile for {user.name}")
        table.add_column("Field", style="cyan")
        table.add_column("Value")

        table.add_row("ID", user.id)
        table.add_row("Name", user.name)
        table.add_row("Email", user.email)
        if user.display_name:
            table.add_row("Display Name", user.display_name)
        table.add_row("Active", "Yes" if user.active else "No")
        table.add_row("Created At", str(user.created_at))

        console.print(table)
    except auth.AuthenticationError as e:
        console.print(f"[red]Authentication error: {str(e)}[/red]")
        raise typer.Exit(code=1) from e
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(code=1) from e


# Project commands
@projects_app.command("list")
def list_projects(ctx: typer.Context) -> None:
    """List all projects."""
    try:
        with console.status("Fetching projects..."):
            projects = api.list_projects(timeout=ctx.obj.timeout)

        if not projects.nodes:
            console.print("[yellow]No projects found[/yellow]")
            return

        table = Table(title="Linear Projects")
        table.add_column("ID", style="dim")
        table.add_column("Name", style="cyan")
        table.add_column("State")
        table.add_column("Description")

        for project in projects.nodes:
            table.add_row(
                project.id,
                project.name,
                project.state,
                project.description or "",
            )

        console.print(table)
    except api.AuthenticationError as e:
        console.print(f"[red]Authentication error: {str(e)}[/red]")
        raise typer.Exit(code=1) from e
    except api.LinearAPIError as e:
        console.print(f"[red]API error: {str(e)}[/red]")
        raise typer.Exit(code=1) from e
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(code=1) from e


@projects_app.command("set-default")
def set_default_project(
    ctx: typer.Context,
    project: str = typer.Argument(..., help="Project name, ID, or slug to set as default"),
) -> None:
    """Set the default project for issue creation and listing."""
    try:
        with console.status("Fetching projects..."):
            projects = api.list_projects(timeout=ctx.obj.timeout)

        if not projects.nodes:
            console.print("[yellow]No projects found[/yellow]")
            return

        # Find the project by name, ID, or slug
        found_project = None
        for p in projects.nodes:
            if p.id == project or p.name.lower() == project.lower():
                found_project = p
                break

        if not found_project:
            console.print(f"[red]Project not found: {project}[/red]")
            raise typer.Exit(code=1)

        # Save the project as default
        config.save_default_project(found_project.id, found_project.name)
        console.print(
            f"[green]Default project set to:[/green] {found_project.name} ({found_project.id})"
        )
    except api.AuthenticationError as e:
        console.print(f"[red]Authentication error: {str(e)}[/red]")
        raise typer.Exit(code=1) from e
    except api.LinearAPIError as e:
        console.print(f"[red]API error: {str(e)}[/red]")
        raise typer.Exit(code=1) from e
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(code=1) from e


@projects_app.command("get-default")
def get_default_project() -> None:
    """Show the current default project."""
    try:
        project = config.get_default_project()
        if project:
            console.print(f"[green]Default project:[/green] {project['name']} ({project['id']})")
        else:
            console.print("[yellow]No default project set[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(code=1) from e


@projects_app.command("clear-default")
def clear_default_project() -> None:
    """Clear the default project."""
    try:
        config.clear_default_project()
        console.print("[green]Default project cleared[/green]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(code=1) from e


# Issue commands
@issues_app.command("list")
def list_issues(
    ctx: typer.Context,
    project: Optional[str] = typer.Option(
        None, "--project", "-p", help="Filter issues by project name, ID, or slug"
    ),
) -> None:
    """
    List issues.

    If project is provided, only issues for that project will be shown.
    If no project is provided, the default project will be used if set.
    """
    try:
        # Use default project if no project is specified
        if project is None:
            default_project = config.get_default_project()
            if default_project:
                project = default_project["id"]
                console.print(f"[blue]Using default project:[/blue] {default_project['name']}")

        with console.status("Fetching issues..."):
            issues = api.list_issues(project_id=project, timeout=ctx.obj.timeout)

        if not issues.nodes:
            console.print("[yellow]No issues found[/yellow]")
            return

        table = Table(title="Linear Issues")
        table.add_column("ID", style="dim")
        table.add_column("Title", style="cyan")
        table.add_column("State")
        table.add_column("Priority")

        for issue in issues.nodes:
            priority = "P" + str(issue.priority) if issue.priority > 0 else "-"
            table.add_row(
                issue.id,
                issue.title,
                issue.state_name or "",
                priority,
            )

        console.print(table)
    except api.AuthenticationError as e:
        console.print(f"[red]Authentication error: {str(e)}[/red]")
        raise typer.Exit(code=1) from e
    except api.LinearAPIError as e:
        console.print(f"[red]API error: {str(e)}[/red]")
        raise typer.Exit(code=1) from e
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(code=1) from e


@issues_app.command("create")
def create_issue(
    ctx: typer.Context,
    title: str = typer.Option(..., "--title", "-t", help="Issue title"),
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="Issue description"
    ),
    project: Optional[str] = typer.Option(
        None, "--project", "-p", help="Project name, ID, or slug (uses default if not specified)"
    ),
    team_id: Optional[str] = typer.Option(
        None, "--team-id", help="Team ID (optional if project belongs to only one team)"
    ),
) -> None:
    """
    Create a new issue.

    If no project is specified, the default project will be used if set.
    """
    try:
        # Use default project if no project is specified
        if project is None:
            default_project = config.get_default_project()
            if default_project:
                project = default_project["id"]
                console.print(f"[blue]Using default project:[/blue] {default_project['name']}")
            else:
                console.print("[red]No project specified and no default project set[/red]")
                console.print(
                    "Use --project to specify a project or set a default project with "
                    "'linear projects set-default'"
                )
                raise typer.Exit(code=1)

        with console.status("Creating issue..."):
            issue = api.create_issue(
                title=title,
                description=description,
                project_id=project,
                team_id=team_id,
                timeout=ctx.obj.timeout,
            )

        console.print(f"[green]Issue created successfully:[/green] {issue.title}")
        console.print(f"[blue]ID:[/blue] {issue.id}")
        if issue.url:
            console.print(f"[blue]URL:[/blue] {issue.url}")
    except api.AuthenticationError as e:
        console.print(f"[red]Authentication error: {str(e)}[/red]")
        raise typer.Exit(code=1) from e
    except api.LinearAPIError as e:
        console.print(f"[red]API error: {str(e)}[/red]")
        raise typer.Exit(code=1) from e
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(code=1) from e


if __name__ == "__main__":
    app()
