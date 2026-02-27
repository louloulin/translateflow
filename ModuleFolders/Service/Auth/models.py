# ModuleFolders/Service/Auth/models.py
"""
User management database models using Peewee ORM.
"""

import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from peewee import (
    UUIDField,
    CharField,
    BooleanField,
    DateTimeField,
    TextField,
    IntegerField,
    ForeignKeyField,
    Field,
    SQL,
    PostgresqlDatabase,
    SqliteDatabase,
)

from playhouse.pool import PooledPostgresqlDatabase


class JSONField(TextField):
    """JSON field implementation for older peewee versions."""

    def db_value(self, value):
        if value is None:
            return None
        return json.dumps(value)

    def python_value(self, value):
        if value is None:
            return None
        if isinstance(value, dict):
            return value
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

# Try to import database backend
try:
    from pgsql import database as db_instance
    _db = db_instance
except ImportError:
    # Fallback to SQLite if PostgreSQL not available
    _db = SqliteDatabase('ainiee_users.db')


class UserRole(str, Enum):
    """User role enumeration."""
    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    TEAM_ADMIN = "team_admin"
    TRANSLATION_ADMIN = "translation_admin"
    DEVELOPER = "developer"
    USER = "user"


class UserStatus(str, Enum):
    """User status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class SubscriptionPlan(str, Enum):
    """Subscription plan enumeration."""
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class TenantStatus(str, Enum):
    """Tenant status enumeration."""
    ACTIVE = "active"
    SUSPENDED = "suspended"


class BaseModel:
    """Base model with common fields."""

    id = UUIDField(primary_key=True, default=uuid.uuid4)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)


class User(_db.Model, BaseModel):
    """User model for authentication and profile management."""

    email = CharField(max_length=255, unique=True, index=True)
    username = CharField(max_length=100, unique=True, index=True)
    password_hash = CharField(max_length=255, null=True)  # Nullable for OAuth users
    avatar_url = CharField(max_length=500, null=True)

    # Role and permissions
    role = CharField(
        max_length=50,
        default=UserRole.USER.value,
        choices=[(r.value, r.name) for r in UserRole]
    )

    # Multi-tenant support
    tenant_id = UUIDField(null=True, index=True)

    # Account status
    status = CharField(
        max_length=20,
        default=UserStatus.ACTIVE.value,
        choices=[(s.value, s.name) for s in UserStatus]
    )

    # Email verification
    email_verified = BooleanField(default=False)
    verification_token = CharField(max_length=255, null=True)

    # Password reset
    reset_token = CharField(max_length=255, null=True)
    reset_token_expires = DateTimeField(null=True)

    # Login tracking
    last_login_at = DateTimeField(null=True)
    failed_login_attempts = IntegerField(default=0)
    locked_until = DateTimeField(null=True)

    # Profile fields
    full_name = CharField(max_length=255, null=True)
    bio = TextField(null=True)
    preferences = JSONField(default=dict)

    class Meta:
        table_name = "users"

    def __str__(self):
        return f"<User {self.username}>"

    @property
    def is_active(self):
        return self.status == UserStatus.ACTIVE.value

    @property
    def is_admin(self):
        return self.role in [
            UserRole.SUPER_ADMIN.value,
            UserRole.TENANT_ADMIN.value
        ]


class Tenant(_db.Model, BaseModel):
    """Tenant model for multi-tenant support."""

    name = CharField(max_length=255)
    slug = CharField(max_length=100, unique=True, index=True)

    # Subscription
    plan = CharField(
        max_length=20,
        default=SubscriptionPlan.FREE.value,
        choices=[(p.value, p.name) for p in SubscriptionPlan]
    )

    # Status
    status = CharField(
        max_length=20,
        default=TenantStatus.ACTIVE.value,
        choices=[(s.value, s.name) for s in TenantStatus]
    )

    # Subscription details from payment provider
    stripe_customer_id = CharField(max_length=255, null=True)
    stripe_subscription_id = CharField(max_length=255, null=True)
    subscription_expires_at = DateTimeField(null=True)

    # Settings
    settings = JSONField(default=dict)

    # Contact
    owner_id = UUIDField(null=True)
    contact_email = CharField(max_length=255, null=True)

    class Meta:
        table_name = "tenants"

    def __str__(self):
        return f"<Tenant {self.name}>"


class ApiKey(_db.Model, BaseModel):
    """API Key model for developer access."""

    user = ForeignKeyField(User, backref="api_keys", on_delete="CASCADE")
    key_hash = CharField(max_length=255, unique=True, index=True)
    key_prefix = CharField(max_length=20)  # First 20 chars for display

    name = CharField(max_length=100)
    description = TextField(null=True)

    # Permissions
    permissions = JSONField(default=dict)

    # Rate limiting
    rate_limit = IntegerField(default=60)  # Requests per minute

    # Usage tracking
    last_used_at = DateTimeField(null=True)
    usage_count = IntegerField(default=0)

    # Expiration
    expires_at = DateTimeField(null=True)

    # Status
    is_active = BooleanField(default=True)

    class Meta:
        table_name = "api_keys"

    def __str__(self):
        return f"<ApiKey {self.name}>"


class LoginHistory(_db.Model):
    """Login history for security audit."""

    id = UUIDField(primary_key=True, default=uuid.uuid4)
    user = ForeignKeyField(User, backref="login_history", on_delete="CASCADE")

    # Connection details
    ip_address = CharField(max_length=45)  # IPv6 compatible
    user_agent = CharField(max_length=500, null=True)
    device_info = JSONField(null=True)

    # Result
    success = BooleanField()
    failure_reason = CharField(max_length=255, null=True)

    # Timestamp
    created_at = DateTimeField(default=datetime.utcnow, index=True)

    class Meta:
        table_name = "login_history"
        indexes = (
            (("user_id", "created_at"), False),
            (("ip_address", "created_at"), False),
        )

    def __str__(self):
        status = "success" if self.success else "failed"
        return f"<LoginHistory {self.user.username} - {status}>"


class PasswordReset(_db.Model):
    """Password reset token storage."""

    id = UUIDField(primary_key=True, default=uuid.uuid4)
    user = ForeignKeyField(User, backref="password_resets", on_delete="CASCADE")

    token = CharField(max_length=255, unique=True, index=True)
    token_hash = CharField(max_length=255)

    # Status
    used = BooleanField(default=False)
    expires_at = DateTimeField()

    created_at = DateTimeField(default=datetime.utcnow)

    class Meta:
        table_name = "password_resets"

    def __str__(self):
        return f"<PasswordReset {self.user.username}>"


class EmailVerification(_db.Model):
    """Email verification token storage."""

    id = UUIDField(primary_key=True, default=uuid.uuid4)
    user = ForeignKeyField(User, backref="email_verifications", on_delete="CASCADE")

    token = CharField(max_length=255, unique=True, index=True)
    token_hash = CharField(max_length=255)

    # Status
    verified = BooleanField(default=False)
    verified_at = DateTimeField(null=True)

    expires_at = DateTimeField()

    created_at = DateTimeField(default=datetime.utcnow)

    class Meta:
        table_name = "email_verifications"

    def __str__(self):
        return f"<EmailVerification {self.user.username}>"


class RefreshToken(_db.Model):
    """Refresh token for JWT authentication."""

    id = UUIDField(primary_key=True, default=uuid.uuid4)
    user = ForeignKeyField(User, backref="refresh_tokens", on_delete="CASCADE")

    token = CharField(max_length=255, unique=True, index=True)
    token_hash = CharField(max_length=255)

    # Metadata
    ip_address = CharField(max_length=45, null=True)
    user_agent = CharField(max_length=500, null=True)

    # Status
    is_revoked = BooleanField(default=False)

    # Expiration
    expires_at = DateTimeField()

    created_at = DateTimeField(default=datetime.utcnow)

    class Meta:
        table_name = "refresh_tokens"
        indexes = (
            (("user_id", "is_revoked"), False),
        )

    def __str__(self):
        return f"<RefreshToken {self.user.username}>"


# Database initialization function
def init_database():
    """Initialize database tables."""
    _db.connect()
    _db.create_tables([
        User,
        Tenant,
        ApiKey,
        LoginHistory,
        PasswordReset,
        EmailVerification,
        RefreshToken,
    ], safe=True)
    return _db


def close_database():
    """Close database connection."""
    if not _db.is_closed():
        _db.close()
