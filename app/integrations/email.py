import asyncio
import smtplib
from email.message import EmailMessage

from app.core.config import get_settings


class EmailProviderError(Exception):
    pass


def _send_email_sync(to_email: str, subject: str, html_body: str) -> None:
    settings = get_settings()

    if not settings.smtp_host or not settings.smtp_port or not settings.smtp_username or not settings.smtp_password:
        raise EmailProviderError("SMTP configuration is incomplete")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from_email
    msg["To"] = to_email
    msg.set_content("Please use an HTML compatible email client.")
    msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
        if settings.smtp_use_tls:
            server.starttls()
        server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(msg)


async def send_verification_email(to_email: str, verification_link: str) -> None:
    settings = get_settings()
    if not settings.email_enabled:
        return

    subject = "Verify your email - Real Estate"
    html_body = (
        "<p>Hi,</p>"
        "<p>Please verify your email by clicking the link below:</p>"
        f"<p><a href=\"{verification_link}\">Verify Email</a></p>"
        "<p>If you did not request this, please ignore this message.</p>"
    )

    await asyncio.to_thread(_send_email_sync, to_email, subject, html_body)
