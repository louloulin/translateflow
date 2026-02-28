# ModuleFolders/Service/User/user_manager.py
"""
User manager for profile management operations.
"""

import re
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse


class UserError(Exception):
    """User management error exception."""
    pass


class UserManager:
    """Manages user profile operations."""

    def __init__(self):
        from .user_repository import UserRepository
        from ModuleFolders.Service.Auth.password_manager import PasswordManager
        from ModuleFolders.Service.Email.email_service import get_email_service

        self.user_repo = UserRepository()
        self.password_manager = PasswordManager()
        self.email_service = get_email_service()

    def validate_username(self, username: str) -> tuple[bool, str]:
        """
        Validate username format.
        Returns (is_valid, error_message).
        """
        if not username:
            return False, "Username is required"

        if len(username) < 3:
            return False, "Username must be at least 3 characters"

        if len(username) > 20:
            return False, "Username must be less than 20 characters"

        pattern = r'^[a-zA-Z0-9_]+$'
        if not re.match(pattern, username):
            return False, "Username can only contain letters, numbers, and underscores"

        return True, ""

    def validate_full_name(self, full_name: str) -> tuple[bool, str]:
        """
        Validate full name.
        Returns (is_valid, error_message).
        """
        if not full_name:
            return True, ""  # Optional field

        if len(full_name) > 255:
            return False, "Full name must be less than 255 characters"

        # Allow letters, spaces, hyphens, and common name characters
        pattern = r'^[\p{L}\s\-\'\.]+$'
        if not re.match(pattern, full_name, re.UNICODE):
            return False, "Full name contains invalid characters"

        return True, ""

    def validate_bio(self, bio: str) -> tuple[bool, str]:
        """
        Validate user bio.
        Returns (is_valid, error_message).
        """
        if not bio:
            return True, ""  # Optional field

        if len(bio) > 500:
            return False, "Bio must be less than 500 characters"

        return True, ""

    def validate_avatar_url(self, url: str) -> tuple[bool, str]:
        """
        Validate avatar URL.
        Returns (is_valid, error_message).
        """
        if not url:
            return True, ""  # Optional field

        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                return False, "Invalid URL format"

            if result.scheme not in ['http', 'https']:
                return False, "URL must use HTTP or HTTPS scheme"

            return True, ""
        except Exception:
            return False, "Invalid URL format"

    def get_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Get user profile by ID.

        Args:
            user_id: User's UUID

        Returns:
            User profile data

        Raises:
            UserError: If user not found
        """
        from ModuleFolders.Service.Auth.models import User

        user = User.get_or_none(User.id == user_id)

        if not user:
            raise UserError("User not found")

        return {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "bio": user.bio,
            "avatar_url": user.avatar_url,
            "role": user.role,
            "status": user.status,
            "email_verified": user.email_verified,
            "tenant_id": str(user.tenant_id) if user.tenant_id else None,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        }

    def update_profile(
        self,
        user_id: str,
        username: Optional[str] = None,
        full_name: Optional[str] = None,
        bio: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update user profile.

        Args:
            user_id: User's UUID
            username: New username (optional)
            full_name: New full name (optional)
            bio: New bio (optional)
            avatar_url: New avatar URL (optional)

        Returns:
            Updated user profile

        Raises:
            UserError: If validation fails or user not found
        """
        from ModuleFolders.Service.Auth.models import User

        user = User.get_or_none(User.id == user_id)

        if not user:
            raise UserError("User not found")

        # Validate and update username if provided
        if username is not None and username != user.username:
            is_valid, error_msg = self.validate_username(username)
            if not is_valid:
                raise UserError(error_msg)

            # Check if username is already taken
            existing = User.get_or_none(User.username == username)
            if existing and existing.id != user.id:
                raise UserError("Username is already taken")

            user.username = username

        # Validate and update full name if provided
        if full_name is not None:
            is_valid, error_msg = self.validate_full_name(full_name)
            if not is_valid:
                raise UserError(error_msg)

            user.full_name = full_name if full_name else None

        # Validate and update bio if provided
        if bio is not None:
            is_valid, error_msg = self.validate_bio(bio)
            if not is_valid:
                raise UserError(error_msg)

            user.bio = bio if bio else None

        # Validate and update avatar URL if provided
        if avatar_url is not None:
            is_valid, error_msg = self.validate_avatar_url(avatar_url)
            if not is_valid:
                raise UserError(error_msg)

            user.avatar_url = avatar_url if avatar_url else None

        user.save()

        return self.get_profile(user_id)

    def update_email(
        self,
        user_id: str,
        new_email: str,
        password: str,
    ) -> Dict[str, Any]:
        """
        Update user email address.

        Args:
            user_id: User's UUID
            new_email: New email address
            password: Current password for verification

        Returns:
            Updated user profile

        Raises:
            UserError: If validation fails or password incorrect
        """
        from ModuleFolders.Service.Auth.models import User
        from ModuleFolders.Service.Auth.auth_manager import AuthManager

        # Validate email format
        auth_manager = AuthManager()
        if not auth_manager.validate_email(new_email):
            raise UserError("Invalid email format")

        user = User.get_or_none(User.id == user_id)

        if not user:
            raise UserError("User not found")

        # Verify password
        if not user.password_hash:
            raise UserError("Cannot change email for OAuth accounts")

        if not self.password_manager.verify_password(password, user.password_hash):
            raise UserError("Current password is incorrect")

        # Check if email is already taken
        existing = User.get_or_none(User.email == new_email)
        if existing:
            raise UserError("Email is already registered")

        # Update email
        user.email = new_email
        user.email_verified = False  # Require re-verification
        user.save()

        # Send verification email
        try:
            auth_manager.send_verification_email(user)
        except Exception:
            # Log error but don't fail the update
            import logging
            logging.getLogger(__name__).warning("Failed to send verification email after email change")

        # Send notification to old email
        try:
            self.email_service.send_email_change_notification(
                to=new_email,
                username=user.username,
            )
        except Exception:
            import logging
            logging.getLogger(__name__).warning("Failed to send email change notification")

        return self.get_profile(user_id)

    def update_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str,
    ) -> Dict[str, Any]:
        """
        Update user password.

        Args:
            user_id: User's UUID
            current_password: Current password
            new_password: New password

        Returns:
            Success message

        Raises:
            UserError: If validation fails or password incorrect
        """
        from ModuleFolders.Service.Auth.models import User
        from ModuleFolders.Service.Auth.auth_manager import AuthManager

        user = User.get_or_none(User.id == user_id)

        if not user:
            raise UserError("User not found")

        # Check if user has password (OAuth users may not)
        if not user.password_hash:
            raise UserError("Cannot set password for OAuth accounts")

        # Verify current password
        if not self.password_manager.verify_password(current_password, user.password_hash):
            raise UserError("Current password is incorrect")

        # Validate new password
        auth_manager = AuthManager()
        is_valid, error_msg = auth_manager.validate_password(new_password)
        if not is_valid:
            raise UserError(error_msg)

        # Update password
        user.password_hash = self.password_manager.hash_password(new_password)
        user.save()

        # Revoke all refresh tokens for security
        from ModuleFolders.Service.Auth.models import RefreshToken
        RefreshToken.update(is_revoked=True).where(
            RefreshToken.user == user,
            RefreshToken.is_revoked == False,
        ).execute()

        # Send password change notification
        try:
            self.email_service.send_password_change_notification(
                to=user.email,
                username=user.username,
            )
        except Exception:
            import logging
            logging.getLogger(__name__).warning("Failed to send password change notification")

        return {
            "message": "Password updated successfully",
        }

    def delete_account(
        self,
        user_id: str,
        password: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Delete user account.

        Args:
            user_id: User's UUID
            password: Current password (required for non-OAuth accounts)

        Returns:
            Success message

        Raises:
            UserError: If validation fails
        """
        from ModuleFolders.Service.Auth.models import User

        user = User.get_or_none(User.id == user_id)

        if not user:
            raise UserError("User not found")

        # Verify password if user has one
        if user.password_hash:
            if not password:
                raise UserError("Password is required to delete account")

            if not self.password_manager.verify_password(password, user.password_hash):
                raise UserError("Current password is incorrect")

        # Send account deletion notification
        try:
            self.email_service.send_account_deletion_notification(
                to=user.email,
                username=user.username,
            )
        except Exception:
            import logging
            logging.getLogger(__name__).warning("Failed to send account deletion notification")

        # Delete user (cascade delete will handle related records)
        user.delete_instance(recursive=True)

        return {
            "message": "Account deleted successfully",
        }

    def list_users(
        self,
        page: int = 1,
        per_page: int = 20,
        search: Optional[str] = None,
        role: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List users with filtering and pagination (admin only).

        Args:
            page: Page number (1-indexed)
            per_page: Items per page
            search: Search query (username, email, full_name)
            role: Filter by role
            status: Filter by status

        Returns:
            Paginated user list

        Raises:
            UserError: If validation fails
        """
        from ModuleFolders.Service.Auth.models import User

        # Validate pagination parameters
        if page < 1:
            raise UserError("Page must be >= 1")

        if per_page < 1 or per_page > 100:
            raise UserError("Per page must be between 1 and 100")

        # Build query
        query = User.select()

        # Apply filters
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                (User.username ** search_pattern) |
                (User.email ** search_pattern) |
                (User.full_name ** search_pattern)
            )

        if role:
            query = query.where(User.role == role)

        if status:
            query = query.where(User.status == status)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * per_page
        users = query.offset(offset).limit(per_page).order_by(User.created_at.desc())

        return {
            "users": [
                {
                    "id": str(user.id),
                    "email": user.email,
                    "username": user.username,
                    "full_name": user.full_name,
                    "role": user.role,
                    "status": user.status,
                    "email_verified": user.email_verified,
                    "created_at": user.created_at.isoformat(),
                    "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
                }
                for user in users
            ],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page,
            },
        }

    def update_user_role(
        self,
        admin_id: str,
        user_id: str,
        new_role: str,
    ) -> Dict[str, Any]:
        """
        Update user role (admin only).

        Args:
            admin_id: Admin user's UUID
            user_id: User's UUID to update
            new_role: New role to assign

        Returns:
            Updated user profile

        Raises:
            UserError: If validation fails or not authorized
        """
        from ModuleFolders.Service.Auth.models import User, UserRole

        # Verify admin has permission
        admin = User.get_by_id(admin_id)
        if admin.role not in [UserRole.SUPER_ADMIN.value, UserRole.TENANT_ADMIN.value]:
            raise UserError("Not authorized to update user roles")

        # Validate role
        valid_roles = [r.value for r in UserRole]
        if new_role not in valid_roles:
            raise UserError(f"Invalid role. Must be one of: {', '.join(valid_roles)}")

        # Get user to update
        user = User.get_or_none(User.id == user_id)
        if not user:
            raise UserError("User not found")

        # Prevent changing own role
        if user_id == admin_id:
            raise UserError("Cannot change your own role")

        # Update role
        user.role = new_role
        user.save()

        # Send role change notification
        try:
            self.email_service.send_role_change_notification(
                to=user.email,
                username=user.username,
                new_role=new_role,
            )
        except Exception:
            import logging
            logging.getLogger(__name__).warning("Failed to send role change notification")

        return self.get_profile(user_id)

    def update_user_status(
        self,
        admin_id: str,
        user_id: str,
        new_status: str,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update user status (admin only).

        Args:
            admin_id: Admin user's UUID
            user_id: User's UUID to update
            new_status: New status to assign
            reason: Reason for status change

        Returns:
            Updated user profile

        Raises:
            UserError: If validation fails or not authorized
        """
        from ModuleFolders.Service.Auth.models import User, UserRole, UserStatus

        # Verify admin has permission
        admin = User.get_by_id(admin_id)
        if admin.role not in [UserRole.SUPER_ADMIN.value, UserRole.TENANT_ADMIN.value]:
            raise UserError("Not authorized to update user status")

        # Validate status
        valid_statuses = [s.value for s in UserStatus]
        if new_status not in valid_statuses:
            raise UserError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

        # Get user to update
        user = User.get_or_none(User.id == user_id)
        if not user:
            raise UserError("User not found")

        # Prevent changing own status
        if user_id == admin_id:
            raise UserError("Cannot change your own status")

        # Update status
        user.status = new_status
        user.save()

        # Send status change notification
        try:
            if new_status == UserStatus.SUSPENDED.value:
                self.email_service.send_account_suspended_notification(
                    to=user.email,
                    username=user.username,
                    reason=reason or "Account suspended by administrator",
                )
            elif new_status == UserStatus.ACTIVE.value:
                self.email_service.send_account_reactivated_notification(
                    to=user.email,
                    username=user.username,
                )
        except Exception:
            import logging
            logging.getLogger(__name__).warning("Failed to send status change notification")

        return self.get_profile(user_id)

    def get_login_history(
        self,
        user_id: str,
        page: int = 1,
        per_page: int = 20,
    ) -> Dict[str, Any]:
        """
        Get user's login history.

        Args:
            user_id: User's UUID
            page: Page number (1-indexed)
            per_page: Items per page

        Returns:
            Paginated login history

        Raises:
            UserError: If user not found
        """
        from ModuleFolders.Service.Auth.models import LoginHistory, User

        # Verify user exists
        user = User.get_or_none(User.id == user_id)
        if not user:
            raise UserError("User not found")

        # Validate pagination parameters
        if page < 1:
            raise UserError("Page must be >= 1")

        if per_page < 1 or per_page > 100:
            raise UserError("Per page must be between 1 and 100")

        # Build query
        query = LoginHistory.select().where(LoginHistory.user == user)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * per_page
        history = query.offset(offset).limit(per_page).order_by(LoginHistory.created_at.desc())

        return {
            "history": [
                {
                    "id": str(entry.id),
                    "ip_address": entry.ip_address,
                    "user_agent": entry.user_agent,
                    "success": entry.success,
                    "failure_reason": entry.failure_reason,
                    "created_at": entry.created_at.isoformat(),
                }
                for entry in history
            ],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page,
            },
        }

    def update_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Update user preferences.

        Args:
            user_id: User's UUID
            preferences: Preferences to update (merged with existing)

        Returns:
            Updated preferences

        Raises:
            UserError: If user not found
        """
        from ModuleFolders.Service.Auth.models import User

        user = User.get_or_none(User.id == user_id)

        if not user:
            raise UserError("User not found")

        # Merge with existing preferences
        current_prefs = user.preferences or {}
        current_prefs.update(preferences)

        user.preferences = current_prefs
        user.save()

        return {
            "preferences": user.preferences,
        }

    def get_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Get user preferences.

        Args:
            user_id: User's UUID

        Returns:
            User preferences

        Raises:
            UserError: If user not found
        """
        from ModuleFolders.Service.Auth.models import User

        user = User.get_or_none(User.id == user_id)

        if not user:
            raise UserError("User not found")

        return {
            "preferences": user.preferences or {},
        }


# Global user manager instance
_user_manager: Optional[UserManager] = None


def get_user_manager() -> UserManager:
    """Get the global user manager instance."""
    global _user_manager
    if _user_manager is None:
        _user_manager = UserManager()
    return _user_manager
