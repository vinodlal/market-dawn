"""Interactive, hidden-input credential setup.

Run:
    python -m core.security.setup_credentials          # set / update secrets
    python -m core.security.setup_credentials --status # show which are set (no values)

Secrets are saved ENCRYPTED in your OS keyring (Windows Credential Manager).
Nothing is written to disk in plaintext or committed to git.
"""
from __future__ import annotations

import getpass
import re
import sys

from . import credentials as c

_B32 = re.compile(r"[A-Z2-7]+")


def _totp_warning(raw: str) -> str | None:
    """Heuristic check: does this look like a base32 TOTP secret, or a mistake
    (e.g. the live 6-digit code, or a value with stray characters)?"""
    cleaned = "".join(_B32.findall(raw.upper()))
    if raw.strip().isdigit() and len(raw.strip()) <= 8:
        return "looks like a 6-digit live code, not the secret key — see SETUP.md"
    if len(cleaned) < 16:
        return "too short / has non-base32 characters to be a real TOTP secret key"
    return None


def _mask(v: str | None) -> str:
    if not v:
        return "-"
    return f"{v[:2]}..{v[-2:]}" if len(v) > 4 else "set"


def _print_status() -> int:
    print(f"Keyring backend: {c.backend_name()}\n")
    for name, label in c.SECRET_KEYS:
        val = c.get_secret(name)
        flag = "[x]" if val else ("[ ]" if name not in c.REQUIRED else "[!]")
        print(f"  {flag} {name:<20} {_mask(val)}")
    missing = [k for k in c.REQUIRED if not c.get_secret(k)]
    print("\nAll required secrets present." if not missing
          else f"\nMissing required: {', '.join(missing)}")
    return 0 if not missing else 1


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if "--status" in argv:
        return _print_status()

    print("MarketDawn — secure credential setup")
    print("Secrets are stored ENCRYPTED in your OS keyring; never in files or git.")
    print(f"Keyring backend: {c.backend_name()}\n")
    print("Press Enter to keep an existing value or skip an optional one.\n")

    for name, label in c.SECRET_KEYS:
        existing = c.get_secret(name)
        req = name in c.REQUIRED
        tag = "" if req else " (optional)"
        cur = f" [current: {_mask(existing)}]" if existing else ""
        val = getpass.getpass(f"{label}{tag}{cur}: ").strip()
        if not val:
            if req and not existing:
                print(f"  [!] {name} is required - still unset.")
            continue
        if name == "KITE_TOTP_SECRET":
            val = re.sub(r"[^A-Za-z2-7]", "", val).upper()  # strip spaces/dashes, normalize case
            warn = _totp_warning(val)
            if warn:
                print(f"  [!] Warning: this value {warn}. Saved anyway, but login will "
                      f"likely fail — see SETUP.md 'What is the TOTP secret'.")
        c.set_secret(name, val)
        print(f"  [x] {name} saved (encrypted).")

    print()
    return _print_status()


if __name__ == "__main__":
    raise SystemExit(main())
