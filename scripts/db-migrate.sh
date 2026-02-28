#!/bin/bash
# TranslateFlow Database Migration Script
# Manage database migrations and schema changes

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
MIGRATIONS_DIR="${PROJECT_ROOT}/migrations"
BACKUP_DIR="${PROJECT_ROOT}/backups"
MIGRATION_TABLE="schema_migrations"

# Database settings (will be loaded from .env)
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-translateflow}"
DB_USER="${DB_USER:-translateflow}"

# Default settings
DRY_RUN=false
FORCE=false
VERBOSE=false

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_verbose() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${BLUE}[DEBUG]${NC} $1"
    fi
}

# Load environment variables
load_env() {
    if [ -f "${PROJECT_ROOT}/.env" ]; then
        set -a
        source "${PROJECT_ROOT}/.env"
        set +a
        log_verbose "Loaded environment from .env"
    else
        log_warning ".env file not found, using defaults"
    fi

    DB_HOST="${DB_HOST:-localhost}"
    DB_PORT="${DB_PORT:-5432}"
    DB_NAME="${DB_NAME:-translateflow}"
    DB_USER="${DB_USER:-translateflow}"
}

# Get PostgreSQL connection string
get_db_connection() {
    local db_pass="${DB_PASSWORD:-}"

    if [ -n "$db_pass" ]; then
        echo "postgresql://${DB_USER}:${db_pass}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
    else
        echo "postgresql://${DB_USER}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
    fi
}

# Execute SQL in database
execute_sql() {
    local sql="$1"
    local container="translateflow-postgres"

    if docker ps | grep -q "$container"; then
        docker exec -i "$container" psql -U "$DB_USER" -d "$DB_NAME" -c "$sql"
    else
        log_error "Database container is not running"
        exit 1
    fi
}

# Initialize migration tracking table
init_migrations() {
    log_info "Initializing migration tracking..."

    local create_table_sql="
        CREATE TABLE IF NOT EXISTS ${MIGRATION_TABLE} (
            id SERIAL PRIMARY KEY,
            version VARCHAR(14) NOT NULL UNIQUE,
            name VARCHAR(255) NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    "

    execute_sql "$create_table_sql"
    log_success "Migration tracking initialized"
}

# Get current migration version
get_current_version() {
    local version
    version=$(execute_sql "SELECT version FROM ${MIGRATION_TABLE} ORDER BY applied_at DESC LIMIT 1;" 2>/dev/null | head -n 1 | tr -d ' ')

    if [ -z "$version" ] || [ "$version" = "version" ]; then
        echo "00000000000000"
    else
        echo "$version"
    fi
}

# List all migrations
list_migrations() {
    if [ ! -d "$MIGRATIONS_DIR" ]; then
        log_warning "No migrations directory found"
        return
    fi

    local migrations=()
    while IFS= read -r file; do
        migrations+=("$file")
    done < <(find "$MIGRATIONS_DIR" -name "*.sql" | sort)

    if [ ${#migrations[@]} -eq 0 ]; then
        log_warning "No migration files found"
        return
    fi

    echo "=========================================="
    echo "Available Migrations"
    echo "=========================================="
    echo

    local current_version
    current_version=$(get_current_version)

    for migration in "${migrations[@]}"; do
        local basename
        basename=$(basename "$migration")
        local version
        version=$(echo "$basename" | cut -d '_' -f1)
        local name
        name=$(echo "$basename" | cut -d '_' -f2- | sed 's/.sql$//')
        local status

        if [ "$version" \> "$current_version" ]; then
            status="PENDING"
        else
            status="APPLIED"
        fi

        echo -e "${GREEN}${version}${NC} - ${name} [${status}]"
    done

    echo
    echo "=========================================="
    echo "Current version: ${current_version}"
    echo "=========================================="
}

# Get migration status
show_status() {
    log_info "Migration Status:"
    echo

    if [ ! -d "$MIGRATIONS_DIR" ]; then
        log_warning "No migrations directory found"
        log_info "Create it with: mkdir -p $MIGRATIONS_DIR"
        return
    fi

    local current_version
    current_version=$(get_current_version)
    echo "Current Migration Version: ${current_version}"
    echo

    # Count pending migrations
    local pending=0
    while IFS= read -r file; do
        local version
        version=$(basename "$file" | cut -d '_' -f1)
        if [ "$version" \> "$current_version" ]; then
            pending=$((pending + 1))
        fi
    done < <(find "$MIGRATIONS_DIR" -name "*.sql" | sort)

    if [ $pending -eq 0 ]; then
        log_success "Database is up to date"
    else
        log_warning "${pending} pending migration(s)"
    fi
}

# Create a new migration file
create_migration() {
    if [ -z "${1:-}" ]; then
        log_error "Please provide a migration name"
        log_info "Usage: ./scripts/db-migrate.sh create <migration_name>"
        exit 1
    fi

    local migration_name="$1"
    local timestamp
    timestamp=$(date +%Y%m%d%H%M%S)
    local filename="${timestamp}_${migration_name}.sql"
    local filepath="${MIGRATIONS_DIR}/${filename}"

    # Create migrations directory if it doesn't exist
    mkdir -p "$MIGRATIONS_DIR"

    if [ -f "$filepath" ]; then
        log_error "Migration file already exists: $filepath"
        exit 1
    fi

    # Create migration file with template
    cat > "$filepath" << EOF
-- Migration: ${migration_name}
-- Created: $(date '+%Y-%m-%d %H:%M:%S')
-- Description: ${migration_name}

-- BEGIN: Add your migration SQL here

-- Example: Add a new column
-- ALTER TABLE users ADD COLUMN new_field VARCHAR(255);

-- END: Migration SQL

-- Record migration (this is done automatically by the migration script)
-- INSERT INTO ${MIGRATION_TABLE} (version, name) VALUES ('${timestamp}', '${migration_name}');
EOF

    log_success "Created migration: $filepath"
    log_info "Edit this file to add your migration SQL"
}

# Backup database before migration
backup_database() {
    local timestamp
    timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${BACKUP_DIR}/pre_migration_${timestamp}.sql"

    mkdir -p "$BACKUP_DIR"

    log_info "Creating database backup..."

    local container="translateflow-postgres"
    if ! docker ps | grep -q "$container"; then
        log_error "Database container is not running"
        exit 1
    fi

    docker exec "$container" pg_dump -U "$DB_USER" -d "$DB_NAME" > "$backup_file"

    # Compress backup
    gzip "$backup_file"

    log_success "Database backed up to: ${backup_file}.gz"
    echo "$backup_file.gz"
}

# Run pending migrations
run_migrations() {
    log_info "Running database migrations..."

    # Check if migrations directory exists
    if [ ! -d "$MIGRATIONS_DIR" ]; then
        log_warning "No migrations directory found"
        log_info "Creating migrations directory: $MIGRATIONS_DIR"
        mkdir -p "$MIGRATIONS_DIR"
        return
    fi

    # Initialize migration tracking
    init_migrations

    # Get current version
    local current_version
    current_version=$(get_current_version)
    log_verbose "Current migration version: ${current_version}"

    # Find pending migrations
    local migrations=()
    while IFS= read -r file; do
        local version
        version=$(basename "$file" | cut -d '_' -f1)
        if [ "$version" \> "$current_version" ]; then
            migrations+=("$file")
        fi
    done < <(find "$MIGRATIONS_DIR" -name "*.sql" | sort)

    if [ ${#migrations[@]} -eq 0 ]; then
        log_success "No pending migrations"
        return
    fi

    log_info "Found ${#migrations[@]} pending migration(s)"

    # Backup database before migration
    if [ "$DRY_RUN" = false ]; then
        backup_database
    fi

    # Run each migration
    for migration in "${migrations[@]}"; do
        local basename
        basename=$(basename "$migration")
        local version
        version=$(echo "$basename" | cut -d '_' -f1)
        local name
        name=$(echo "$basename" | cut -d '_' -f2- | sed 's/.sql$//')

        log_info "Applying migration: ${basename}"

        if [ "$DRY_RUN" = true ]; then
            log_warning "DRY RUN: Would apply ${basename}"
            continue
        fi

        # Read and execute migration SQL
        local sql
        sql=$(cat "$migration")

        # Remove the record migration line (we handle it separately)
        sql=$(echo "$sql" | grep -v "^INSERT INTO ${MIGRATION_TABLE}")

        # Execute migration
        if execute_sql "$sql"; then
            # Record migration
            execute_sql "INSERT INTO ${MIGRATION_TABLE} (version, name) VALUES ('${version}', '${name}');"
            log_success "Applied: ${basename}"
        else
            log_error "Failed to apply: ${basename}"
            log_error "Migration rolled back"
            exit 1
        fi
    done

    log_success "All migrations applied successfully"
}

# Rollback last migration
rollback_migration() {
    log_warning "Rollback functionality requires manual migration scripts"
    log_info "To rollback, create a new migration that reverses the changes"
    log_info
    log_info "Example:"
    log_info "  ./scripts/db-migrate.sh create revert_add_new_field"
    log_info
    log_info "Then edit the created file to add DROP COLUMN or other revert SQL"

    # Alternative: Show last applied migration
    local current_version
    current_version=$(get_current_version)

    if [ "$current_version" = "00000000000000" ]; then
        log_warning "No migrations have been applied yet"
        return
    fi

    log_info "Last applied migration: ${current_version}"

    # Find the migration file
    local last_migration
    last_migration=$(find "$MIGRATIONS_DIR" -name "${current_version}_*.sql" | head -n 1)

    if [ -n "$last_migration" ]; then
        echo
        log_info "Migration file: $last_migration"
        log_info "Please review this file to create an appropriate rollback migration"
    fi
}

# Seed database with initial data
seed_database() {
    log_info "Seeding database..."

    local seed_file="${MIGRATIONS_DIR}/seed.sql"

    if [ ! -f "$seed_file" ]; then
        log_warning "Seed file not found: $seed_file"
        log_info "Create a seed.sql file in $MIGRATIONS_DIR to seed data"
        return
    fi

    if [ "$DRY_RUN" = true ]; then
        log_warning "DRY RUN: Would seed database"
        return
    fi

    # Execute seed file
    local sql
    sql=$(cat "$seed_file")

    if execute_sql "$sql"; then
        log_success "Database seeded successfully"
    else
        log_error "Failed to seed database"
        exit 1
    fi
}

# Reset database (DANGEROUS!)
reset_database() {
    if [ "$FORCE" = false ]; then
        log_error "This will DELETE ALL DATA in the database!"
        echo
        read -p "Are you absolutely sure? (type 'yes' to confirm): " confirm
        echo

        if [ "$confirm" != "yes" ]; then
            log_info "Reset cancelled"
            return
        fi
    fi

    log_warning "Resetting database..."

    if [ "$DRY_RUN" = true ]; then
        log_warning "DRY RUN: Would reset database"
        return
    fi

    # Backup before reset
    backup_database

    # Drop and recreate database
    local container="translateflow-postgres"
    docker exec -i "$container" psql -U "$DB_USER" postgres <<-EOF
        DROP DATABASE IF EXISTS ${DB_NAME};
        CREATE DATABASE ${DB_NAME};
        GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};
EOF

    log_success "Database reset complete"

    # Run migrations if available
    if [ -d "$MIGRATIONS_DIR" ] && [ -n "$(ls -A $MIGRATIONS_DIR/*.sql 2>/dev/null)" ]; then
        log_info "Running migrations..."
        run_migrations
    fi

    # Seed if available
    if [ -f "${MIGRATIONS_DIR}/seed.sql" ]; then
        log_info "Seeding database..."
        seed_database
    fi

    log_success "Database reset complete"
}

# Show help
show_help() {
    cat << EOF
TranslateFlow Database Migration Script

Usage: ./scripts/db-migrate.sh [OPTIONS] COMMAND [ARGS...]

Options:
    -n, --dry-run           Show what would be done without making changes
    -f, --force             Skip confirmation prompts (use with caution!)
    -v, --verbose           Enable verbose output
    -h, --help              Show this help message

Commands:
    status                  Show migration status and current version
    list                    List all available migrations
    create <name>           Create a new migration file
    migrate                 Run pending migrations
    rollback                Show rollback instructions (manual rollback)
    seed                    Seed database with initial data
    reset                   Reset database (WARNING: deletes all data)
    help                    Show this help message

Examples:
    # Show migration status
    ./scripts/db-migrate.sh status

    # Create a new migration
    ./scripts/db-migrate.sh create add_user_preferences

    # Run pending migrations
    ./scripts/db-migrate.sh migrate

    # Dry-run migrations (test without applying)
    ./scripts/db-migrate.sh --dry-run migrate

    # Seed database with initial data
    ./scripts/db-migrate.sh seed

    # Reset database (development only!)
    ./scripts/db-migrate.sh --force reset

Migration Files:
    Migrations should be placed in the 'migrations/' directory
    with the naming format: YYYYMMDDHHMMSS_description.sql

    Example: migrations/20250228120000_add_user_preferences.sql

Database Backup:
    Automatic backups are created before migrations
    in the 'backups/' directory

Tracking:
    Migrations are tracked in the 'schema_migrations' table
    which stores version, name, and applied timestamp.

For more information, see the database documentation.
EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -n|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -f|--force)
                FORCE=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                break
                ;;
        esac
    done

    COMMAND="${1:-help}"
    shift || true
    COMMAND_ARGS=("$@")
}

# Main execution
main() {
    parse_args "$@"

    # Load environment
    load_env

    # Execute command
    case $COMMAND in
        status)
            init_migrations
            show_status
            ;;
        list)
            init_migrations
            list_migrations
            ;;
        create)
            create_migration "${COMMAND_ARGS[0]:-}"
            ;;
        migrate)
            run_migrations
            ;;
        rollback)
            rollback_migration
            ;;
        seed)
            seed_database
            ;;
        reset)
            reset_database
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $COMMAND"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
