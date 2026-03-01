#!/bin/bash
set -e

echo "========================================="
echo "TranslateFlow Docker Initialization"
echo "========================================="

# Initialize default configuration files
init_config() {
    echo "[Init] Checking configuration files..."

    # Create default profile if not exists
    if [ ! -f "/app/Resource/profiles/default.json" ]; then
        echo "[Init] Creating default profile from preset..."
        mkdir -p /app/Resource/profiles
        cp /app/Resource/platforms/preset.json /app/Resource/profiles/default.json
        echo "✓ Default profile created"
    else
        echo "✓ Default profile exists"
    fi

    # Create main config.json if not exists
    if [ ! -f "/app/Resource/config.json" ]; then
        echo "[Init] Creating main config.json..."
        cat > /app/Resource/config.json << 'EOF'
{
    "wizard_completed": true,
    "active_profile": "default",
    "active_rules_profile": "default"
}
EOF
        echo "✓ Main config.json created"
    else
        echo "✓ Main config.json exists"
    fi
}

# Function to wait for database
wait_for_db() {
    echo "[Init] Checking database connection..."
    max_attempts=30
    attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if python -c "from ModuleFolders.Service.Auth import init_database; init_database()" 2>/dev/null; then
            echo "[Init] Database connection successful"
            return 0
        fi

        attempt=$((attempt + 1))
        echo "[Init] Waiting for database... (attempt $attempt/$max_attempts)"
        sleep 2
    done

    echo "[Init] ERROR: Database connection failed after $max_attempts attempts"
    return 1
}

# Initialize database tables
init_db() {
    echo "[Init] Creating database tables..."

    python << 'EOF'
from ModuleFolders.Service.Auth import init_database

try:
    # Initialize auth tables
    init_database()
    print("✓ Database tables created successfully")
except Exception as e:
    print(f"Error creating tables: {e}")
    raise
EOF
}

# Create default admin user
create_admin() {
    echo "[Init] Creating default admin user..."

    python << 'EOF'
import traceback
from uuid import uuid4
from ModuleFolders.Service.Auth.models import User, UserRole, UserStatus
from ModuleFolders.Service.Auth.password_manager import PasswordManager

try:
    # Check if admin exists
    print("[DB] Querying for existing admin user...")
    admin_user = User.get_or_none(User.username == "admin")
    print(f"[DB] Query result: {admin_user}")

    if admin_user is None:
        # Create admin
        print("[DB] Creating new admin user...")
        password_manager = PasswordManager()
        print("[DB] Password manager initialized")

        password_hash = password_manager.hash_password("admin")
        print(f"[DB] Password hash generated: {password_hash[:20]}...")

        admin_user = User.create(
            id=str(uuid4()),
            email="admin@translateflow.local",
            username="admin",
            password_hash=password_hash,
            role=UserRole.SUPER_ADMIN.value,
            status=UserStatus.ACTIVE.value,
            email_verified=True,
            preferences={},  # Explicitly set all JSONField defaults
            failed_login_attempts=0,
            tenant_id=None,
            full_name=None,
            bio=None,
        )
        print("[DB] User.create() called successfully")
        print(f"[DB] Created user ID: {admin_user.id}")
        print("✓ Default admin user created (username: admin, password: admin)")
    else:
        print(f"[DB] Admin user already exists: {admin_user.username}")
        print("✓ Admin user already exists")
except Exception as e:
    print(f"[ERROR] Could not create admin user: {e}")
    print(f"[ERROR] Exception type: {type(e).__name__}")
    print(f"[ERROR] Traceback:")
    traceback.print_exc()
EOF
}

# Display configuration
show_config() {
    echo ""
    echo "========================================="
    echo "Configuration"
    echo "========================================="
    echo "Database: SQLite (${SQLITE_PATH:-/app/data/translateflow.db})"
    echo "Web Server: http://0.0.0.0:${PORT:-8000}"
    echo "Default Login: admin / admin"
    echo "========================================="
    echo ""
}

# Main initialization
main() {
    echo "[Init] Starting initialization..."

    # Initialize default configuration files
    init_config

    # Wait for database
    wait_for_db

    # Initialize database tables
    init_db

    # Create default admin user
    create_admin

    # Show configuration
    show_config

    echo "[Init] Initialization complete!"
    echo ""
}

# Run initialization
main

# Execute the main command (web server)
echo "[Init] Starting FastAPI web server..."
exec uv run python -m uvicorn Tools.WebServer.web_server:app --host 0.0.0.0 --port "${PORT:-8000}"
