"""
Configuration module for Linear CLI.

This module handles configuration settings for the Linear CLI, including
secure storage and retrieval of authentication tokens.
"""

import base64
import contextlib
import json
import os
from pathlib import Path
from typing import Any, Optional

import keyring
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Constants
APP_NAME = "linear-cli"
CONFIG_DIR = Path.home() / ".config" / "linear_cli"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"
API_KEY_FILE = Path.home() / ".linear-cli-auth"
PROJECT_FILE = CONFIG_DIR / "project.json"
KEYRING_SERVICE = "linear-cli"
KEYRING_USERNAME = "linear-user"
DEFAULT_TIMEOUT = 30.0  # Default timeout for API requests in seconds


class ConfigError(Exception):
    """Exception raised for configuration errors."""

    pass


def _derive_key(password: str, salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
    """
    Derive a key from a password using PBKDF2.

    Args:
        password: The password to derive the key from
        salt: Optional salt to use for key derivation

    Returns:
        A tuple of (key, salt)
    """
    if salt is None:
        salt = os.urandom(16)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key, salt


def _encrypt(data: str, password: str) -> dict[str, str]:
    """
    Encrypt data with a password.

    Args:
        data: The data to encrypt
        password: The password to use for encryption

    Returns:
        A dictionary containing the encrypted data and salt
    """
    key, salt = _derive_key(password)
    f = Fernet(key)
    encrypted_data = f.encrypt(data.encode()).decode()
    return {
        "data": encrypted_data,
        "salt": base64.b64encode(salt).decode(),
    }


def _decrypt(encrypted_data: str, salt: str, password: str) -> str:
    """
    Decrypt data with a password.

    Args:
        encrypted_data: The encrypted data
        salt: The salt used for encryption
        password: The password to use for decryption

    Returns:
        The decrypted data
    """
    salt_bytes = base64.b64decode(salt)
    key, _ = _derive_key(password, salt_bytes)
    f = Fernet(key)
    return f.decrypt(encrypted_data.encode()).decode()


def ensure_config_dir() -> None:
    """Ensure the configuration directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def get_token() -> Optional[str]:
    """
    Get the Linear API token from secure storage.

    First checks for an API key in the dedicated auth file, then falls back to
    the regular token storage mechanisms.

    Returns:
        The API token if found, None otherwise
    """
    # First try to get the API key from the dedicated auth file
    api_key = get_api_key()
    if api_key:
        return api_key

    # Try to get the token from keyring
    token = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
    if token:
        return token

    # Fall back to encrypted file
    if not CREDENTIALS_FILE.exists():
        return None

    try:
        with open(CREDENTIALS_FILE) as f:
            data = json.load(f)

        # Use a default password derived from the machine ID
        # This is not highly secure but better than plaintext
        machine_id = _get_machine_id()
        return _decrypt(data["data"], data["salt"], machine_id)
    except Exception as e:
        raise ConfigError(f"Failed to read credentials: {e}") from e


def save_token(token: str) -> None:
    """
    Save the Linear API token to secure storage.

    Args:
        token: The API token to save
    """
    ensure_config_dir()

    # Try to save to keyring first
    # Use contextlib.suppress to silently ignore exceptions
    # This is expected behavior if keyring is not available
    # or fails for any reason, so we silently continue to the fallback
    with contextlib.suppress(Exception):
        keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, token)
        return

    try:
        # Use a default password derived from the machine ID
        machine_id = _get_machine_id()
        encrypted = _encrypt(token, machine_id)

        with open(CREDENTIALS_FILE, "w") as f:
            json.dump(encrypted, f)
    except Exception as e:
        raise ConfigError(f"Failed to save credentials: {e}") from e


def clear_token() -> None:
    """Clear the stored Linear API token."""
    with contextlib.suppress(Exception):
        keyring.delete_password(KEYRING_SERVICE, KEYRING_USERNAME)

    if CREDENTIALS_FILE.exists():
        CREDENTIALS_FILE.unlink()


def _get_machine_id() -> str:
    """
    Get a unique identifier for the current machine.

    This is used as a fallback encryption key when keyring is not available.
    """
    # Try to get a machine ID from the system
    # Use a series of if statements to avoid try-except-pass

    # Try Linux machine ID files
    if os.path.exists("/etc/machine-id"):
        # Use contextlib.suppress to silently ignore exceptions
        # and continue to the next method if this fails
        with contextlib.suppress(Exception), open("/etc/machine-id") as f:
            return f.read().strip()

    if os.path.exists("/var/lib/dbus/machine-id"):
        # Use contextlib.suppress to silently ignore exceptions
        # and continue to the next method if this fails
        with contextlib.suppress(Exception), open("/var/lib/dbus/machine-id") as f:
            return f.read().strip()

    # Try macOS
    if os.path.exists("/Library/Preferences/SystemConfiguration/preferences.plist"):
        # Use contextlib.suppress to silently ignore exceptions
        # and continue to the fallback method if this fails
        with contextlib.suppress(Exception):
            import shutil
            import subprocess

            # Get the full path to the ioreg executable
            ioreg_path = shutil.which("ioreg")
            if not ioreg_path:
                # If ioreg is not found, skip this method
                return None

            # All arguments are hardcoded and trusted
            result = subprocess.run(  # noqa: S603
                [ioreg_path, "-rd1", "-c", "IOPlatformExpertDevice"],
                capture_output=True,
                text=True,
                check=False,  # Don't raise an exception if the command fails
            )

            for line in result.stdout.splitlines():
                if "IOPlatformUUID" in line:
                    return line.split('"')[-2]

    # Fallback to a combination of hostname and username
    import getpass
    import socket
    return f"{socket.gethostname()}-{getpass.getuser()}"


def save_api_key(api_key: str) -> None:
    """
    Save the Linear API key to a dedicated auth file in the home directory.

    Args:
        api_key: The API key to save
    """
    try:
        with open(API_KEY_FILE, "w") as f:
            f.write(api_key)
        # Set appropriate permissions (readable only by the user)
        os.chmod(API_KEY_FILE, 0o600)
    except Exception as e:
        raise ConfigError(f"Failed to save API key: {e}") from e


def get_api_key() -> Optional[str]:
    """
    Get the Linear API key from the dedicated auth file.

    Returns:
        The API key if found, None otherwise
    """
    if not API_KEY_FILE.exists():
        return None

    try:
        with open(API_KEY_FILE) as f:
            api_key = f.read().strip()
        return api_key if api_key else None
    except Exception as e:
        raise ConfigError(f"Failed to read API key: {e}") from e


def clear_api_key() -> None:
    """Clear the stored Linear API key."""
    if API_KEY_FILE.exists():
        API_KEY_FILE.unlink()


def save_default_project(project_id: str, project_name: str) -> None:
    """
    Save the default project ID and name to the configuration file.

    Args:
        project_id: The project ID to save
        project_name: The project name to save
    """
    ensure_config_dir()

    try:
        with open(PROJECT_FILE, "w") as f:
            json.dump({"id": project_id, "name": project_name}, f)
    except Exception as e:
        raise ConfigError(f"Failed to save default project: {e}") from e


def get_default_project() -> Optional[dict[str, str]]:
    """
    Get the default project ID and name from the configuration file.

    Returns:
        A dictionary containing the project ID and name if found, None otherwise
    """
    if not PROJECT_FILE.exists():
        return None

    try:
        with open(PROJECT_FILE) as f:
            data = json.load(f)
            # Ensure the data has the expected structure
            if isinstance(data, dict) and "id" in data and "name" in data:
                return {"id": str(data["id"]), "name": str(data["name"])}
            raise ConfigError("Invalid project data format")
    except Exception as e:
        raise ConfigError(f"Failed to read default project: {e}") from e


def clear_default_project() -> None:
    """Clear the stored default project."""
    if PROJECT_FILE.exists():
        PROJECT_FILE.unlink()


def get_config() -> dict[str, Any]:
    """
    Get the CLI configuration.

    Returns:
        A dictionary containing configuration values
    """
    return {
        "timeout": DEFAULT_TIMEOUT,
    }
