"""
Email service for sending notifications.

Supports multiple email providers:
- Resend (recommended): https://resend.com
- SendGrid: https://sendgrid.com
- SMTP: Generic SMTP server

Environment variables:
    EMAIL_PROVIDER: resend|sendgrid|smtp (default: resend)
    RESEND_API_KEY: Resend API key
    SENDGRID_API_KEY: SendGrid API key
    SMTP_HOST: SMTP server hostname
    SMTP_PORT: SMTP server port (default: 587)
    SMTP_USER: SMTP username
    SMTP_PASSWORD: SMTP password
    SMTP_USE_TLS: Use TLS (default: true)
    EMAIL_FROM: Default from email address
    EMAIL_FROM_NAME: Default from name (default: TranslateFlow)
"""

from .email_service import EmailService, EmailError, get_email_service

__all__ = [
    "EmailService",
    "EmailError",
    "get_email_service",
]
