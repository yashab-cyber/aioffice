"""Telegram bot — sends daily reports to the director."""

from __future__ import annotations

import logging
import httpx
from config import settings

logger = logging.getLogger("aioffice")

_BASE = "https://api.telegram.org/bot{token}"


async def send_telegram_message(text: str, parse_mode: str = "Markdown") -> bool:
    """Send a message to the configured Telegram chat."""
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        logger.warning("Telegram not configured — skipping send")
        return False

    url = f"{_BASE.format(token=settings.telegram_bot_token)}/sendMessage"
    payload = {
        "chat_id": settings.telegram_chat_id,
        "text": text[:4096],  # Telegram message limit
        "parse_mode": parse_mode,
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload)
            data = resp.json()
            if data.get("ok"):
                logger.info("Telegram message sent successfully")
                return True
            else:
                logger.error(f"Telegram API error: {data}")
                return False
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")
        return False


async def send_daily_report(reports: list[str]) -> bool:
    """Format and send the combined daily report to Telegram."""
    header = f"🏢 *{settings.company_name} — Daily Office Report*\n"
    header += "━" * 30 + "\n\n"
    body = "\n\n".join(reports)
    footer = "\n\n━" * 30
    footer += f"\n_Sent by AI Office_"

    full_message = header + body + footer

    # Split into chunks if too long
    if len(full_message) <= 4096:
        return await send_telegram_message(full_message)

    # Split into multiple messages
    chunks = [full_message[i:i+4000] for i in range(0, len(full_message), 4000)]
    success = True
    for chunk in chunks:
        if not await send_telegram_message(chunk):
            success = False
    return success
