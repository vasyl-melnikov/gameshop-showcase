import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.email_sender import GmailEmailSender, MockEmailSender, get_email_sender


@pytest.mark.asyncio
async def test_gmail_email_sender_connect():
    # Mock SMTP connection
    mock_smtp = AsyncMock()

    # Patch the aiosmtplib.SMTP class to use our mock
    with patch("app.email_sender.aiosmtplib.SMTP", return_value=mock_smtp):
        email_sender = GmailEmailSender(
            host="smtp.gmail.com",
            port=587,
            user="testuser",
            password="testpassword",
        )

        # Call the connect method
        await email_sender.connect()

        # Ensure that the connect method of SMTP is called
        mock_smtp.connect.assert_called_once()
        mock_smtp.login.assert_called_once_with("testuser", "testpassword")


@pytest.mark.asyncio
async def test_gmail_email_sender_send_message():
    # Mock the SMTP connection and send_message method
    mock_smtp = AsyncMock()
    with patch("app.email_sender.aiosmtplib.SMTP", return_value=mock_smtp):
        email_sender = GmailEmailSender(
            host="smtp.gmail.com",
            port=587,
            user="testuser",
            password="testpassword",
        )

        # Prepare data for the message
        subject = "Test Subject"
        text = "Test Email Content"
        to = ["recipient@example.com"]
        cc = ["cc@example.com"]

        # Call the send_message method
        await email_sender.send_message(subject, text, to, cc)

        # Ensure send_message method is called
        mock_smtp.send_message.assert_called_once()
        msg = mock_smtp.send_message.call_args[0][
            0]  # The first argument is the message object
        assert msg["Subject"] == subject
        assert msg["From"] == "testuser"
        assert msg["To"] == ", ".join(to)
        assert msg["Cc"] == ", ".join(cc)
        assert msg.get_payload() == text


@pytest.mark.asyncio
async def test_gmail_email_sender_close():
    # Mock the SMTP connection
    mock_smtp = AsyncMock()
    with patch("app.email_sender.aiosmtplib.SMTP", return_value=mock_smtp):
        email_sender = GmailEmailSender(
            host="smtp.gmail.com",
            port=587,
            user="testuser",
            password="testpassword",
        )

        # Call the close method
        await email_sender.close()

        # Ensure the quit method was called to close the connection
        mock_smtp.quit.assert_called_once()


@pytest.mark.asyncio
async def test_mock_email_sender_send_message():
    # Create an instance of MockEmailSender
    mock_email_sender = MockEmailSender()

    # Patch the print function to capture print statements
    with patch("builtins.print") as mock_print:
        subject = "Test Subject"
        text = "Test Email Content"
        to = ["recipient@example.com"]

        # Call the send_message method
        await mock_email_sender.send_message(subject, text, to)

        # Ensure print is called with the email content
        mock_print.assert_called_once_with(text)


@pytest.mark.asyncio
async def test_get_email_sender():
    # Mock the settings to provide user credentials
    mock_settings = MagicMock()
    mock_settings.email_sender.user = "testuser"
    mock_settings.email_sender.host = "smtp.gmail.com"
    mock_settings.email_sender.port = 587
    mock_settings.email_sender.password = "testpassword"

    with patch("app.settings.settings", mock_settings):
        # Patch the GmailEmailSender initialization
        with patch("app.email_sender.GmailEmailSender") as mock_gmail_sender:
            mock_gmail_sender.return_value = MagicMock()
            email_sender = await get_email_sender()

            # Check that the GmailEmailSender was initialized
            mock_gmail_sender.assert_called_once_with(
                host="smtp.gmail.com",
                port=587,
                user="testuser",
                password="testpassword",
            )
            assert email_sender is mock_gmail_sender.return_value
