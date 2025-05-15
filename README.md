# Linear CLI

A command-line interface for interacting with the Linear.app API.

[![CI](https://github.com/royreznik/linear-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/royreznik/linear-cli/actions/workflows/ci.yml)
[![Publish](https://github.com/royreznik/linear-cli/actions/workflows/publish.yml/badge.svg)](https://github.com/royreznik/linear-cli/actions/workflows/publish.yml)

## Features

- Authenticate with Linear using your email and password or API key
- List projects and issues
- Create new issues
- Set a default project for issue creation and listing
- View your profile information
- Rich terminal output with colors and formatting

## Installation

### Using uv (recommended)

```bash
uv pip install linear-app-cli
```

### From source

```bash
git clone https://github.com/royreznik/linear-cli.git
cd linear-cli
uv pip install -e .
```

## Quick Start

1. Authenticate with Linear:

```bash
# Using interactive prompt for email and password
linear auth login

# Or using an API key
linear auth login --api-key <your-api-key>
```

2. List your projects:

```bash
linear projects list
```

3. Set a default project (optional):

```bash
linear projects set-default <project-name-or-id>
```

4. List issues for a specific project (or default project if set):

```bash
# For a specific project
linear issues list --project <project-name-or-id>

# For the default project (if set)
linear issues list
```

5. Create a new issue:

```bash
# For a specific project
linear issues create --title "New Issue" --description "Description" --project <project-name-or-id>

# For the default project (if set)
linear issues create --title "New Issue" --description "Description"
```

6. View your profile:

```bash
linear me
```

## Commands

### Authentication

- `linear auth login`: Log in to Linear with your email and password (interactive prompt)
- `linear auth login --email <email> --password <password>`: Log in with email and password
- `linear auth login --api-key <api-key>`: Log in with an API key
- `linear auth logout`: Log out from Linear

### Projects

- `linear projects list`: List all projects
- `linear projects set-default <project>`: Set the default project for issue creation and listing
- `linear projects get-default`: Show the current default project
- `linear projects clear-default`: Clear the default project

### Issues

- `linear issues list`: List all issues (uses default project if set)
- `linear issues list --project <id-or-name>`: List issues for a specific project
- `linear issues create --title <title> --description <desc>`: Create a new issue (uses default project if set)
- `linear issues create --title <title> --description <desc> --project <id-or-name>`: Create a new issue for a specific project

### User

- `linear me`: Show your Linear profile

### Global Options

- `--timeout <seconds>`: Set request timeout in seconds
- `--version`: Show version information
- `--help`: Show help information

## Development

### Setup

1. Clone the repository:

```bash
git clone https://github.com/royreznik/linear-cli.git
cd linear-cli
```

2. Install development dependencies:

```bash
uv pip install -e ".[dev]"
```

### Testing

Run tests with pytest:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=linear_cli
```

### Linting

Run ruff:

```bash
ruff check .
```

Run mypy:

```bash
mypy linear_cli
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please make sure your code passes all tests and linting checks.

## Releasing

This project uses GitHub Actions to automatically build and publish the package to PyPI when a new release is created or when manually triggered.

### Creating a Release

#### Option 1: Create a GitHub Release

1. Update the version in `pyproject.toml`
2. Create a new tag with the version number:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```
3. Go to the GitHub repository and create a new release using the tag
4. The GitHub Action will automatically build and publish the package to PyPI

#### Option 2: Manual Dispatch

1. Update the version in `pyproject.toml`
2. Commit and push your changes
3. Go to the GitHub repository's Actions tab
4. Select the "Publish to PyPI" workflow
5. Click "Run workflow"
6. Enter the version number (e.g., 0.1.0) and click "Run workflow"
7. The GitHub Action will build and publish the package to PyPI

### PyPI Configuration

To publish to PyPI, you need to add a PyPI API token as a GitHub secret:

1. Generate an API token on PyPI (https://pypi.org/manage/account/token/)
2. Add the token as a secret in your GitHub repository with the name `PYPI_API_TOKEN`

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
