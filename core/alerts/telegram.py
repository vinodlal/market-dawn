"""Telegram push: the morning brief, formatted for a phone notification.

Credentials come from the encrypted keyring (core.security.credentials) —
never printed, never logged. The bot token/chat id are optional secrets; if
unset, send_brief() raises a clear error rather than failing silently.

Formatting uses Telegram's HTML parse mode for real visual hierarchy (bold
section headers, italics) instead of a flat plain-text dump — the original
M7 version worked (delivery was proven) but read poorly on a phone. This is
a pure string-formatting improvement, zero LLM calls, per the explicit
low-token-usage constraint on any brief-quality work.
"""
from __future__ import annotations

import html
from datetime import datetime

import requests

from ..security import credentials as creds

API_BASE = "https://api.telegram.org/bot{token}/{method}"
MAX_LEN = 4096

_SENTIMENT_ARROW = {"bullish": "▲", "bearish": "▼", "neutral": "●"}
_BIAS_ARROW = {"Long": "▲", "Short": "▼", "Neutral": "●"}


def send_message(text: str, parse_mode: str | None = None) -> dict:
    token = creds.require("TELEGRAM_BOT_TOKEN")
    chat_id = creds.require("TELEGRAM_CHAT_ID")
    url = API_BASE.format(token=token, method="sendMessage")
    payload = {"chat_id": chat_id, "text": text[:MAX_LEN]}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    resp = requests.post(url, data=payload, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _esc(value) -> str:
    """Escape for Telegram HTML — headlines/status text are dynamic and may
    contain '<', '>', '&', which would otherwise break message parsing."""
    return html.escape(str(value), quote=False)


def _fmt_dt(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%d %b %Y, %H:%M IST")
    except ValueError:
        return iso


def format_brief_message(brief: dict) -> str:
    lines = ["<b>MarketDawn — Pre-open Brief</b>", f"<i>{_esc(_fmt_dt(brief['generated_at']))}</i>", ""]
    lines.append(_esc(brief["status"]))
    lines.append("")

    lines.append("<b>Snapshot</b>")
    for name, tile in brief.get("snapshot", {}).items():
        price, cp = tile.get("last_price"), tile.get("change_pct")
        if price is None:
            lines.append(f"{_esc(name)}: unavailable")
        elif cp is None:
            lines.append(f"{_esc(name)}: {price:,.2f}")
        else:
            arrow = "▲" if cp > 0 else ("▼" if cp < 0 else "●")
            lines.append(f"{_esc(name)}  {price:,.2f}  {arrow} {cp:+.2f}%")
    if brief.get("pcr") is not None:
        lines.append(f"PCR (Bank Nifty): {brief['pcr']}")
    lines.append("")

    if brief.get("top_signals"):
        lines.append("<b>Top signals</b>")
        for sig in brief["top_signals"]:
            arrow = _BIAS_ARROW.get(sig["bias"], "●")
            lines.append(f"<b>{_esc(sig['symbol'])}</b> {arrow} {_esc(sig['bias']).upper()} "
                         f"(score {sig['score']}, {_esc(sig['confidence'])} confidence)")
            for reason in sig.get("reasons", [])[:2]:
                lines.append(f"  • {_esc(reason)}")
        lines.append("")

    news = brief.get("news", {})
    for label, key in (("India news", "india"), ("Global news", "global")):
        headlines = news.get(key, [])[:3]
        if headlines:
            lines.append(f"<b>{label}</b>")
            for h in headlines:
                arrow = _SENTIMENT_ARROW.get(h["sentiment"], "●")
                lines.append(f"{arrow} {_esc(h['title'])}")
            lines.append("")

    lines.append(f"<i>{_esc(brief['disclaimer'])}</i>")
    return "\n".join(lines)


def send_brief(brief: dict) -> dict:
    return send_message(format_brief_message(brief), parse_mode="HTML")
