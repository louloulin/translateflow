# ModuleFolders/Service/Auth/jwt_handler.py
"""
JWT token handler for authentication.
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

# JWT Configuration
JWT_SECRET_KEY = secrets.token_hex(32)
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # 15 minutes
REFRESH_TOKEN_EXPIRE_DAYS = 7  # 7 days


class JWTHandler:
    """JWT token handler for access and refresh tokens."""

    @staticmethod
    def create_access_token(user_id: str, email: str, role: str) -> str:
        """Create a new access token."""
        now = datetime.utcnow()
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        payload = {
            "sub": user_id,
            "email": email,
            "role": role,
            "type": "access",
            "iat": now,
            "exp": expire,
        }

        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """Create a new refresh token."""
        now = datetime.utcnow()
        expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        payload = {
            "sub": user_id,
            "type": "refresh",
            "iat": now,
            "exp": expire,
        }

        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(
                token,
                JWT_SECRET_KEY,
                algorithms=[JWT_ALGORITHM]
            )
            return payload
        except ExpiredSignatureError:
            return None
        except InvalidTokenError:
            return None

    @staticmethod
    def decode_token(token: str) -> Optional[Dict[str, Any]]:
        """Decode token without verification (for debugging)."""
        try:
            return jwt.decode(
                token,
                JWT_SECRET_KEY,
                algorithms=[JWT_ALGORITHM],
                options={"verify_signature": False}
            )
        except InvalidTokenError:
            return None

    @staticmethod
    def get_token_hash(token: str) -> str:
        """Get SHA256 hash of a token for storage."""
        return hashlib.sha256(token.encode()).hexdigest()
