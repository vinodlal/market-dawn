"""Encrypted credential store.

Secrets live in the OS keyring (Windows Credential Manager / macOS Keychain /
Linux Secret Service) — encrypted at rest by the OS, per user account. They are
NEVER written to a plaintext file or committed to git.

Resolution order for `get_secret`:
  1. Environment variable  — used by CI / the cloud host's secret store.
  2. OS keyring            — used on the local machine (set via setup_credentials).

Run `python -m core.security.setup_credentials` to store them interactively.
"""
from __future__ import annotations

import os

import keyring
from keyring.errors import PasswordDeleteError

SERVICE = "marketdawn"

# (env/keyring name, human label)
SECRET_KEYS: list[tuple[str, str]] = [
    ("KITE_API_KEY", "Kite API key"),
    ("KITE_API_SECRET", "Kite API secret"),
    ("KITE_USER_ID", "Kite / Zerodha client ID (e.g. AB1234)"),
    ("KITE_PASSWORD", "Kite login password"),
    ("KITE_TOTP_SECRET", "Kite TOTP secret (base32 string, NOT a 6-digit code)"),
    ("TELEGRAM_BOT_TOKEN", "Telegram bot token"),
    ("TELEGRAM_CHAT_ID", "Telegram chat id"),
    ("ANTHROPIC_API_KEY", "Anthropic API key (for optional news summaries)"),
]

REQUIRED = {
    "KITE_API_KEY", "KITE_API_SECRET", "KITE_USER_ID",
    "KITE_PASSWORD", "KITE_TOTP_SECRET",
}


def get_secret(name: str) -> str | None:
    """Return a secret from the environment first, then the OS keyring."""
    val = os.environ.get(name)
    if val:
        return val
    return keyring.get_password(SERVICE, name)


def set_secret(name: str, value: str) -> None:
    """Store a secret encrypted in the OS keyring."""
    keyring.set_password(SERVICE, name, value)


def delete_secret(name: str) -> None:
    """Remove a secret from the OS keyring (no error if absent)."""
    try:
        keyring.delete_password(SERVICE, name)
    except PasswordDeleteError:
        pass


def require(name: str) -> str:
    """Return a secret or raise a clear error telling the user how to set it."""
    v = get_secret(name)
    if not v:
        raise RuntimeError(
            f"Missing secret {name!r}. Run: python -m core.security.setup_credentials"
        )
    return v


def status() -> dict[str, bool]:
    """Which secrets are present (True/False) — never returns the values."""
    return {name: bool(get_secret(name)) for name, _ in SECRET_KEYS}


def backend_name() -> str:
    return keyring.get_keyring().__class__.__name__
