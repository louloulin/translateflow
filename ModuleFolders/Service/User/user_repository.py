# ModuleFolders/Service/User/user_repository.py
"""
User repository for data access operations.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID


class UserRepository:
    """Repository for user data access operations."""

    def __init__(self):
        from ModuleFolders.Service.Auth.models import User
        self.User = User

    def find_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Find user by ID.

        Args:
            user_id: User's UUID

        Returns:
            User data or None
        """
        try:
            user = self.User.get_by_id(user_id)
            return self._to_dict(user)
        except self.User.DoesNotExist:
            return None

    def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Find user by email.

        Args:
            email: User's email

        Returns:
            User data or None
        """
        user = self.User.get_or_none(self.User.email == email)
        if user:
            return self._to_dict(user)
        return None

    def find_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Find user by username.

        Args:
            username: Username

        Returns:
            User data or None
        """
        user = self.User.get_or_none(self.User.username == username)
        if user:
            return self._to_dict(user)
        return None

    def find_many(
        self,
        offset: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        role: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find multiple users with filtering.

        Args:
            offset: Query offset
            limit: Query limit
            search: Search query
            role: Filter by role
            status: Filter by status

        Returns:
            List of user data
        """
        query = self.User.select()

        # Apply filters
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                (self.User.username ** search_pattern) |
                (self.User.email ** search_pattern) |
                (self.User.full_name ** search_pattern)
            )

        if role:
            query = query.where(self.User.role == role)

        if status:
            query = query.where(self.User.status == status)

        users = query.offset(offset).limit(limit).order_by(self.User.created_at.desc())

        return [self._to_dict(user) for user in users]

    def count(
        self,
        search: Optional[str] = None,
        role: Optional[str] = None,
        status: Optional[str] = None,
    ) -> int:
        """
        Count users with filtering.

        Args:
            search: Search query
            role: Filter by role
            status: Filter by status

        Returns:
            User count
        """
        query = self.User.select()

        # Apply filters
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                (self.User.username ** search_pattern) |
                (self.User.email ** search_pattern) |
                (self.User.full_name ** search_pattern)
            )

        if role:
            query = query.where(self.User.role == role)

        if status:
            query = query.where(self.User.status == status)

        return query.count()

    def create(
        self,
        email: str,
        username: str,
        password_hash: str,
        role: str = "user",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a new user.

        Args:
            email: User's email
            username: Username
            password_hash: Hashed password
            role: User role
            **kwargs: Additional user fields

        Returns:
            Created user data
        """
        import uuid
        from ModuleFolders.Service.Auth.models import UserStatus

        user = self.User.create(
            id=uuid.uuid4(),
            email=email,
            username=username,
            password_hash=password_hash,
            role=role,
            status=UserStatus.ACTIVE.value,
            **kwargs
        )

        return self._to_dict(user)

    def update(
        self,
        user_id: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Update user fields.

        Args:
            user_id: User's UUID
            **kwargs: Fields to update

        Returns:
            Updated user data or None
        """
        try:
            user = self.User.get_by_id(user_id)

            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)

            user.save()
            return self._to_dict(user)
        except self.User.DoesNotExist:
            return None

    def delete(self, user_id: str) -> bool:
        """
        Delete user by ID.

        Args:
            user_id: User's UUID

        Returns:
            True if deleted, False otherwise
        """
        try:
            user = self.User.get_by_id(user_id)
            user.delete_instance(recursive=True)
            return True
        except self.User.DoesNotExist:
            return False

    def _to_dict(self, user) -> Dict[str, Any]:
        """
        Convert user model to dictionary.

        Args:
            user: User model instance

        Returns:
            User data dictionary
        """
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
            "preferences": user.preferences or {},
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        }
