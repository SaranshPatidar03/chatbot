"""Email delivery helpers (SMTP / Mailpit)."""

from __future__ import annotations

import asyncio
import smtplib
from email.message import EmailMessage

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


async def send_email(
    *,
    to_email: str,
    subject: str,
    body_text: str,
    body_html: str | None = None,
    settings: Settings | None = None,
) -> None:
    """Send an email via configured SMTP (Mailpit in local development)."""
    cfg = settings or get_settings()
    message = EmailMessage()
    message["From"] = cfg.smtp_from
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body_text)
    if body_html:
        message.add_alternative(body_html, subtype="html")

    def _send() -> None:
        with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=15) as server:
            if cfg.smtp_tls:
                server.starttls()
            if cfg.smtp_user:
                server.login(cfg.smtp_user, cfg.smtp_password)
            server.send_message(message)

    await asyncio.to_thread(_send)
    logger.info("email_sent", to=to_email, subject=subject)


async def send_password_reset_email(
    *,
    to_email: str,
    reset_token: str,
    settings: Settings | None = None,
) -> None:
    """Send password reset link to the user."""
    cfg = settings or get_settings()
    reset_url = f"{cfg.frontend_url.rstrip('/')}/reset-password?token={reset_token}"
    subject = f"{cfg.app_name} — Reset your password"
    body_text = (
        f"You requested a password reset for {cfg.app_name}.\n\n"
        f"Open this link to choose a new password:\n{reset_url}\n\n"
        "If you did not request this, you can ignore this email."
    )
    body_html = f"""
    <p>You requested a password reset for <strong>{cfg.app_name}</strong>.</p>
    <p><a href="{reset_url}">Reset your password</a></p>
    <p>If you did not request this, you can ignore this email.</p>
    """
    await send_email(
        to_email=to_email,
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        settings=cfg,
    )


async def send_verification_email(
    *,
    to_email: str,
    verification_token: str,
    settings: Settings | None = None,
) -> None:
    """Send email verification link to the user."""
    cfg = settings or get_settings()
    verify_url = f"{cfg.frontend_url.rstrip('/')}/verify-email?token={verification_token}"
    subject = f"{cfg.app_name} — Verify your email"
    body_text = (
        f"Welcome to {cfg.app_name}.\n\n"
        f"Verify your email address:\n{verify_url}\n\n"
        "If you did not create this account, you can ignore this email."
    )
    body_html = f"""
    <p>Welcome to <strong>{cfg.app_name}</strong>.</p>
    <p><a href="{verify_url}">Verify your email address</a></p>
    <p>If you did not create this account, you can ignore this email.</p>
    """
    await send_email(
        to_email=to_email,
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        settings=cfg,
    )
