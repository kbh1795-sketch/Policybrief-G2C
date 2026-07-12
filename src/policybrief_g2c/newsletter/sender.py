from __future__ import annotations

import smtplib
from email.message import EmailMessage
from pathlib import Path

from policybrief_g2c.config import AppSettings
from policybrief_g2c.models import NewsletterIssue


class EmailSendError(RuntimeError):
    """Raised when email delivery is unsafe or fails."""


class EmailSender:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings

    def load_recipients(self) -> list[str]:
        recipients = [
            item.strip() for item in self.settings.email_recipients.split(",") if item.strip()
        ]
        path: Path = self.settings.email_recipients_file
        if path.exists():
            recipients.extend(
                line.strip()
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            )
        return list(dict.fromkeys(recipients))[: self.settings.email_batch_size]

    def send(
        self, issue: NewsletterIssue, *, dry_run: bool = True, confirm_send: bool = False
    ) -> dict[str, object]:
        recipients = self.load_recipients()
        if dry_run:
            return {"sent": False, "dry_run": True, "recipient_count": len(recipients)}
        if not self.settings.email_send_enabled or not confirm_send:
            msg = "Real sending requires EMAIL_SEND_ENABLED=true and --confirm-send"
            raise EmailSendError(msg)
        if not recipients or not self.settings.smtp_host or not self.settings.smtp_from:
            msg = "SMTP sender and at least one recipient are required"
            raise EmailSendError(msg)

        message = EmailMessage()
        message["Subject"] = issue.title
        message["From"] = self.settings.smtp_from
        message["To"] = ", ".join(recipients)
        message.set_content(issue.generated_text)
        message.add_alternative(issue.generated_html, subtype="html")
        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=30) as smtp:
            if self.settings.smtp_use_tls:
                smtp.starttls()
            if self.settings.smtp_username:
                smtp.login(self.settings.smtp_username, self.settings.smtp_password)
            smtp.send_message(message)
        return {"sent": True, "dry_run": False, "recipient_count": len(recipients)}
