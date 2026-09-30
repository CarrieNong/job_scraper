"""
Lightweight Telegram Bot API helper for scrapers (sync, no PTB dependency).

Uses TELEGRAM_BOT_TOKEN + TELEGRAM_ALLOWED_USER_ID from the environment.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_PROJECT_ROOT / ".env")


def _bot_token() -> str:
    return (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()


def _chat_id() -> Optional[int]:
    raw = (os.getenv("TELEGRAM_ALLOWED_USER_ID") or "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def send_telegram_message(
    text: str,
    *,
    reply_markup: Optional[dict[str, Any]] = None,
    parse_mode: Optional[str] = None,
    disable_web_page_preview: bool = True,
) -> bool:
    """
    Send a message to the allowed user via Telegram Bot API.

    Returns True on HTTP success. Failures are logged and return False
    (scrapers should keep working without Telegram).
    """
    token = _bot_token()
    chat_id = _chat_id()
    if not token or chat_id is None:
        print("⚠ Telegram notify skipped: TELEGRAM_BOT_TOKEN / TELEGRAM_ALLOWED_USER_ID missing")
        return False

    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": disable_web_page_preview,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = json.loads(response.read().decode("utf-8") or "{}")
        if not body.get("ok"):
            print(f"⚠ Telegram notify rejected: {body}")
            return False
        return True
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        print(f"⚠ Telegram notify failed: {type(exc).__name__}: {exc}")
        return False


def indeed_challenge_keyboard() -> dict[str, Any]:
    """Inline keyboard: Continue button → callback_data indeed_resume."""
    return {
        "inline_keyboard": [
            [{"text": "✅ Continue", "callback_data": "indeed_resume"}]
        ]
    }
