# ModuleFolders/Service/Auth/__init__.py
"""
Auth service module for user management and authentication.
"""

from .models import (
    User,
    Tenant,
    ApiKey,
    LoginHistory,
    PasswordReset,
    EmailVerification,
    RefreshToken,
    UserRole,
    UserStatus,
    SubscriptionPlan,
    TenantStatus,
    init_database,
    close_database,
)

from .auth_manager import AuthManager, get_auth_manager, AuthError
from .jwt_handler import JWTHandler
from .password_manager import PasswordManager

__all__ = [
    "User",
    "Tenant",
    "ApiKey",
    "LoginHistory",
    "PasswordReset",
    "EmailVerification",
    "RefreshToken",
    "UserRole",
    "UserStatus",
    "SubscriptionPlan",
    "TenantStatus",
    "init_database",
    "close_database",
    "AuthManager",
    "get_auth_manager",
    "AuthError",
    "JWTHandler",
    "PasswordManager",
]
