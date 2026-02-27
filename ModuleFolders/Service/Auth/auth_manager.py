# ModuleFolders/Service/Auth/auth_manager.py
"""
Authentication manager for user registration and login.
"""

import re
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from uuid import uuid4

from .models import (
    User,
    LoginHistory,
    RefreshToken,
    PasswordReset,
    EmailVerification,
    UserRole,
    UserStatus,
)
from .password_manager import PasswordManager
from .jwt_handler import JWTHandler


class AuthError(Exception):
    """Authentication error exception."""
    pass


class AuthManager:
    """Manages user authentication operations."""

    def __init__(self):
        self.password_manager = PasswordManager()
        self.jwt_handler = JWTHandler()

    def validate_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def validate_username(self, username: str) -> bool:
        """Validate username format (3-20 chars, alphanumeric + underscore)."""
        pattern = r'^[a-zA-Z0-9_]{3,20}$'
        return bool(re.match(pattern, username))

    def validate_password(self, password: str) -> Tuple[bool, str]:
        """
        Validate password strength.
        Returns (is_valid, error_message).
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        if len(password) > 100:
            return False, "Password must be less than 100 characters"
        if not re.search(r'[A-Za-z]', password):
            return False, "Password must contain at least one letter"
        if not re.search(r'[0-9]', password):
            return False, "Password must contain at least one number"
        return True, ""

    def register(
        self,
        email: str,
        username: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        send_verification: bool = True,
    ) -> Tuple[Dict[str, Any], str]:
        """
        Register a new user.
        Returns (user_data, access_token).
        """
        # Validate email
        if not self.validate_email(email):
            raise AuthError("Invalid email format")

        # Validate username
        if not self.validate_username(username):
            raise AuthError(
                "Username must be 3-20 characters and contain only letters, numbers, and underscores"
            )

        # Validate password
        is_valid, error_msg = self.validate_password(password)
        if not is_valid:
            raise AuthError(error_msg)

        # Check if email already exists
        if User.get_or_none(User.email == email):
            raise AuthError("Email already registered")

        # Check if username already exists
        if User.get_or_none(User.username == username):
            raise AuthError("Username already taken")

        # Create user
        user = User.create(
            id=uuid4(),
            email=email,
            username=username,
            password_hash=self.password_manager.hash_password(password),
            role=UserRole.USER.value,
            status=UserStatus.ACTIVE.value,
            email_verified=False,
        )

        # Generate tokens
        access_token = self.jwt_handler.create_access_token(
            str(user.id),
            user.email,
            user.role
        )
        refresh_token = self.jwt_handler.create_refresh_token(str(user.id))

        # Store refresh token
        RefreshToken.create(
            id=uuid4(),
            user=user,
            token=refresh_token,
            token_hash=self.jwt_handler.get_token_hash(refresh_token),
            expires_at=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Record login history
        LoginHistory.create(
            id=uuid4(),
            user=user,
            ip_address=ip_address or "unknown",
            user_agent=user_agent,
            success=True,
        )

        # Update last login
        user.last_login_at = datetime.utcnow()
        user.save()

        # Send verification email if requested
        if send_verification:
            try:
                self.send_verification_email(user)
            except Exception:
                # Log error but don't fail registration
                import logging
                logging.getLogger(__name__).warning("Failed to send verification email during registration")

        return {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "role": user.role,
                "status": user.status,
                "email_verified": user.email_verified,
            },
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    def login(
        self,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Authenticate a user.
        Returns user data and tokens.
        """
        # Find user by email
        user = User.get_or_none(User.email == email)

        if not user:
            raise AuthError("Invalid email or password")

        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise AuthError("Account is temporarily locked. Please try again later.")

        # Check password
        if not user.password_hash:
            raise AuthError("Please use OAuth login for this account")

        if not self.password_manager.verify_password(password, user.password_hash):
            # Record failed login
            LoginHistory.create(
                id=uuid4(),
                user=user,
                ip_address=ip_address or "unknown",
                user_agent=user_agent,
                success=False,
                failure_reason="Invalid password",
            )

            # Increment failed attempts
            user.failed_login_attempts += 1

            # Lock account after 5 failed attempts
            if user.failed_login_attempts >= 5:
                from datetime import timedelta
                user.locked_until = datetime.utcnow() + timedelta(minutes=15)
                user.save()
                raise AuthError("Too many failed attempts. Account locked for 15 minutes.")

            user.save()
            raise AuthError("Invalid email or password")

        # Check if account is active
        if user.status != UserStatus.ACTIVE.value:
            raise AuthError("Account is not active")

        # Reset failed attempts
        user.failed_login_attempts = 0
        user.locked_until = None

        # Generate tokens
        access_token = self.jwt_handler.create_access_token(
            str(user.id),
            user.email,
            user.role
        )
        refresh_token = self.jwt_handler.create_refresh_token(str(user.id))

        # Store refresh token
        RefreshToken.create(
            id=uuid4(),
            user=user,
            token=refresh_token,
            token_hash=self.jwt_handler.get_token_hash(refresh_token),
            expires_at=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Record successful login
        LoginHistory.create(
            id=uuid4(),
            user=user,
            ip_address=ip_address or "unknown",
            user_agent=user_agent,
            success=True,
        )

        # Update last login
        user.last_login_at = datetime.utcnow()
        user.save()

        return {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "role": user.role,
                "status": user.status,
            },
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token."""
        # Verify refresh token
        payload = self.jwt_handler.verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise AuthError("Invalid refresh token")

        # Check if token exists and not revoked
        token_hash = self.jwt_handler.get_token_hash(refresh_token)
        stored_token = RefreshToken.get_or_none(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked == False
        )

        if not stored_token:
            raise AuthError("Refresh token has been revoked")

        # Get user
        user = User.get_by_id(payload.get("sub"))
        if not user or user.status != UserStatus.ACTIVE.value:
            raise AuthError("User not found or inactive")

        # Generate new access token
        access_token = self.jwt_handler.create_access_token(
            str(user.id),
            user.email,
            user.role
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
        }

    def logout(self, refresh_token: str) -> bool:
        """Logout user by revoking refresh token."""
        token_hash = self.jwt_handler.get_token_hash(refresh_token)
        stored_token = RefreshToken.get_or_none(
            RefreshToken.token_hash == token_hash
        )

        if stored_token:
            stored_token.is_revoked = True
            stored_token.save()
            return True

        return False

    def get_current_user(self, token: str) -> Optional[User]:
        """Get current user from access token."""
        payload = self.jwt_handler.verify_token(token)
        if not payload or payload.get("type") != "access":
            return None

        return User.get_or_none(User.id == payload.get("sub"))

    def forgot_password(
        self,
        email: str,
        reset_url_base: str = "https://translateflow.example.com/reset-password",
    ) -> Dict[str, Any]:
        """
        Initiate password reset process.
        Sends a password reset email to the user.
        """
        # Find user by email
        user = User.get_or_none(User.email == email)

        # For security, always return success even if user doesn't exist
        # This prevents email enumeration attacks
        if not user:
            return {
                "message": "If an account exists with this email, a password reset link has been sent."
            }

        # Check if user has a password (OAuth users may not)
        if not user.password_hash:
            return {
                "message": "If an account exists with this email, a password reset link has been sent."
            }

        # Generate reset token
        import secrets
        reset_token = secrets.token_urlsafe(32)
        token_hash = self.jwt_handler.get_token_hash(reset_token)

        from datetime import timedelta
        expires_at = datetime.utcnow() + timedelta(hours=1)

        # Store token in database
        PasswordReset.create(
            id=uuid4(),
            user=user,
            token=reset_token,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        # Also store token on user for quick lookup
        user.reset_token = reset_token
        user.reset_token_expires = expires_at
        user.save()

        # Send password reset email
        try:
            from ModuleFolders.Service.Email.email_service import get_email_service

            email_service = get_email_service()
            reset_url = f"{reset_url_base}?token={reset_token}"
            email_service.send_password_reset_email(
                to=user.email,
                username=user.username,
                reset_url=reset_url,
            )
        except Exception as e:
            # Log error but don't expose to user
            import logging
            logging.getLogger(__name__).error(f"Failed to send password reset email: {e}")

        return {
            "message": "If an account exists with this email, a password reset link has been sent."
        }

    def reset_password(
        self,
        token: str,
        new_password: str,
    ) -> Dict[str, Any]:
        """
        Reset user password using the reset token.
        """
        # Validate new password
        is_valid, error_msg = self.validate_password(new_password)
        if not is_valid:
            raise AuthError(error_msg)

        # Find user by reset token
        user = User.get_or_none(User.reset_token == token)

        if not user:
            raise AuthError("Invalid or expired reset token")

        # Check if token has expired
        if user.reset_token_expires and user.reset_token_expires < datetime.utcnow():
            raise AuthError("Reset token has expired")

        # Verify token hash in PasswordReset table
        token_hash = self.jwt_handler.get_token_hash(token)
        password_reset = PasswordReset.get_or_none(
            PasswordReset.token_hash == token_hash,
            PasswordReset.used == False,
        )

        if not password_reset:
            raise AuthError("Invalid or expired reset token")

        # Update password
        user.password_hash = self.password_manager.hash_password(new_password)
        user.reset_token = None
        user.reset_token_expires = None

        # Reset security-related fields
        user.failed_login_attempts = 0
        user.locked_until = None
        user.save()

        # Mark reset token as used
        password_reset.used = True
        password_reset.save()

        # Revoke all refresh tokens for security
        RefreshToken.update(is_revoked=True).where(
            RefreshToken.user == user,
            RefreshToken.is_revoked == False,
        ).execute()

        return {
            "message": "Password has been reset successfully",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
            },
        }

    def verify_reset_token(self, token: str) -> Optional[User]:
        """Verify if a reset token is valid and return the user."""
        user = User.get_or_none(User.reset_token == token)

        if not user:
            return None

        if user.reset_token_expires and user.reset_token_expires < datetime.utcnow():
            return None

        return user

    def send_verification_email(
        self,
        user: User,
        verification_url_base: str = "https://translateflow.example.com/verify-email",
    ) -> Dict[str, Any]:
        """
        Send email verification email to user.

        Args:
            user: User to send verification email to
            verification_url_base: Base URL for verification

        Returns:
            Dict with send result
        """
        import secrets
        from datetime import timedelta

        # Generate verification token
        verification_token = secrets.token_urlsafe(32)
        token_hash = self.jwt_handler.get_token_hash(verification_token)
        expires_at = datetime.utcnow() + timedelta(hours=24)

        # Store token in database
        EmailVerification.create(
            id=uuid4(),
            user=user,
            token=verification_token,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        # Also store token on user for quick lookup
        user.verification_token = verification_token
        user.save()

        # Send verification email
        try:
            from ModuleFolders.Service.Email.email_service import get_email_service

            email_service = get_email_service()
            verification_url = f"{verification_url_base}?token={verification_token}"
            email_service.send_verification_email(
                to=user.email,
                username=user.username,
                verification_url=verification_url,
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to send verification email: {e}")
            raise AuthError("Failed to send verification email")

        return {
            "message": "Verification email sent successfully",
            "expires_at": expires_at.isoformat(),
        }

    def verify_email(self, token: str) -> Dict[str, Any]:
        """
        Verify user's email using the verification token.

        Args:
            token: Verification token from email

        Returns:
            Dict with verification result
        """
        # Find user by verification token
        user = User.get_or_none(User.verification_token == token)

        if not user:
            raise AuthError("Invalid verification token")

        # Check if already verified
        if user.email_verified:
            return {
                "message": "Email already verified",
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "username": user.username,
                    "email_verified": user.email_verified,
                },
            }

        # Verify token in EmailVerification table
        token_hash = self.jwt_handler.get_token_hash(token)
        email_verification = EmailVerification.get_or_none(
            EmailVerification.token_hash == token_hash,
            EmailVerification.verified == False,
        )

        if not email_verification:
            raise AuthError("Invalid or expired verification token")

        # Check if token has expired
        if email_verification.expires_at < datetime.utcnow():
            raise AuthError("Verification token has expired")

        # Mark email as verified
        user.email_verified = True
        user.verification_token = None
        user.save()

        # Mark verification token as used
        email_verification.verified = True
        email_verification.verified_at = datetime.utcnow()
        email_verification.save()

        # Send welcome email
        try:
            from ModuleFolders.Service.Email.email_service import get_email_service

            email_service = get_email_service()
            email_service.send_welcome_email(
                to=user.email,
                username=user.username,
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to send welcome email: {e}")

        return {
            "message": "Email verified successfully",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "email_verified": user.email_verified,
            },
        }

    def resend_verification_email(
        self,
        email: str,
        verification_url_base: str = "https://translateflow.example.com/verify-email",
    ) -> Dict[str, Any]:
        """
        Resend verification email to user.

        Args:
            email: User's email address
            verification_url_base: Base URL for verification

        Returns:
            Dict with send result
        """
        # Find user by email
        user = User.get_or_none(User.email == email)

        # For security, always return success even if user doesn't exist
        # This prevents email enumeration attacks
        if not user:
            return {
                "message": "If an account exists and is not verified, a verification email has been sent."
            }

        # Check if already verified
        if user.email_verified:
            return {
                "message": "Email is already verified"
            }

        # Check if there's an existing unexpired verification token
        if user.verification_token:
            # Check if token is still valid by looking it up
            token_hash = self.jwt_handler.get_token_hash(user.verification_token)
            existing_verification = EmailVerification.get_or_none(
                EmailVerification.token_hash == token_hash,
                EmailVerification.verified == False,
            )

            if existing_verification and existing_verification.expires_at > datetime.utcnow():
                return {
                    "message": "A verification email has already been sent. Please check your inbox or try again later."
                }

        # Generate new verification token
        return self.send_verification_email(user, verification_url_base)

    def verify_verification_token(self, token: str) -> Optional[User]:
        """
        Verify if a verification token is valid and return the user.

        Args:
            token: Verification token from email

        Returns:
            User if token is valid, None otherwise
        """
        user = User.get_or_none(User.verification_token == token)

        if not user:
            return None

        # Check token in database
        token_hash = self.jwt_handler.get_token_hash(token)
        email_verification = EmailVerification.get_or_none(
            EmailVerification.token_hash == token_hash,
            EmailVerification.verified == False,
        )

        if not email_verification:
            return None

        if email_verification.expires_at < datetime.utcnow():
            return None

        return user


# Global auth manager instance
_auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    """Get the global auth manager instance."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager
