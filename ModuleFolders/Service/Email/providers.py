"""
Email provider implementations.

Supports multiple email providers:
- Resend: Modern email API service
- SendGrid: Twilio's email service
- SMTP: Generic SMTP protocol
"""

import os
import smtplib
from abc import ABC, abstractmethod
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class EmailProvider(ABC):
    """Abstract base class for email providers."""

    @abstractmethod
    def send_email(
        self,
        to: str | List[str],
        subject: str,
        html: str,
        text: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send an email.

        Args:
            to: Recipient email address(es)
            subject: Email subject
            html: HTML content
            text: Plain text content
            from_email: Override sender email
            from_name: Override sender name
            reply_to: Reply-to address

        Returns:
            Dict with provider-specific response (e.g., message_id)
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is configured and available."""
        pass


class ResendProvider(EmailProvider):
    """Resend email provider implementation."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = None

    def _get_client(self):
        """Lazy load Resend client."""
        if self._client is None:
            try:
                import resend
                resend.api_key = self.api_key
                self._client = resend
            except ImportError:
                raise RuntimeError(
                    "resend package not installed. Install with: pip install resend"
                )
        return self._client

    def send_email(
        self,
        to: str | List[str],
        subject: str,
        html: str,
        text: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send email using Resend API."""
        client = self._get_client()

        # Prepare recipients
        recipients = [to] if isinstance(to, str) else to

        # Build email payload
        payload = {
            "from": f"{from_name} <{from_email}>" if from_name else from_email,
            "to": recipients,
            "subject": subject,
            "html": html,
            "text": text,
        }

        if reply_to:
            payload["reply_to"] = reply_to

        try:
            response = client.Emails.send(**payload)
            logger.info(f"Email sent via Resend: {response.get('id', 'unknown')}")
            return {
                "provider": "resend",
                "message_id": response.get("id"),
                "status": "sent",
            }
        except Exception as e:
            logger.error(f"Resend API error: {e}")
            raise

    def is_available(self) -> bool:
        """Check if Resend is available."""
        return bool(self.api_key)


class SendGridProvider(EmailProvider):
    """SendGrid email provider implementation."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = None

    def _get_client(self):
        """Lazy load SendGrid client."""
        if self._client is None:
            try:
                from sendgrid import SendGridAPIClient
                from sendgrid.helpers.mail import (
                    Mail,
                    MailHelper,
                    Email,
                    To,
                    Content,
                )
                self._client = SendGridAPIClient(self.api_key)
                self._helper = MailHelper
            except ImportError:
                raise RuntimeError(
                    "sendgrid package not installed. Install with: pip install sendgrid"
                )
        return self._client

    def send_email(
        self,
        to: str | List[str],
        subject: str,
        html: str,
        text: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send email using SendGrid API."""
        client = self._get_client()

        # Prepare recipients
        recipients = [to] if isinstance(to, str) else to

        # Build email
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{from_name} <{from_email}>" if from_name else from_email
        msg["To"] = ", ".join(recipients)

        if reply_to:
            msg["Reply-To"] = reply_to

        # Attach plain text and HTML
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")
        msg.attach(part1)
        msg.attach(part2)

        try:
            response = client.send(msg)
            logger.info(f"Email sent via SendGrid: {response.status_code}")
            return {
                "provider": "sendgrid",
                "status_code": response.status_code,
                "status": "sent" if response.status_code in (200, 201, 202) else "failed",
            }
        except Exception as e:
            logger.error(f"SendGrid API error: {e}")
            raise

    def is_available(self) -> bool:
        """Check if SendGrid is available."""
        return bool(self.api_key)


class SMTPProvider(EmailProvider):
    """SMTP email provider implementation."""

    def __init__(
        self,
        host: str,
        port: int = 587,
        username: str = None,
        password: str = None,
        use_tls: bool = True,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls

    def send_email(
        self,
        to: str | List[str],
        subject: str,
        html: str,
        text: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send email using SMTP."""
        # Prepare recipients
        recipients = [to] if isinstance(to, str) else to

        # Build email
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{from_name} <{from_email}>" if from_name else from_email
        msg["To"] = ", ".join(recipients)

        if reply_to:
            msg["Reply-To"] = reply_to

        # Attach plain text and HTML
        part1 = MIMEText(text, "plain", "utf-8")
        part2 = MIMEText(html, "html", "utf-8")
        msg.attach(part1)
        msg.attach(part2)

        try:
            # Connect and send
            if self.use_tls:
                server = smtplib.SMTP(self.host, self.port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.host, self.port)

            if self.username and self.password:
                server.login(self.username, self.password)

            server.sendmail(from_email, recipients, msg.as_string())
            server.quit()

            logger.info(f"Email sent via SMTP to {recipients}")
            return {
                "provider": "smtp",
                "status": "sent",
            }
        except Exception as e:
            logger.error(f"SMTP error: {e}")
            raise

    def is_available(self) -> bool:
        """Check if SMTP is configured."""
        return bool(self.host and self.port)


def create_email_provider() -> EmailProvider:
    """
    Create email provider based on environment configuration.

    Returns:
        Configured email provider instance

    Raises:
        RuntimeError: If no valid provider is configured
    """
    provider_type = os.getenv("EMAIL_PROVIDER", "resend").lower()

    if provider_type == "resend":
        api_key = os.getenv("RESEND_API_KEY")
        if not api_key:
            raise RuntimeError("RESEND_API_KEY environment variable not set")
        return ResendProvider(api_key)

    elif provider_type == "sendgrid":
        api_key = os.getenv("SENDGRID_API_KEY")
        if not api_key:
            raise RuntimeError("SENDGRID_API_KEY environment variable not set")
        return SendGridProvider(api_key)

    elif provider_type == "smtp":
        host = os.getenv("SMTP_HOST")
        if not host:
            raise RuntimeError("SMTP_HOST environment variable not set")

        return SMTPProvider(
            host=host,
            port=int(os.getenv("SMTP_PORT", "587")),
            username=os.getenv("SMTP_USER"),
            password=os.getenv("SMTP_PASSWORD"),
            use_tls=os.getenv("SMTP_USE_TLS", "true").lower() == "true",
        )

    else:
        raise RuntimeError(f"Unknown email provider: {provider_type}")
