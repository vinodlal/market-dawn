"""Kite Connect login — automated TOTP flow, credentials from the OS keyring.

Ports the proven flow from scripts/generate_token.py, with two changes:
  - secrets come from core.security.credentials (encrypted keyring), not env vars
    (env vars are still honored first, for CI/host use — see credentials.get_secret)
  - the resulting access token is cached to a gitignored local file, reused for the
    rest of the same IST trading day (Kite tokens are single-day; avoids re-hitting
    the login endpoint on every run)

SECURITY: the access token is never printed and never logged.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from zoneinfo import ZoneInfo

import requests

from ..security import credentials as creds

IST = ZoneInfo("Asia/Kolkata")
LOGIN_URL = "https://kite.zerodha.com/api/login"
TWOFA_URL = "https://kite.zerodha.com/api/twofa"

ROOT = Path(__file__).resolve().parents[2]
SESSION_FILE = ROOT / "data" / "cache" / "kite_session.json"


def _extract_request_token(urls: list[str]) -> str | None:
    for u in urls:
        if not u:
            continue
        try:
            qs = parse_qs(urlparse(u).query)
        except Exception:
            continue
        if qs.get("request_token"):
            return qs["request_token"][0]
    return None


def _login() -> tuple[str, str]:
    """Run the TOTP web-login flow. Returns (api_key, access_token)."""
    import pyotp
    from kiteconnect import KiteConnect

    api_key = creds.require("KITE_API_KEY")
    api_secret = creds.require("KITE_API_SECRET")
    user_id = creds.require("KITE_USER_ID")
    password = creds.require("KITE_PASSWORD")
    totp_secret = creds.require("KITE_TOTP_SECRET")

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (marketdawn)"})

    r1 = session.post(LOGIN_URL, data={"user_id": user_id, "password": password}, timeout=30)
    r1.raise_for_status()
    j1 = r1.json()
    if j1.get("status") != "success":
        raise RuntimeError(f"Kite login step failed: {j1.get('message', j1)}")
    request_id = j1["data"]["request_id"]

    totp = pyotp.TOTP(totp_secret).now()
    r2 = session.post(TWOFA_URL, data={
        "user_id": user_id, "request_id": request_id,
        "twofa_value": totp, "twofa_type": "totp", "skip_session": "",
    }, timeout=30)
    r2.raise_for_status()
    j2 = r2.json()
    if j2.get("status") != "success":
        raise RuntimeError(f"Kite TOTP step failed: {j2.get('message', j2)}")

    kite = KiteConnect(api_key=api_key)
    login_url = kite.login_url()
    candidate_urls: list[str] = []
    try:
        resp = session.get(login_url, allow_redirects=True, timeout=30)
        candidate_urls.append(resp.url)
        candidate_urls.extend(h.headers.get("Location", "") for h in resp.history)
        candidate_urls.extend(h.url for h in resp.history)
    except requests.exceptions.RequestException as exc:
        req = getattr(exc, "request", None)
        if req is not None:
            candidate_urls.append(req.url)

    request_token = _extract_request_token(candidate_urls)
    if not request_token:
        raise RuntimeError(
            "Could not extract request_token from the Kite login redirect. "
            "Check the app's Redirect URL in kite.trade matches what we expect, "
            f"or that a one-time consent step isn't required. URLs tried: {candidate_urls}"
        )

    data = kite.generate_session(request_token, api_secret=api_secret)
    return api_key, data["access_token"]


def _cached_token() -> tuple[str, str] | None:
    if not SESSION_FILE.exists():
        return None
    try:
        obj = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    gen_date = obj.get("generated_date")
    today = datetime.now(IST).strftime("%Y-%m-%d")
    if gen_date != today:
        return None
    return obj.get("api_key"), obj.get("access_token")


def _persist_token(api_key: str, access_token: str) -> None:
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSION_FILE.write_text(json.dumps({
        "api_key": api_key,
        "access_token": access_token,
        "generated_date": datetime.now(IST).strftime("%Y-%m-%d"),
    }), encoding="utf-8")


def get_client(force_refresh: bool = False):
    """Return an authenticated KiteConnect client, using the day-cached token
    when available, else a fresh TOTP login."""
    from kiteconnect import KiteConnect

    env_token = os.environ.get("KITE_ACCESS_TOKEN")
    api_key = creds.require("KITE_API_KEY")
    if env_token and not force_refresh:
        access_token = env_token
    else:
        cached = None if force_refresh else _cached_token()
        if cached:
            api_key, access_token = cached
        else:
            api_key, access_token = _login()
            _persist_token(api_key, access_token)

    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)
    return kite
