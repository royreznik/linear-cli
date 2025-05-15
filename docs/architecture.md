# Linear CLI Architecture

This document describes the architecture of the Linear CLI application, including module responsibilities and the authentication flow.

## Overview

The Linear CLI is designed with a modular architecture to separate concerns and make the codebase maintainable and testable. The application follows these design principles:

1. **Separation of concerns**: Each module has a specific responsibility
2. **Async-first design**: Core functionality is implemented with async/await, with sync wrappers for CLI simplicity
3. **Error handling**: Custom exceptions for different error types with user-friendly messages
4. **Secure authentication**: Credentials are never stored, only access tokens are securely cached

## Module Responsibilities

### models.py

This module defines Pydantic models for Linear entities such as users, projects, issues, etc. These models are used to:

- Parse and validate responses from the Linear GraphQL API
- Provide type hints for the rest of the application
- Ensure consistent data structures throughout the application

### config.py

This module handles configuration settings for the CLI, including:

- Secure storage and retrieval of authentication tokens
- Default configuration values
- Path management for configuration files

The module uses the OS keyring when available, with a fallback to an encrypted file stored in `~/.config/linear_cli/credentials.json`.

### api.py

This module provides a thin wrapper around the Linear GraphQL API, handling:

- Authentication with the Linear API
- Executing GraphQL queries and mutations
- Error handling and response parsing
- Converting API responses to Pydantic models

The module provides both async and sync versions of each function, with the async versions being the primary implementation and the sync versions being wrappers around the async ones.

### auth.py

This module handles user authentication, including:

- Prompting for credentials
- Authenticating with the Linear API
- Storing and retrieving access tokens securely
- Managing authentication state

### cli.py

This module implements the command-line interface using Typer, including:

- Command definitions and argument parsing
- Output formatting using Rich
- Error handling and user feedback
- Global options like timeout and version

## Authentication Flow

The authentication flow in the Linear CLI works as follows:

1. **Initial authentication**:
   - User runs `linear auth login`
   - CLI prompts for email and password
   - Credentials are sent to Linear's OAuth endpoint to exchange for an access token
   - The access token is stored securely (keyring or encrypted file)
   - User information is fetched and displayed

2. **Subsequent commands**:
   - CLI checks for a stored access token
   - If found, the token is used to authenticate API requests
   - If not found, the user is prompted to log in
   - If a token is found but invalid, it is cleared and the user is prompted to log in again

3. **Token storage**:
   - The access token is stored using the system keyring if available
   - If keyring is not available, the token is encrypted and stored in `~/.config/linear_cli/credentials.json`
   - The encryption key is derived from a machine-specific identifier
   - The original credentials (email/password) are never stored

4. **Logout**:
   - User runs `linear auth logout`
   - The stored access token is cleared from both keyring and file storage

## Error Handling

The application uses a hierarchy of custom exceptions to handle different types of errors:

- `LinearAPIError`: Base exception for all API errors
  - `AuthenticationError`: For authentication-related errors
  - `NetworkError`: For network-related errors

These exceptions are caught at the CLI level and presented to the user with friendly messages.

## Async Design

The application is designed with async/await as the primary implementation pattern:

1. Core API functions are implemented as async functions
2. Sync wrappers are provided for simplicity in the CLI
3. The async implementation allows for better performance, especially when making multiple API calls

This design ensures the CLI remains responsive even on slow networks, while keeping the code simple and maintainable.