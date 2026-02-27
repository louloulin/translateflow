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
        user_agent: Optional[str] = None
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


# Global auth manager instance
_auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    """Get the global auth manager instance."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager
