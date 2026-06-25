import smtplib
import logging
import json
import urllib.request
from datetime import datetime, timezone
from email.mime.text import MIMEText
from typing import Optional
import config

logger = logging.getLogger(__name__)


def log_event(lead_id: int, contact: str, source: Optional[str]) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] NEW LEAD id={lead_id} contact={contact} source={source}\n"
    with open(config.LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line)


def send_email(
    lead_id: int,
    name: Optional[str],
    contact: str,
    source: Optional[str],
    comment: Optional[str],
) -> None:
    if not all([config.SMTP_USER, config.SMTP_PASS, config.MANAGER_EMAIL]):
        logger.warning("Email config incomplete — skipping notification")
        return

    body = (
        f"Neue Lead-Anfrage #{lead_id}\n\n"
        f"Name:    {name or '—'}\n"
        f"Contact: {contact}\n"
        f"Source:  {source or '—'}\n"
        f"Comment: {comment or '—'}\n"
    )
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = f"Neue Lead-Anfrage #{lead_id}"
    msg["From"] = config.SMTP_USER
    msg["To"] = config.MANAGER_EMAIL

    try:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(config.SMTP_USER, config.SMTP_PASS)
            smtp.send_message(msg)
    except Exception as e:
        logger.error(f"Failed to send email for lead {lead_id}: {e}")


def _post_json(url: str, payload: dict) -> None:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    urllib.request.urlopen(req, timeout=10)


def send_to_sheet(
    lead_id: int,
    name: Optional[str],
    contact: str,
    source: Optional[str],
    comment: Optional[str],
    consent: bool,
) -> None:
    if not config.SHEETS_WEBHOOK_URL:
        logger.warning("Sheets webhook not configured — skipping")
        return

    payload = {
        "id": lead_id,
        "name": name or "",
        "contact": contact,
        "source": source or "",
        "comment": comment or "",
        "consent": consent,
    }
    try:
        _post_json(config.SHEETS_WEBHOOK_URL, payload)
    except Exception as e:
        logger.error(f"Failed to send lead {lead_id} to sheet: {e}")
