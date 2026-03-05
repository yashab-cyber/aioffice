"""Advanced email tool — campaigns, drip sequences, templates, tracking, bulk send."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import re
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Any

import aiosmtplib

from config import settings

logger = logging.getLogger("aioffice")

# ── In-memory send log (persists for the process lifetime) ──
_send_log: list[dict] = []
_MAX_LOG = 500


def _log_send(to: str, subject: str, status: str, campaign: str = "", error: str = ""):
    entry = {
        "to": to,
        "subject": subject,
        "status": status,
        "campaign": campaign,
        "error": error,
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "message_id": hashlib.sha256(f"{to}{subject}{datetime.now(timezone.utc).isoformat()}".encode()).hexdigest()[:16],
    }
    _send_log.append(entry)
    if len(_send_log) > _MAX_LOG:
        _send_log.pop(0)
    return entry


def _is_configured() -> bool:
    return bool(settings.smtp_user and settings.smtp_password)


def _sanitize_html(html: str) -> str:
    """Basic sanitization — strip script tags from HTML email bodies."""
    return re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)


# ── Core Send ─────────────────────────────────────────────

async def send_email(
    to: str,
    subject: str,
    body: str,
    html: bool = False,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    reply_to: str = "",
    headers: dict[str, str] | None = None,
    campaign: str = "",
) -> dict:
    """Send a single email via SMTP. Returns a result dict with status and message_id."""
    if not _is_configured():
        logger.warning("Email not configured — skipping send")
        return _log_send(to, subject, "skipped", campaign, "SMTP not configured")

    msg = MIMEMultipart("alternative")
    msg["From"] = settings.email_from or settings.smtp_user
    msg["To"] = to
    msg["Subject"] = subject

    if cc:
        msg["Cc"] = ", ".join(cc)
    if reply_to:
        msg["Reply-To"] = reply_to

    # Custom headers (e.g. List-Unsubscribe, X-Campaign-Id)
    if headers:
        for k, v in headers.items():
            if k.lower().startswith("x-") or k.lower() in ("list-unsubscribe",):
                msg[k] = v

    if html:
        body = _sanitize_html(body)

    content_type = "html" if html else "plain"
    msg.attach(MIMEText(body, content_type, "utf-8"))

    # Build recipient list
    recipients = [to]
    if cc:
        recipients.extend(cc)
    if bcc:
        recipients.extend(bcc)

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            start_tls=True,
        )
        logger.info(f"📧 Email sent to {to}: {subject}")
        return _log_send(to, subject, "sent", campaign)
    except Exception as e:
        logger.error(f"Email send failed to {to}: {e}")
        return _log_send(to, subject, "failed", campaign, str(e))


# ── Bulk / Batch Send ────────────────────────────────────

async def send_bulk_email(
    recipients: list[dict],
    subject_template: str,
    body_template: str,
    html: bool = False,
    campaign: str = "",
    delay_between: float = 1.0,
) -> dict:
    """
    Send personalized emails to multiple recipients.
    
    Each recipient dict can have: email, name, and any custom fields for template substitution.
    Templates use {field_name} placeholders, e.g. "Hello {name}, welcome to {company}!"
    
    Returns summary with sent/failed counts.
    """
    if not _is_configured():
        return {"status": "skipped", "reason": "SMTP not configured", "sent": 0, "failed": 0}

    sent = 0
    failed = 0
    results = []

    for recipient in recipients:
        email_addr = recipient.get("email", "")
        if not email_addr:
            continue

        # Template substitution with safe defaults
        subs = {"company": settings.company_name, "product": settings.product_name, **recipient}
        try:
            subject = subject_template.format_map(_SafeDict(subs))
            body = body_template.format_map(_SafeDict(subs))
        except Exception:
            subject = subject_template
            body = body_template

        result = await send_email(email_addr, subject, body, html=html, campaign=campaign)
        results.append(result)

        if result["status"] == "sent":
            sent += 1
        else:
            failed += 1

        if delay_between > 0:
            await asyncio.sleep(delay_between)

    return {"campaign": campaign, "sent": sent, "failed": failed, "total": len(recipients), "results": results}


class _SafeDict(dict):
    """Dict that returns {key} for missing keys instead of raising KeyError."""
    def __missing__(self, key):
        return f"{{{key}}}"


# ── Email Templates ──────────────────────────────────────

TEMPLATES = {
    "welcome": {
        "subject": "Welcome to {company}, {name}! 🎉",
        "body": """Hi {name},

Welcome to {company}! We're thrilled to have you.

Here's what you can do to get started:
1. Check out our product: {product}
2. Join our community: {discord_url}
3. Star us on GitHub: {github_url}

If you have any questions, just reply to this email.

Best,
The {company} Team""",
    },
    "newsletter": {
        "subject": "{company} Weekly Update — {date}",
        "body": """Hi {name},

Here's what happened this week at {company}:

{content}

Stay tuned for more updates!

Best,
The {company} Team

---
You're receiving this because you subscribed to {company} updates.
""",
    },
    "cold_outreach": {
        "subject": "Quick question about {topic}",
        "body": """Hi {name},

I'm {sender_name} from {company}. I noticed {hook} and thought you might be interested in {product}.

{value_prop}

Would you be open to a quick chat this week?

Best,
{sender_name}
{company}""",
    },
    "follow_up": {
        "subject": "Re: {original_subject}",
        "body": """Hi {name},

Just following up on my previous email about {topic}. I wanted to share a quick update:

{update}

Let me know if you'd like to discuss further.

Best,
{sender_name}
{company}""",
    },
    "event_invite": {
        "subject": "You're invited: {event_name} 🎯",
        "body": """Hi {name},

You're invited to {event_name}!

📅 Date: {event_date}
📍 Location: {event_location}
🔗 Link: {event_link}

{event_description}

RSVP by replying to this email.

See you there!
The {company} Team""",
    },
    "report": {
        "subject": "{company} — Daily AI Office Report ({date})",
        "body": """Hi Director,

Here's your daily AI Office report for {date}:

{report_content}

---
Generated by AI Office v2.0
{company}""",
    },
}


async def send_from_template(
    to: str,
    template_name: str,
    variables: dict[str, str] | None = None,
    html: bool = False,
    campaign: str = "",
) -> dict:
    """Send an email using a named template with variable substitution."""
    template = TEMPLATES.get(template_name)
    if not template:
        return {"status": "error", "error": f"Template '{template_name}' not found", "available": list(TEMPLATES.keys())}

    subs = {
        "company": settings.company_name,
        "product": settings.product_name,
        "github_url": settings.product_github_url,
        "discord_url": settings.product_discord_url,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        **(variables or {}),
    }

    try:
        subject = template["subject"].format_map(_SafeDict(subs))
        body = template["body"].format_map(_SafeDict(subs))
    except Exception:
        subject = template["subject"]
        body = template["body"]

    return await send_email(to, subject, body, html=html, campaign=campaign or template_name)


# ── Drip Sequence ────────────────────────────────────────

async def send_drip_sequence(
    to: str,
    sequence: list[dict],
    variables: dict[str, str] | None = None,
    campaign: str = "drip",
    delay_seconds: float = 0,
) -> dict:
    """
    Send a multi-step drip email sequence.
    
    Each step in the sequence: {"subject": "...", "body": "...", "delay": 0}
    The delay is in seconds between emails (useful for testing; in production
    you'd schedule these with a task queue).
    
    Returns summary of all sends.
    """
    subs = {
        "company": settings.company_name,
        "product": settings.product_name,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        **(variables or {}),
    }

    results = []
    for i, step in enumerate(sequence):
        step_delay = step.get("delay", delay_seconds)
        if i > 0 and step_delay > 0:
            await asyncio.sleep(step_delay)

        try:
            subject = step["subject"].format_map(_SafeDict(subs))
            body = step["body"].format_map(_SafeDict(subs))
        except Exception:
            subject = step.get("subject", f"Step {i+1}")
            body = step.get("body", "")

        result = await send_email(to, subject, body, campaign=f"{campaign}_step{i+1}")
        results.append({"step": i + 1, **result})

    sent = sum(1 for r in results if r["status"] == "sent")
    return {"campaign": campaign, "to": to, "steps": len(sequence), "sent": sent, "results": results}


# ── Daily Report Email ───────────────────────────────────

async def send_daily_report_email(reports: list[str], to: str | None = None) -> dict:
    """Format and send the daily office report via email."""
    recipient = to or settings.email_from or settings.smtp_user
    if not recipient:
        return {"status": "skipped", "reason": "No email recipient configured"}

    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    content = "\n\n".join(reports)

    return await send_from_template(
        to=recipient,
        template_name="report",
        variables={"report_content": content, "date": date},
        campaign="daily_report",
    )


# ── Analytics ─────────────────────────────────────────────

def get_email_stats() -> dict:
    """Return email sending statistics."""
    if not _send_log:
        return {"total": 0, "sent": 0, "failed": 0, "skipped": 0, "campaigns": {}}

    total = len(_send_log)
    by_status = {}
    by_campaign = {}

    for entry in _send_log:
        status = entry["status"]
        by_status[status] = by_status.get(status, 0) + 1

        campaign = entry.get("campaign", "")
        if campaign:
            if campaign not in by_campaign:
                by_campaign[campaign] = {"sent": 0, "failed": 0, "total": 0}
            by_campaign[campaign]["total"] += 1
            if status == "sent":
                by_campaign[campaign]["sent"] += 1
            elif status == "failed":
                by_campaign[campaign]["failed"] += 1

    return {
        "total": total,
        "sent": by_status.get("sent", 0),
        "failed": by_status.get("failed", 0),
        "skipped": by_status.get("skipped", 0),
        "campaigns": by_campaign,
        "configured": _is_configured(),
        "from_address": settings.email_from or settings.smtp_user or "not set",
    }


def get_send_log(limit: int = 50, campaign: str = "") -> list[dict]:
    """Return recent send log entries, optionally filtered by campaign."""
    entries = _send_log
    if campaign:
        entries = [e for e in entries if e.get("campaign") == campaign]
    return entries[-limit:]


def list_templates() -> dict:
    """Return available email templates with their subjects."""
    return {name: {"subject": t["subject"]} for name, t in TEMPLATES.items()}
