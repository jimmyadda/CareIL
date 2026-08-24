"""Transactional email delivery through Resend's HTTPS API."""

import base64
import json
import os
from email.utils import parseaddr
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


RESEND_API_URL = "https://api.resend.com/emails"


def resend_is_configured():
    return bool(os.environ.get("RESEND_API_KEY") and os.environ.get("CAREIL_FROM_EMAIL"))


def resend_from_email():
    return os.environ.get("CAREIL_FROM_EMAIL", "CareIL <noreply@mail.careil.net>")


def resend_sender_address():
    return parseaddr(resend_from_email())[1] or "noreply@mail.careil.net"


def encoded_attachment(content, filename, content_type=None, content_id=None):
    if isinstance(content, str):
        content = content.encode("utf-8")
    attachment = {
        "content": base64.b64encode(content).decode("ascii"),
        "filename": filename,
    }
    if content_type:
        attachment["content_type"] = content_type
    if content_id:
        attachment["content_id"] = content_id
    return attachment


def careil_logo_attachment(project_root):
    logo_path = os.path.join(
        project_root, "static", "img", "therapy-hands-logo-email.png"
    )
    with open(logo_path, "rb") as logo_file:
        return encoded_attachment(
            logo_file.read(), "careil.png", "image/png", "careil-logo"
        )


def send_resend_email(to, subject, html, text=None, attachments=None):
    """Send one transactional email and return Resend's response payload."""
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        raise RuntimeError("RESEND_API_KEY is not configured")
    if not os.environ.get("CAREIL_FROM_EMAIL"):
        raise RuntimeError("CAREIL_FROM_EMAIL is not configured")

    payload = {
        "from": resend_from_email(),
        "to": [to] if isinstance(to, str) else list(to),
        "subject": subject,
        "html": html,
    }
    if text:
        payload["text"] = text
    if attachments:
        payload["attachments"] = attachments

    request = Request(
        RESEND_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json",
            "User-Agent": "CareIL/1.0",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Resend rejected the email ({exc.code}): {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach Resend: {exc.reason}") from exc
