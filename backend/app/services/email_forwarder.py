"""Forward raw email to user's personal inbox."""
import aiosmtplib
from email import message_from_string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import get_settings

settings = get_settings()


async def forward_email(user_email: str, raw_mime: str):
    """
    Forward raw MIME email to the user's personal email address.
    Uses Mailgun SMTP relay.
    """
    if not raw_mime:
        return

    try:
        # Parse original message
        original = message_from_string(raw_mime)
        subject = original.get("Subject", "")
        sender = original.get("From", "noreply@juggle.app")

        # Create forwarded message
        fwd = MIMEMultipart()
        fwd["From"] = f"Gio at Juggle <noreply@{settings.mailgun_domain}>"
        fwd["To"] = user_email
        fwd["Subject"] = f"Fwd: {subject}"
        fwd["Reply-To"] = sender

        # Add body
        body = MIMEText("--- מייל שועבר על ידי Juggle ---\n\n", "plain", "utf-8")
        fwd.attach(body)

        # Attach original parts
        for part in original.walk():
            if part.get_content_maintype() == "multipart":
                continue
            fwd.attach(part)

        await aiosmtplib.send(
            fwd,
            hostname="smtp.mailgun.org",
            port=587,
            username=f"postmaster@{settings.mailgun_domain}",
            password=settings.mailgun_api_key,
            start_tls=True,
        )
    except Exception as e:
        # Log but don't fail — forwarding is best-effort
        pass
