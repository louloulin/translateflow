"""
Email service for sending notifications.

Provides a high-level interface for sending various types of emails
with template support and provider abstraction.
"""

import os
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from .providers import EmailProvider, create_email_provider
from .templates import (
    get_verification_email_template,
    get_password_reset_email_template,
    get_welcome_email_template,
    get_subscription_confirmation_template,
    get_quota_warning_template,
    get_login_alert_template,
    get_email_change_notification_template,
    get_password_change_notification_template,
    get_account_deletion_notification_template,
    get_role_change_notification_template,
    get_account_suspended_notification_template,
    get_account_reactivated_notification_template,
    get_payment_notification_template,
    get_subscription_notification_template,
    get_invoice_notification_template,
    EmailTemplate,
)

logger = logging.getLogger(__name__)


class EmailError(Exception):
    """Email service error."""
    pass


@dataclass
class EmailConfig:
    """Email service configuration."""
    provider: str
    from_email: str
    from_name: str
    reply_to: Optional[str] = None


class EmailService:
    """
    Main email service for sending notifications.

    Supports:
    - Email verification
    - Password reset
    - Welcome emails
    - Subscription notifications
    - Quota warnings
    - Login alerts
    """

    def __init__(self, provider: Optional[EmailProvider] = None):
        """
        Initialize email service.

        Args:
            provider: Email provider instance (auto-created if not provided)
        """
        if provider:
            self._provider = provider
        else:
            try:
                self._provider = create_email_provider()
            except RuntimeError as e:
                logger.warning(f"Email provider not configured: {e}")
                self._provider = None

        # Load configuration
        self.config = EmailConfig(
            provider=os.getenv("EMAIL_PROVIDER", "resend"),
            from_email=os.getenv("EMAIL_FROM", "noreply@translateflow.example.com"),
            from_name=os.getenv("EMAIL_FROM_NAME", "TranslateFlow"),
            reply_to=os.getenv("EMAIL_REPLY_TO"),
        )

    def is_available(self) -> bool:
        """Check if email service is available."""
        return self._provider is not None and self._provider.is_available()

    def send_email(
        self,
        to: str | List[str],
        template: EmailTemplate,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send an email using a template.

        Args:
            to: Recipient email address(es)
            template: EmailTemplate instance
            from_email: Override sender email
            from_name: Override sender name
            reply_to: Reply-to address

        Returns:
            Dict with send result

        Raises:
            EmailError: If sending fails
        """
        if not self.is_available():
            raise EmailError("Email service not available. Check configuration.")

        try:
            return self._provider.send_email(
                to=to,
                subject=template.subject,
                html=template.html,
                text=template.text,
                from_email=from_email or self.config.from_email,
                from_name=from_name or self.config.from_name,
                reply_to=reply_to or self.config.reply_to,
            )
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise EmailError(f"Failed to send email: {e}")

    # Convenience methods for common email types

    def send_verification_email(
        self,
        to: str,
        username: str,
        verification_url: str,
    ) -> Dict[str, Any]:
        """Send email verification email."""
        template = get_verification_email_template(username, verification_url)
        return self.send_email(to, template)

    def send_password_reset_email(
        self,
        to: str,
        username: str,
        reset_url: str,
    ) -> Dict[str, Any]:
        """Send password reset email."""
        template = get_password_reset_email_template(username, reset_url)
        return self.send_email(to, template)

    def send_welcome_email(
        self,
        to: str,
        username: str,
    ) -> Dict[str, Any]:
        """Send welcome email after email verification."""
        template = get_welcome_email_template(username)
        return self.send_email(to, template)

    def send_subscription_confirmation(
        self,
        to: str,
        username: str,
        plan_name: str,
        amount: str,
    ) -> Dict[str, Any]:
        """Send subscription confirmation email."""
        template = get_subscription_confirmation_template(username, plan_name, amount)
        return self.send_email(to, template)

    def send_quota_warning(
        self,
        to: str,
        username: str,
        plan_name: str,
        used_percentage: int,
    ) -> Dict[str, Any]:
        """Send quota usage warning email."""
        template = get_quota_warning_template(username, plan_name, used_percentage)
        return self.send_email(to, template)

    def send_login_alert(
        self,
        to: str,
        username: str,
        ip_address: str,
        location: Optional[str] = None,
        time: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send login security alert email."""
        template = get_login_alert_template(username, ip_address, location, time)
        return self.send_email(to, template)

    def send_email_change_notification(
        self,
        to: str,
        username: str,
    ) -> Dict[str, Any]:
        """Send email change notification email."""
        template = get_email_change_notification_template(username)
        return self.send_email(to, template)

    def send_password_change_notification(
        self,
        to: str,
        username: str,
    ) -> Dict[str, Any]:
        """Send password change notification email."""
        template = get_password_change_notification_template(username)
        return self.send_email(to, template)

    def send_account_deletion_notification(
        self,
        to: str,
        username: str,
    ) -> Dict[str, Any]:
        """Send account deletion notification email."""
        template = get_account_deletion_notification_template(username)
        return self.send_email(to, template)

    def send_role_change_notification(
        self,
        to: str,
        username: str,
        new_role: str,
    ) -> Dict[str, Any]:
        """Send role change notification email."""
        template = get_role_change_notification_template(username, new_role)
        return self.send_email(to, template)

    def send_account_suspended_notification(
        self,
        to: str,
        username: str,
        reason: str,
    ) -> Dict[str, Any]:
        """Send account suspended notification email."""
        template = get_account_suspended_notification_template(username, reason)
        return self.send_email(to, template)

    def send_account_reactivated_notification(
        self,
        to: str,
        username: str,
    ) -> Dict[str, Any]:
        """Send account reactivated notification email."""
        template = get_account_reactivated_notification_template(username)
        return self.send_email(to, template)

    def send_payment_notification(
        self,
        email: str,
        payment_id: str,
        status: str,
        amount: float = None,
        currency: str = None,
        error_message: str = None,
    ) -> Dict[str, Any]:
        """发送支付通知邮件"""
        # 查找用户名
        username = email.split("@")[0]  # 简化处理，实际应从数据库查询
        template = get_payment_notification_template(
            username=username,
            payment_id=payment_id,
            amount=amount or 0,
            currency=currency or "CNY",
            status=status,
            error_message=error_message,
        )
        return self.send_email(email, template)

    def send_subscription_notification(
        self,
        email: str,
        event: str,
        plan: str,
        status: str = None,
    ) -> Dict[str, Any]:
        """发送订阅通知邮件"""
        username = email.split("@")[0]  # 简化处理
        template = get_subscription_notification_template(
            username=username,
            event=event,
            plan=plan,
            status=status,
        )
        return self.send_email(email, template)

    def send_invoice_notification(
        self,
        email: str,
        invoice_id: str,
        status: str,
        amount: float = None,
        currency: str = None,
        attempt_count: int = None,
    ) -> Dict[str, Any]:
        """发送发票通知邮件"""
        username = email.split("@")[0]  # 简化处理
        template = get_invoice_notification_template(
            username=username,
            invoice_id=invoice_id,
            status=status,
            amount=amount,
            currency=currency,
            attempt_count=attempt_count,
        )
        return self.send_email(email, template)


# Global instance for convenience
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """
    Get global email service instance.

    Returns:
        EmailService instance

    Raises:
        EmailError: If service cannot be initialized
    """
    global _email_service

    if _email_service is None:
        try:
            _email_service = EmailService()
        except Exception as e:
            logger.error(f"Failed to initialize email service: {e}")
            raise EmailError(f"Failed to initialize email service: {e}")

    return _email_service


def init_email_service(provider: EmailProvider) -> EmailService:
    """
    Initialize global email service with custom provider.

    Args:
        provider: Custom email provider

    Returns:
        Initialized EmailService instance
    """
    global _email_service
    _email_service = EmailService(provider)
    return _email_service
