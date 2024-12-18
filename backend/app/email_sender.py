from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Protocol

import aiosmtplib

from app.settings import settings


class EmailSender(Protocol):
    async def connect(self): ...

    async def send_message(
        self,
        subject: str,
        text: str,
        to: list[str],
        cc: list[str] | None = None,
        text_type: str = "plain",
    ): ...

    async def close(self): ...


class GmailEmailSender:
    def __init__(
        self, host: str, port: int, user: str, password: str, sender: str | None = None
    ):
        self.smtp = aiosmtplib.SMTP(hostname=host, port=port, start_tls=True)
        self.user = user
        self.password = password
        self.sender = sender or self.user

    async def connect(self):
        if self.smtp.is_connected:
            return
        await self.smtp.connect()
        await self.smtp.login(self.user, self.password)

    async def send_message(
        self,
        subject: str,
        text: str,
        to: list[str],
        cc: list[str] | None = None,
        text_type: str = "plain",
    ):
        await self.connect()

        msg = MIMEMultipart()
        msg.preamble = subject
        msg["Subject"] = subject
        msg["From"] = self.sender
        msg["To"] = ", ".join(to)

        if cc is not None:
            msg["Cc"] = ", ".join(cc)

        msg.attach(MIMEText(text, text_type, "utf-8"))

        await self.smtp.send_message(msg)

    async def close(self):
        if self.smtp.is_connected:
            await self.smtp.quit()


class MockEmailSender:
    def __init__(self, *_, **__): ...

    async def send_message(
        self,
        subject: str,
        text: str,
        to: list[str],
        cc: list[str] | None = None,
        text_type: str = "plain",
    ):
        print(text)

    async def connect(self): ...

    async def close(self): ...


_email_sender: EmailSender | None = None


async def get_email_sender() -> EmailSender:
    global _email_sender

    if _email_sender is None:
        if not settings.email_sender.user:
            _email_sender = MockEmailSender()
        _email_sender = GmailEmailSender(
            host=settings.email_sender.host,
            port=settings.email_sender.port,
            user=settings.email_sender.user,
            password=settings.email_sender.password,
        )
    try:
        yield _email_sender
    finally:
        if _email_sender:
            await _email_sender.close()
