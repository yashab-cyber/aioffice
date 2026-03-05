"""Telegram Bot — rich notifications, commands, inline keyboards, polling, reports."""

from __future__ import annotations

import asyncio
import hashlib
import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from config import settings

logger = logging.getLogger("aioffice")

_BASE = "https://api.telegram.org/bot{token}"

# ── In-memory message log ─────────────────────────────────
_message_log: list[dict] = []
_MAX_LOG = 300


def _log_msg(chat_id: str, text_preview: str, status: str, msg_type: str = "text", error: str = ""):
    entry = {
        "chat_id": chat_id,
        "preview": text_preview[:120],
        "status": status,
        "type": msg_type,
        "error": error,
        "sent_at": datetime.now(timezone.utc).isoformat(),
    }
    _message_log.append(entry)
    if len(_message_log) > _MAX_LOG:
        _message_log.pop(0)
    return entry


def _is_configured() -> bool:
    return bool(settings.telegram_bot_token and settings.telegram_chat_id)


def _api_url(method: str) -> str:
    return f"{_BASE.format(token=settings.telegram_bot_token)}/{method}"


# ── Core API Calls ────────────────────────────────────────

async def _api_call(method: str, payload: dict, timeout: float = 15.0) -> dict:
    """Make a Telegram Bot API call. Returns the API response dict."""
    if not _is_configured():
        logger.warning("Telegram not configured — skipping API call")
        return {"ok": False, "error": "Not configured"}

    url = _api_url(method)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload)
            data = resp.json()
            if not data.get("ok"):
                logger.error(f"Telegram API error ({method}): {data.get('description', data)}")
            return data
    except Exception as e:
        logger.error(f"Telegram API call failed ({method}): {e}")
        return {"ok": False, "error": str(e)}


# ── Send Messages ─────────────────────────────────────────

async def send_message(
    text: str,
    chat_id: str = "",
    parse_mode: str = "Markdown",
    disable_preview: bool = False,
    reply_to_message_id: int | None = None,
) -> dict:
    """Send a text message to a Telegram chat."""
    cid = chat_id or settings.telegram_chat_id
    if not cid:
        return _log_msg("", text, "skipped", error="No chat_id")

    payload: dict[str, Any] = {
        "chat_id": cid,
        "text": text[:4096],
        "parse_mode": parse_mode,
        "disable_web_page_preview": disable_preview,
    }
    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id

    result = await _api_call("sendMessage", payload)
    if result.get("ok"):
        logger.info(f"📱 Telegram message sent to {cid}")
        return _log_msg(cid, text, "sent")
    else:
        return _log_msg(cid, text, "failed", error=result.get("description", result.get("error", "")))


async def send_html_message(text: str, chat_id: str = "") -> dict:
    """Send an HTML-formatted message."""
    return await send_message(text, chat_id=chat_id, parse_mode="HTML")


async def send_photo(
    photo_url: str,
    caption: str = "",
    chat_id: str = "",
    parse_mode: str = "Markdown",
) -> dict:
    """Send a photo by URL with optional caption."""
    cid = chat_id or settings.telegram_chat_id
    payload = {
        "chat_id": cid,
        "photo": photo_url,
        "caption": caption[:1024],
        "parse_mode": parse_mode,
    }
    result = await _api_call("sendPhoto", payload)
    status = "sent" if result.get("ok") else "failed"
    return _log_msg(cid, f"[photo] {caption}", status, "photo")


async def send_document(
    document_url: str,
    caption: str = "",
    chat_id: str = "",
) -> dict:
    """Send a document by URL with optional caption."""
    cid = chat_id or settings.telegram_chat_id
    payload = {
        "chat_id": cid,
        "document": document_url,
        "caption": caption[:1024],
    }
    result = await _api_call("sendDocument", payload)
    status = "sent" if result.get("ok") else "failed"
    return _log_msg(cid, f"[document] {caption}", status, "document")


# ── Inline Keyboard ───────────────────────────────────────

async def send_with_buttons(
    text: str,
    buttons: list[list[dict]],
    chat_id: str = "",
    parse_mode: str = "Markdown",
) -> dict:
    """
    Send a message with inline keyboard buttons.
    
    buttons format: [[{"text": "Button 1", "url": "https://..."}, {"text": "Button 2", "callback_data": "btn2"}]]
    Each inner list is a row of buttons.
    """
    cid = chat_id or settings.telegram_chat_id
    payload = {
        "chat_id": cid,
        "text": text[:4096],
        "parse_mode": parse_mode,
        "reply_markup": {"inline_keyboard": buttons},
    }
    result = await _api_call("sendMessage", payload)
    status = "sent" if result.get("ok") else "failed"
    return _log_msg(cid, text, status, "keyboard")


# ── Formatted Notifications ──────────────────────────────

async def send_alert(
    title: str,
    message: str,
    severity: str = "info",
    chat_id: str = "",
) -> dict:
    """Send a formatted alert notification with emoji severity indicators."""
    icons = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "🚨",
        "critical": "🔴",
    }
    icon = icons.get(severity, "📢")
    text = f"{icon} *{title}*\n\n{message}\n\n_{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_"
    return await send_message(text, chat_id=chat_id)


async def send_agent_update(
    agent_id: str,
    agent_role: str,
    task_type: str,
    summary: str,
    status: str = "completed",
) -> dict:
    """Send a formatted agent task update."""
    icons = {"completed": "✅", "failed": "❌", "timeout": "⏰", "working": "🔄"}
    icon = icons.get(status, "📋")
    text = (
        f"{icon} *Agent Update: {agent_role}*\n"
        f"Agent: `{agent_id}`\n"
        f"Task: `{task_type}`\n"
        f"Status: {status}\n\n"
        f"{summary[:2000]}\n\n"
        f"_{datetime.now(timezone.utc).strftime('%H:%M UTC')}_"
    )
    return await send_message(text)


async def send_metric_report(metrics: dict) -> dict:
    """Send formatted metrics/KPI report."""
    lines = ["📊 *Office Metrics Report*\n"]
    for key, value in metrics.items():
        if isinstance(value, (int, float)):
            lines.append(f"• {key}: `{value}`")
        elif isinstance(value, dict):
            lines.append(f"\n*{key}*:")
            for k, v in value.items():
                lines.append(f"  • {k}: `{v}`")
        else:
            lines.append(f"• {key}: {value}")
    lines.append(f"\n_{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_")
    return await send_message("\n".join(lines))


# ── Long Message Handling ─────────────────────────────────

async def _send_long_message(text: str, chat_id: str = "", parse_mode: str = "Markdown") -> list[dict]:
    """Split and send messages that exceed Telegram's 4096 char limit."""
    if len(text) <= 4096:
        return [await send_message(text, chat_id=chat_id, parse_mode=parse_mode)]

    chunks = []
    while text:
        if len(text) <= 4096:
            chunks.append(text)
            break
        # Try to split at a newline near the limit
        split_at = text.rfind("\n", 0, 4000)
        if split_at == -1:
            split_at = 4000
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")

    results = []
    for chunk in chunks:
        result = await send_message(chunk, chat_id=chat_id, parse_mode=parse_mode)
        results.append(result)
        await asyncio.sleep(0.5)  # avoid rate limits
    return results


# ── Daily Report ──────────────────────────────────────────

async def send_daily_report(reports: list[str], chat_id: str = "") -> dict:
    """Format and send the combined daily office report to Telegram."""
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    header = f"🏢 *{settings.company_name} — Daily Office Report*\n"
    header += f"📅 {date}\n"
    header += "━" * 30 + "\n"

    body_parts = []
    for report in reports:
        body_parts.append(report)

    body = "\n\n".join(body_parts)

    footer = "\n\n━" * 1
    footer += "━" * 29
    footer += f"\n🤖 _AI Office v2.0 — {len(reports)} agents reported_"

    full_message = header + "\n" + body + footer

    # Send (handles splitting if too long)
    results = await _send_long_message(full_message, chat_id=chat_id)

    # Also send a quick summary with buttons
    total_done = body.count("✅")
    total_failed = body.count("❌") + body.count("⏰")
    summary = f"📋 *Report Summary*: {total_done} tasks done, {total_failed} issues"

    await send_with_buttons(
        summary,
        [[
            {"text": "🌐 Open Dashboard", "url": f"http://localhost:{settings.port}"},
            {"text": "📊 Full Report", "callback_data": "full_report"},
        ]],
        chat_id=chat_id,
    )

    sent = sum(1 for r in results if r.get("status") == "sent")
    return {
        "status": "sent" if sent > 0 else "failed",
        "messages_sent": sent,
        "total_chunks": len(results),
        "report_date": date,
        "agents_reported": len(reports),
    }


# ── Cycle Notification ───────────────────────────────────

async def send_cycle_summary(
    cycle: int,
    agents_summary: dict[str, dict],
    chat_id: str = "",
) -> dict:
    """Send a summary after each work cycle completes."""
    lines = [f"🔄 *Work Cycle {cycle} Complete*\n"]
    total_done = 0
    total_failed = 0

    for agent_id, info in agents_summary.items():
        done = info.get("completed", 0)
        failed = info.get("failed", 0)
        total_done += done
        total_failed += failed
        status_icon = "🟢" if failed == 0 else "🟡" if failed < done else "🔴"
        lines.append(f"{status_icon} `{agent_id}`: {done}✅ {failed}❌")

    lines.append(f"\n*Total*: {total_done} completed, {total_failed} failed")
    lines.append(f"_{datetime.now(timezone.utc).strftime('%H:%M UTC')}_")

    return await send_message("\n".join(lines), chat_id=chat_id)


# ── Polling for Commands ─────────────────────────────────

_last_update_id = 0


async def get_updates(timeout: int = 0) -> list[dict]:
    """Poll for new messages/commands from Telegram (long-polling)."""
    global _last_update_id
    if not _is_configured():
        return []

    payload: dict[str, Any] = {"offset": _last_update_id + 1, "timeout": timeout, "limit": 10}
    result = await _api_call("getUpdates", payload, timeout=float(timeout + 10))

    updates = []
    if result.get("ok"):
        for update in result.get("result", []):
            _last_update_id = max(_last_update_id, update["update_id"])
            msg = update.get("message", {})
            text = msg.get("text", "")
            from_user = msg.get("from", {})
            updates.append({
                "update_id": update["update_id"],
                "chat_id": str(msg.get("chat", {}).get("id", "")),
                "text": text,
                "from_user": from_user.get("username", from_user.get("first_name", "unknown")),
                "is_command": text.startswith("/"),
                "command": text.split()[0][1:] if text.startswith("/") else "",
                "args": text.split()[1:] if text.startswith("/") and len(text.split()) > 1 else [],
            })
    return updates


async def process_commands(updates: list[dict]) -> list[dict]:
    """Process incoming commands and return responses to send."""
    responses = []
    for update in updates:
        if not update.get("is_command"):
            continue

        cmd = update["command"]
        args = update.get("args", [])
        chat_id = update["chat_id"]

        if cmd == "status":
            responses.append({"chat_id": chat_id, "action": "status"})
        elif cmd == "report":
            responses.append({"chat_id": chat_id, "action": "report"})
        elif cmd == "agents":
            responses.append({"chat_id": chat_id, "action": "agents"})
        elif cmd == "health":
            responses.append({"chat_id": chat_id, "action": "health"})
        elif cmd == "delegate" and args:
            agent = args[0] if args else "ceo"
            task = " ".join(args[1:]) if len(args) > 1 else ""
            responses.append({"chat_id": chat_id, "action": "delegate", "agent": agent, "task": task})
        elif cmd == "message" and args:
            to = args[0] if args else "ceo"
            content = " ".join(args[1:]) if len(args) > 1 else ""
            responses.append({"chat_id": chat_id, "action": "message", "to": to, "content": content})
        elif cmd == "help":
            help_text = (
                "🤖 *AI Office Bot Commands*\n\n"
                "/status — Office status overview\n"
                "/report — Force generate daily report\n"
                "/agents — List all agents\n"
                "/health — Health check\n"
                "/delegate `agent` `task` — Delegate task to agent\n"
                "/message `agent` `text` — Message an agent\n"
                "/help — Show this help"
            )
            await send_message(help_text, chat_id=chat_id)
        else:
            await send_message(f"❓ Unknown command: /{cmd}\nType /help for available commands.", chat_id=chat_id)

    return responses


# ── Bot Info ──────────────────────────────────────────────

async def get_bot_info() -> dict:
    """Fetch bot information from Telegram API."""
    if not _is_configured():
        return {"configured": False}
    result = await _api_call("getMe", {})
    if result.get("ok"):
        bot = result["result"]
        return {
            "configured": True,
            "bot_id": bot.get("id"),
            "username": bot.get("username"),
            "first_name": bot.get("first_name"),
            "can_read_messages": bot.get("can_read_all_group_messages", False),
        }
    return {"configured": True, "error": result.get("description", "Unknown error")}


# ── Analytics ─────────────────────────────────────────────

def get_telegram_stats() -> dict:
    """Return Telegram messaging statistics."""
    if not _message_log:
        return {"total": 0, "sent": 0, "failed": 0, "configured": _is_configured()}

    total = len(_message_log)
    by_status = {}
    by_type = {}

    for entry in _message_log:
        status = entry["status"]
        by_status[status] = by_status.get(status, 0) + 1
        msg_type = entry.get("type", "text")
        by_type[msg_type] = by_type.get(msg_type, 0) + 1

    return {
        "total": total,
        "sent": by_status.get("sent", 0),
        "failed": by_status.get("failed", 0),
        "skipped": by_status.get("skipped", 0),
        "by_type": by_type,
        "configured": _is_configured(),
        "chat_id": settings.telegram_chat_id or "not set",
    }


def get_message_log(limit: int = 50) -> list[dict]:
    """Return recent Telegram message log entries."""
    return _message_log[-limit:]
