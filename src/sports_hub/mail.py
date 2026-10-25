"""Sending email: one small interface and a Gmail implementation.

Settings come only from environment variables (GitHub secrets on the real
runs). Nothing here ever prints, logs or raises with an address or password
in the message. This module uses only Python's standard library, so the
workflow's last-resort failure email can use it even when installing the
project failed. (The fake sender for tests lives in tests/conftest.py.)
"""

from __future__ import annotations

import smtplib
import ssl
from dataclasses import dataclass, field
from email.message import EmailMessage
from typing import Mapping, Protocol

GMAIL_HOST = "smtp.gmail.com"
GMAIL_PORT = 465

ENV_USER = "SPORTS_HUB_MAIL_USER"
ENV_APP_PASSWORD = "SPORTS_HUB_MAIL_APP_PASSWORD"
ENV_ALERT_TO = "SPORTS_HUB_ALERT_TO"
ENV_HUB_URL = "SPORTS_HUB_URL"
REQUIRED = (ENV_USER, ENV_APP_PASSWORD, ENV_ALERT_TO)


class MailError(Exception):
    """An email couldn't be sent. The message never contains credentials or addresses."""


@dataclass(frozen=True)
class Message:
    to: tuple[str, ...]
    subject: str
    text: str


class MailSender(Protocol):
    def send(self, message: Message) -> None: ...


@dataclass(frozen=True)
class MailSettings:
    user: str
    app_password: str = field(repr=False)
    alert_to: tuple[str, ...]
    hub_url: str | None

    @staticmethod
    def missing(env: Mapping[str, str]) -> list[str]:
        return [name for name in REQUIRED if not env.get(name)]

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> "MailSettings":
        missing = cls.missing(env)
        if missing:
            raise MailError("mail settings are missing: " + ", ".join(missing))
        return cls(
            user=env[ENV_USER],
            app_password=env[ENV_APP_PASSWORD],
            alert_to=tuple(a.strip() for a in env[ENV_ALERT_TO].split(",") if a.strip()),
            hub_url=env.get(ENV_HUB_URL) or None,
        )


class GmailSender:
    """Sends from a Gmail account with an app password. Recipients go in Bcc,
    so nobody sees anyone else's address."""

    def __init__(self, settings: MailSettings) -> None:
        self._settings = settings

    def send(self, message: Message) -> None:
        try:
            email = EmailMessage()
            email["From"] = f"Sports Hub <{self._settings.user}>"
            email["To"] = f"Sports Hub <{self._settings.user}>"
            email["Bcc"] = ", ".join(message.to)
            email["Subject"] = message.subject
            email.set_content(message.text)
        except (ValueError, TypeError):
            raise MailError("an email address in the mail settings isn't valid") from None
        try:
            with smtplib.SMTP_SSL(GMAIL_HOST, GMAIL_PORT, context=ssl.create_default_context(), timeout=30) as smtp:
                smtp.login(self._settings.user, self._settings.app_password)
                smtp.send_message(email)
        except smtplib.SMTPAuthenticationError:
            raise MailError("Gmail rejected the sign-in; check the app password secret") from None
        except (smtplib.SMTPException, OSError) as exc:
            raise MailError(f"Gmail couldn't be reached or refused the email ({type(exc).__name__})") from None
