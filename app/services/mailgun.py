"""Mailgun email forwarding helper."""
import httpx

from app.config import settings


async def forward_email(
    to: str,
    subject: str,
    from_address: str,
    text: str,
    attachments: list[tuple[str, bytes]] | None = None,
) -> None:
    """Forward an email via Mailgun."""
    data = {
        "from": f"Juggle Forwarder <noreply@{settings.MAILGUN_DOMAIN}>",
        "to": to,
        "subject": f"Fwd: {subject}",
        "text": text,
    }
    files = []
    if attachments:
        for filename, content in attachments:
            files.append(("attachment", (filename, content, "application/pdf")))

    async with httpx.AsyncClient() as client:
        await client.post(
            f"https://api.mailgun.net/v3/{settings.MAILGUN_DOMAIN}/messages",
            auth=("api", settings.MAILGUN_API_KEY),
            data=data,
            files=files or None,
        )
