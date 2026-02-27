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
from .auth_middleware import (
    JWTAuthMiddleware,
    get_jwt_middleware,
    jwt_middleware,
    get_current_user,
    get_current_user_optional,
    oauth2_scheme,
)

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
    "JWTAuthMiddleware",
    "get_jwt_middleware",
    "jwt_middleware",
    "get_current_user",
    "get_current_user_optional",
    "oauth2_scheme",
]
