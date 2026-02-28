# ModuleFolders/Service/Auth/password_manager.py
"""
Password management for user authentication.
"""

import secrets
import string
import hashlib
import bcrypt
from datetime import datetime, timedelta
from typing import Optional


class PasswordManager:
    """Password hashing and verification manager."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify a password against a hash."""
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        except Exception:
            return False

    @staticmethod
    def generate_reset_token() -> str:
        """Generate a secure password reset token."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_verification_token() -> str:
        """Generate an email verification token."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def get_token_hash(token: str) -> str:
        """Get SHA256 hash of a token for storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def generate_reset_token_expiry(hours: int = 24) -> datetime:
        """Generate token expiry datetime."""
        return datetime.utcnow() + timedelta(hours=hours)

    @staticmethod
    def is_token_expired(expiry: datetime) -> bool:
        """Check if a token has expired."""
        return datetime.utcnow() > expiry
