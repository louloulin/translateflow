# ModuleFolders/Service/Auth/auth_middleware.py
"""
JWT Authentication Middleware for FastAPI.

Provides middleware and dependencies for protecting routes with JWT authentication.
"""

from typing import Optional, List
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.oauth2 import OAuth2

from .jwt_handler import JWTHandler
from .auth_manager import get_auth_manager, AuthManager
from .models import User, UserStatus

# OAuth2 scheme instance
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class JWTAuthMiddleware:
    """
    JWT Authentication Middleware for FastAPI.

    Provides token verification and user authentication for protected routes.
    """

    def __init__(self, jwt_handler: Optional[JWTHandler] = None):
        self.jwt_handler = jwt_handler or JWTHandler()

    async def verify_token(self, token: str) -> Optional[dict]:
        """
        Verify JWT token and return payload.

        Returns None if token is invalid or expired.
        """
        return self.jwt_handler.verify_token(token)

    async def get_current_user(
        self,
        token: str = Depends(oauth2_scheme),
        auth_manager: AuthManager = Depends(get_auth_manager)
    ) -> User:
        """
        FastAPI dependency to get current authenticated user.

        Usage:
            @app.get("/protected")
            async def protected_route(user: User = Depends(jwt_middleware.get_current_user)):
                return {"user_id": user.id}

        Raises:
            HTTPException: 401 if token is invalid or expired
        """
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        payload = await self.verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = auth_manager.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if user.status != UserStatus.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not active",
            )

        return user

    async def get_current_user_optional(
        self,
        token: Optional[str] = Depends(oauth2_scheme),
        auth_manager: AuthManager = Depends(get_auth_manager)
    ) -> Optional[User]:
        """
        FastAPI dependency to get current user if authenticated, None otherwise.

        Usage:
            @app.get("/optional-auth")
            async def optional_auth_route(user: Optional[User] = Depends(jwt_middleware.get_current_user_optional)):
                if user:
                    return {"user_id": user.id}
                return {"message": "Anonymous user"}
        """
        if not token:
            return None

        try:
            payload = await self.verify_token(token)
            if not payload or payload.get("type") != "access":
                return None

            return auth_manager.get_current_user(token)
        except Exception:
            return None

    def require_role(self, allowed_roles: List[str]):
        """
        Factory function to create a role-based dependency.

        Usage:
            @app.get("/admin")
            async def admin_route(user: User = Depends(jwt_middleware.require_role(["admin", "superuser"]))):
                return {"admin": user.username}

        Args:
            allowed_roles: List of role names that are allowed to access the route

        Returns:
            A FastAPI dependency function
        """
        async def role_checker(user: User = Depends(self.get_current_user)) -> User:
            if user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            return user

        return role_checker

    def require_admin(self):
        """Shortcut for requiring admin role."""
        return self.require_role(["admin", "superuser"])


# Global middleware instance
_jwt_middleware: Optional[JWTAuthMiddleware] = None


def get_jwt_middleware() -> JWTAuthMiddleware:
    """Get the global JWT middleware instance."""
    global _jwt_middleware
    if _jwt_middleware is None:
        _jwt_middleware = JWTAuthMiddleware()
    return _jwt_middleware


# Convenience aliases for common usage
jwt_middleware = get_jwt_middleware()
get_current_user = jwt_middleware.get_current_user
get_current_user_optional = jwt_middleware.get_current_user_optional
