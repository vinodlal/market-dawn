"""
generate_token.py — Kite Connect programmatic login (Section 2).

Performs the Zerodha Kite web login flow headlessly:
  1. POST user_id/password  -> request_id
  2. POST TOTP (live via pyotp) -> authenticated session cookies
  3. GET the Kite Connect login_url following redirects -> request_token
  4. kite.generate_session(request_token, api_secret) -> access_token

Reads these environment variables (set as GitHub Secrets in CI):
  KITE_API_KEY, KITE_API_SECRET, KITE_USER_ID, KITE_PASSWORD, KITE_TOTP_SECRET

When run as a script it:
  - masks the token in GitHub Actions logs (::add-mask::),
  - writes `access_token=<token>` to $GITHUB_OUTPUT (for later workflow steps),
  - writes kite_access_token.json (gitignored) so fetch_data.py can read it locally
    and within the same CI job.

SECURITY: never print the raw token to stdout. Only the mask directive is printed.
"""

import json
import os
import sys
from urllib.parse import urlparse, parse_qs

import requests

LOGIN_URL = "https://kite.zerodha.com/api/login"
TWOFA_URL = "https://kite.zerodha.com/api/twofa"

REQUIRED_ENV = [
    "KITE_API_KEY",
    "KITE_API_SECRET",
    "KITE_USER_ID",
    "KITE_PASSWORD",
    "KITE_TOTP_SECRET",
]

TOKEN_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "kite_access_token.json")


def _read_env():
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        raise SystemExit(
            "Missing required environment variables: " + ", ".join(missing) +
            "\nSet them as GitHub Secrets (CI) or export them locally before running."
        )
    return {k: os.environ[k].strip() for k in REQUIRED_ENV}


def _extract_request_token(urls):
    """Scan a list of candidate URLs for a request_token query param."""
    for u in urls:
        if not u:
            continue
        try:
            qs = parse_qs(urlparse(u).query)
        except Exception:
            continue
        if "request_token" in qs and qs["request_token"]:
            return qs["request_token"][0]
    return None


def get_access_token(api_key, api_secret, user_id, password, totp_secret):
    """Run the full login flow and return a fresh access_token string."""
    import pyotp
    from kiteconnect import KiteConnect

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (banknifty-predictor)"})

    # Step 1 — username/password -> request_id
    r1 = session.post(LOGIN_URL, data={"user_id": user_id, "password": password}, timeout=30)
    r1.raise_for_status()
    j1 = r1.json()
    if j1.get("status") != "success":
        raise RuntimeError(f"Login step failed: {j1}")
    request_id = j1["data"]["request_id"]

    # Step 2 — TOTP two-factor
    totp = pyotp.TOTP(totp_secret).now()
    r2 = session.post(
        TWOFA_URL,
        data={
            "user_id": user_id,
            "request_id": request_id,
            "twofa_value": totp,
            "twofa_type": "totp",
            "skip_session": "",
        },
        timeout=30,
    )
    r2.raise_for_status()
    j2 = r2.json()
    if j2.get("status") != "success":
        raise RuntimeError(f"TOTP step failed: {j2}")

    # Step 3 — follow the connect login redirect to harvest request_token.
    kite = KiteConnect(api_key=api_key)
    login_url = kite.login_url()  # https://kite.zerodha.com/connect/login?api_key=...&v=3

    request_token = None
    candidate_urls = []
    try:
        resp = session.get(login_url, allow_redirects=True, timeout=30)
        candidate_urls.append(resp.url)
        candidate_urls.extend(h.headers.get("Location", "") for h in resp.history)
        candidate_urls.extend(h.url for h in resp.history)
    except requests.exceptions.RequestException as exc:
        # The app's redirect URL may be unreachable (e.g. a localhost/postback URL).
        # The request_token still lives in the URL requests tried to reach.
        req = getattr(exc, "request", None)
        if req is not None:
            candidate_urls.append(req.url)

    request_token = _extract_request_token(candidate_urls)
    if not request_token:
        raise RuntimeError(
            "Could not extract request_token from the login redirect. "
            "Candidate URLs: " + repr(candidate_urls) + "\n"
            "Common causes: the Connect app requires a one-time consent/authorize "
            "step in the browser, or the app's redirect URL is misconfigured in the "
            "Kite developer console."
        )

    # Step 4 — exchange for access_token
    data = kite.generate_session(request_token, api_secret=api_secret)
    return data["access_token"]


def _persist_token(token):
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump({"access_token": token}, f)

    # GitHub Actions integration
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        # Register a log mask so the value is redacted everywhere it appears.
        print(f"::add-mask::{token}")
        with open(gh_out, "a", encoding="utf-8") as f:
            f.write(f"access_token={token}\n")


def main():
    env = _read_env()
    token = get_access_token(
        api_key=env["KITE_API_KEY"],
        api_secret=env["KITE_API_SECRET"],
        user_id=env["KITE_USER_ID"],
        password=env["KITE_PASSWORD"],
        totp_secret=env["KITE_TOTP_SECRET"],
    )
    _persist_token(token)
    # Never print the token itself.
    print("Access token generated and saved to kite_access_token.json (masked in CI).")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001 — surface a clean error, hide stack secrets
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
