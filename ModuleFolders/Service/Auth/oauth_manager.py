# ModuleFolders/Service/Auth/oauth_manager.py
"""
OAuth manager for third-party login (GitHub, Google).
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from uuid import uuid4
import httpx

from .models import User, LoginHistory, RefreshToken, UserRole, UserStatus, OAuthAccount
from .jwt_handler import JWTHandler
from .password_manager import PasswordManager


class OAuthError(Exception):
    """OAuth error exception."""
    pass


class OAuthProvider(str):
    """OAuth provider enumeration."""
    GITHUB = "github"
    GOOGLE = "google"


class OAuthManager:
    """Manages OAuth authentication operations."""

    def __init__(self):
        self.password_manager = PasswordManager()
        self.jwt_handler = JWTHandler()

        # OAuth configuration (load from environment)
        import os
        self.github_client_id = os.getenv("GITHUB_CLIENT_ID")
        self.github_client_secret = os.getenv("GITHUB_CLIENT_SECRET")
        self.google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.oauth_redirect_uri = os.getenv(
            "OAUTH_REDIRECT_URI",
            "http://localhost:8000/api/v1/auth/oauth/callback"
        )

        # API endpoints
        self.github_api_url = "https://api.github.com"
        self.google_token_url = "https://oauth2.googleapis.com/token"
        self.google_userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"

    def get_authorization_url(
        self,
        provider: str,
        state: Optional[str] = None,
        redirect_uri: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Generate OAuth authorization URL.

        Args:
            provider: OAuth provider (github or google)
            state: Optional state parameter for CSRF protection
            redirect_uri: Optional custom redirect URI

        Returns:
            Tuple of (authorization_url, state)
        """
        if state is None:
            state = secrets.token_urlsafe(32)

        redirect = redirect_uri or self.oauth_redirect_uri

        if provider == OAuthProvider.GITHUB:
            auth_url = (
                f"https://github.com/login/oauth/authorize"
                f"?client_id={self.github_client_id}"
                f"&redirect_uri={redirect}"
                f"&scope=user:email"
                f"&state={state}"
            )
        elif provider == OAuthProvider.GOOGLE:
            auth_url = (
                f"https://accounts.google.com/o/oauth2/v2/auth"
                f"?client_id={self.google_client_id}"
                f"&redirect_uri={redirect}"
                f"?response_type=code"
                f"&scope=https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile"
                f"&state={state}"
            )
        else:
            raise OAuthError(f"Unsupported OAuth provider: {provider}")

        return auth_url, state

    async def exchange_code_for_token(
        self,
        provider: str,
        code: str,
        redirect_uri: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.

        Args:
            provider: OAuth provider (github or google)
            code: Authorization code from OAuth callback
            redirect_uri: Optional custom redirect URI

        Returns:
            Dict with access_token and optional refresh_token
        """
        redirect = redirect_uri or self.oauth_redirect_uri

        async with httpx.AsyncClient() as client:
            if provider == OAuthProvider.GITHUB:
                # GitHub OAuth token exchange
                response = await client.post(
                    "https://github.com/login/oauth/access_token",
                    json={
                        "client_id": self.github_client_id,
                        "client_secret": self.github_client_secret,
                        "code": code,
                        "redirect_uri": redirect,
                    },
                    headers={"Accept": "application/json"},
                )
                response.raise_for_status()
                token_data = response.json()

                if "error" in token_data:
                    raise OAuthError(f"GitHub OAuth error: {token_data.get('error_description', 'Unknown error')}")

                return {
                    "access_token": token_data["access_token"],
                    "token_type": token_data.get("token_type", "bearer"),
                    "scope": token_data.get("scope", ""),
                }

            elif provider == OAuthProvider.GOOGLE:
                # Google OAuth token exchange
                response = await client.post(
                    self.google_token_url,
                    data={
                        "code": code,
                        "client_id": self.google_client_id,
                        "client_secret": self.google_client_secret,
                        "redirect_uri": redirect,
                        "grant_type": "authorization_code",
                    },
                )
                response.raise_for_status()
                token_data = response.json()

                if "error" in token_data:
                    raise OAuthError(f"Google OAuth error: {token_data.get('error_description', 'Unknown error')}")

                return {
                    "access_token": token_data["access_token"],
                    "refresh_token": token_data.get("refresh_token"),
                    "expires_in": token_data.get("expires_in"),
                    "token_type": token_data.get("token_type", "Bearer"),
                }

            else:
                raise OAuthError(f"Unsupported OAuth provider: {provider}")

    async def get_user_info(
        self,
        provider: str,
        access_token: str,
    ) -> Dict[str, Any]:
        """
        Get user information from OAuth provider.

        Args:
            provider: OAuth provider (github or google)
            access_token: OAuth access token

        Returns:
            Dict with user information (id, email, name, avatar_url)
        """
        async with httpx.AsyncClient() as client:
            if provider == OAuthProvider.GITHUB:
                # Get user info from GitHub API
                response = await client.get(
                    f"{self.github_api_url}/user",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/json",
                    },
                )
                response.raise_for_status()
                user_data = response.json()

                # Get primary email
                email_response = await client.get(
                    f"{self.github_api_url}/user/emails",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/json",
                    },
                )
                email_response.raise_for_status()
                emails_data = email_response.json()

                # Find primary verified email
                primary_email = None
                for email_info in emails_data:
                    if email_info.get("primary") and email_info.get("verified"):
                        primary_email = email_info["email"]
                        break

                if not primary_email and emails_data:
                    primary_email = emails_data[0]["email"]

                return {
                    "oauth_id": str(user_data["id"]),
                    "email": primary_email,
                    "username": user_data.get("login"),
                    "name": user_data.get("name") or user_data.get("login"),
                    "avatar_url": user_data.get("avatar_url"),
                    "bio": user_data.get("bio"),
                    "location": user_data.get("location"),
                }

            elif provider == OAuthProvider.GOOGLE:
                # Get user info from Google API
                response = await client.get(
                    self.google_userinfo_url,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                    },
                )
                response.raise_for_status()
                user_data = response.json()

                return {
                    "oauth_id": user_data["id"],
                    "email": user_data["email"],
                    "username": user_data["email"].split("@")[0],
                    "name": user_data.get("name"),
                    "avatar_url": user_data.get("picture"),
                    "verified_email": user_data.get("verified_email", False),
                }

            else:
                raise OAuthError(f"Unsupported OAuth provider: {provider}")

    async def oauth_login(
        self,
        provider: str,
        code: str,
        redirect_uri: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Complete OAuth login flow.

        Args:
            provider: OAuth provider (github or google)
            code: Authorization code from OAuth callback
            redirect_uri: Optional custom redirect URI
            ip_address: Client IP address for login history
            user_agent: Client user agent for login history

        Returns:
            Dict with user data and JWT tokens
        """
        # Exchange code for access token
        token_data = await self.exchange_code_for_token(provider, code, redirect_uri)
        access_token = token_data["access_token"]

        # Get user info from provider
        user_info = await self.get_user_info(provider, access_token)
        oauth_id = user_info["oauth_id"]
        email = user_info["email"]

        # Check if OAuth account exists
        oauth_account = OAuthAccount.get_or_none(
            OAuthAccount.provider == provider,
            OAuthAccount.oauth_id == oauth_id,
        )

        if oauth_account:
            # Existing user - login
            user = oauth_account.user

            # Check if account is active
            if user.status != UserStatus.ACTIVE.value:
                raise OAuthError("Account is not active")

            # Update OAuth account info
            oauth_account.access_token = access_token
            oauth_account.refresh_token = token_data.get("refresh_token")
            oauth_account.token_expires_at = (
                datetime.utcnow() + timedelta(seconds=int(token_data["expires_in"]))
                if token_data.get("expires_in")
                else None
            )
            oauth_account.last_login_at = datetime.utcnow()
            oauth_account.save()

            # Update user profile if needed
            if user_info.get("avatar_url") and not user.avatar_url:
                user.avatar_url = user_info["avatar_url"]
            if user_info.get("name") and not user.full_name:
                user.full_name = user_info["name"]
            user.last_login_at = datetime.utcnow()
            user.save()

        else:
            # New OAuth user - create account
            # Check if email already exists
            existing_user = User.get_or_none(User.email == email)

            if existing_user:
                # Link OAuth to existing account
                OAuthAccount.create(
                    id=uuid4(),
                    user=existing_user,
                    provider=provider,
                    oauth_id=oauth_id,
                    access_token=access_token,
                    refresh_token=token_data.get("refresh_token"),
                    token_expires_at=(
                        datetime.utcnow() + timedelta(seconds=int(token_data["expires_in"]))
                        if token_data.get("expires_in")
                        else None
                    ),
                    account_email=email,
                    account_username=user_info.get("username"),
                    account_data=user_info,
                    last_login_at=datetime.utcnow(),
                )
                user = existing_user
            else:
                # Create new user account
                username = user_info.get("username", email.split("@")[0])
                original_username = username
                counter = 1

                # Ensure username is unique
                while User.get_or_none(User.username == username):
                    username = f"{original_username}{counter}"
                    counter += 1

                user = User.create(
                    id=uuid4(),
                    email=email,
                    username=username,
                    password_hash=None,  # OAuth users don't have password
                    full_name=user_info.get("name"),
                    avatar_url=user_info.get("avatar_url"),
                    role=UserRole.USER.value,
                    status=UserStatus.ACTIVE.value,
                    email_verified=True,  # OAuth emails are pre-verified
                    last_login_at=datetime.utcnow(),
                )

                # Create OAuth account link
                OAuthAccount.create(
                    id=uuid4(),
                    user=user,
                    provider=provider,
                    oauth_id=oauth_id,
                    access_token=access_token,
                    refresh_token=token_data.get("refresh_token"),
                    token_expires_at=(
                        datetime.utcnow() + timedelta(seconds=int(token_data["expires_in"]))
                        if token_data.get("expires_in")
                        else None
                    ),
                    account_email=email,
                    account_username=user_info.get("username"),
                    account_data=user_info,
                    last_login_at=datetime.utcnow(),
                )

        # Generate JWT tokens
        jwt_access_token = self.jwt_handler.create_access_token(
            str(user.id),
            user.email,
            user.role
        )
        jwt_refresh_token = self.jwt_handler.create_refresh_token(str(user.id))

        # Store refresh token
        RefreshToken.create(
            id=uuid4(),
            user=user,
            token=jwt_refresh_token,
            token_hash=self.jwt_handler.get_token_hash(jwt_refresh_token),
            expires_at=datetime.utcnow() + timedelta(days=7),
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

        return {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "role": user.role,
                "status": user.status,
                "email_verified": user.email_verified,
                "avatar_url": user.avatar_url,
                "full_name": user.full_name,
            },
            "access_token": jwt_access_token,
            "refresh_token": jwt_refresh_token,
            "token_type": "bearer",
            "provider": provider,
        }

    def link_oauth_account(
        self,
        user_id: str,
        provider: str,
        oauth_id: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        account_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Link OAuth account to existing user.

        Args:
            user_id: User ID to link OAuth account to
            provider: OAuth provider
            oauth_id: OAuth provider user ID
            access_token: OAuth access token
            refresh_token: Optional OAuth refresh token
            account_data: Optional additional account data

        Returns:
            Created OAuthAccount instance
        """
        # Check if user exists
        user = User.get_or_none(User.id == user_id)
        if not user:
            raise OAuthError("User not found")

        # Check if OAuth account already linked
        existing = OAuthAccount.get_or_none(
            OAuthAccount.provider == provider,
            OAuthAccount.oauth_id == oauth_id,
        )
        if existing:
            raise OAuthError("OAuth account already linked to another user")

        # Check if user already has this provider linked
        user_provider = OAuthAccount.get_or_none(
            OAuthAccount.user == user,
            OAuthAccount.provider == provider,
        )
        if user_provider:
            raise OAuthError(f"{provider.capitalize()} account already linked to this user")

        # Create OAuth account link
        oauth_account = OAuthAccount.create(
            id=uuid4(),
            user=user,
            provider=provider,
            oauth_id=oauth_id,
            access_token=access_token,
            refresh_token=refresh_token,
            account_email=account_data.get("email") if account_data else None,
            account_username=account_data.get("username") if account_data else None,
            account_data=account_data or {},
            linked_at=datetime.utcnow(),
        )

        return {
            "message": f"Successfully linked {provider} account",
            "provider": provider,
            "account_email": oauth_account.account_email,
        }

    def unlink_oauth_account(
        self,
        user_id: str,
        provider: str,
    ) -> Dict[str, Any]:
        """
        Unlink OAuth account from user.

        Args:
            user_id: User ID
            provider: OAuth provider to unlink

        Returns:
            Dict with unlink result
        """
        # Find OAuth account
        oauth_account = OAuthAccount.get_or_none(
            OAuthAccount.user == user_id,
            OAuthAccount.provider == provider,
        )

        if not oauth_account:
            raise OAuthError(f"No {provider} account linked to this user")

        # Check if user has password (for OAuth-only accounts)
        user = oauth_account.user
        if not user.password_hash:
            # Count OAuth accounts
            oauth_count = OAuthAccount.select().where(OAuthAccount.user == user).count()
            if oauth_count <= 1:
                raise OAuthError(
                    "Cannot unlink last OAuth account. Please set a password first."
                )

        # Delete OAuth account
        oauth_account.delete_instance()

        return {
            "message": f"Successfully unlinked {provider} account",
            "provider": provider,
        }

    def get_linked_accounts(self, user_id: str) -> list:
        """
        Get all linked OAuth accounts for a user.

        Args:
            user_id: User ID

        Returns:
            List of linked OAuth accounts
        """
        accounts = OAuthAccount.select().where(OAuthAccount.user == user_id)

        return [
            {
                "provider": account.provider,
                "account_email": account.account_email,
                "account_username": account.account_username,
                "linked_at": account.linked_at.isoformat() if account.linked_at else None,
                "last_login_at": account.last_login_at.isoformat() if account.last_login_at else None,
            }
            for account in accounts
        ]


# Global OAuth manager instance
_oauth_manager: Optional[OAuthManager] = None


def get_oauth_manager() -> OAuthManager:
    """Get the global OAuth manager instance."""
    global _oauth_manager
    if _oauth_manager is None:
        _oauth_manager = OAuthManager()
    return _oauth_manager
