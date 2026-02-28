#!/bin/bash
# TranslateFlow Docker Deployment Script
# Unified deployment orchestration for production and development environments

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
ENV_FILE="${PROJECT_ROOT}/.env"
BACKUP_DIR="${PROJECT_ROOT}/backups"
COMPOSE_FILE="docker-compose.yml"
PRODUCTION_COMPOSE="docker-compose.yml"
DEVELOPMENT_COMPOSE="docker-compose.override.yml"

# Default settings
MODE="production"
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

# Check if required tools are installed
check_dependencies() {
    log_info "Checking dependencies..."

    local missing_deps=()

    if ! command -v docker &> /dev/null; then
        missing_deps+=("docker")
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        missing_deps+=("docker-compose")
    fi

    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing required dependencies: ${missing_deps[*]}"
        log_info "Please install missing dependencies and try again."
        exit 1
    fi

    log_success "All dependencies are installed"
}

# Check if .env file exists
check_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        log_error "Environment file not found: $ENV_FILE"
        log_info "Run './scripts/deploy.sh setup' to create it from template"
        exit 1
    fi

    # Check for default secrets
    if grep -q "changeme" "$ENV_FILE" 2>/dev/null; then
        log_warning "Environment file contains default values. Please update secrets for production!"
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    log_verbose "Environment file validated"
}

# Generate random secret
generate_secret() {
    openssl rand -hex 32
}

# Generate random password
generate_password() {
    openssl rand -base64 24 | tr -d '/+=' | head -c 24
}

# Setup initial environment
setup_environment() {
    log_info "Setting up TranslateFlow environment..."

    # Check if .env already exists
    if [ -f "$ENV_FILE" ]; then
        log_warning ".env file already exists"
        read -p "Overwrite existing configuration? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Setup cancelled"
            return
        fi
        # Backup existing .env
        cp "$ENV_FILE" "${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    fi

    # Copy template
    if [ -f "${PROJECT_ROOT}/.env.example" ]; then
        cp "${PROJECT_ROOT}/.env.example" "$ENV_FILE"
        log_success "Created .env from template"
    else
        log_error ".env.example not found"
        exit 1
    fi

    # Generate secrets
    log_info "Generating secure secrets..."

    SECRET_KEY=$(generate_secret)
    DB_PASSWORD=$(generate_password)

    # Update .env with generated secrets
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/SECRET_KEY=changeme-in-production/SECRET_KEY=${SECRET_KEY}/" "$ENV_FILE"
        sed -i '' "s/DB_PASSWORD=changeme/DB_PASSWORD=${DB_PASSWORD}/" "$ENV_FILE"
    else
        # Linux
        sed -i "s/SECRET_KEY=changeme-in-production/SECRET_KEY=${SECRET_KEY}/" "$ENV_FILE"
        sed -i "s/DB_PASSWORD=changeme/DB_PASSWORD=${DB_PASSWORD}/" "$ENV_FILE"
    fi

    log_success "Generated and configured secrets"
    log_warning "Please review $ENV_FILE and configure additional settings (email, OAuth, Stripe)"

    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    log_success "Created backup directory: $BACKUP_DIR"

    # Pull Docker images
    log_info "Pulling Docker images..."
    cd "$PROJECT_ROOT"
    docker-compose pull --ignore-pull-failures || true
    log_success "Docker images pulled"

    log_success "Setup complete! Run './scripts/deploy.sh start' to launch services"
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."
    cd "$PROJECT_ROOT"

    local build_args=()
    if [ "$VERBOSE" = true ]; then
        build_args+=("--progress=plain")
    fi

    if [ "$MODE" = "production" ]; then
        log_info "Building for production..."
        docker-compose -f "$PRODUCTION_COMPOSE" build "${build_args[@]}" --no-cache
    else
        log_info "Building for development..."
        docker-compose -f "$PRODUCTION_COMPOSE" -f "$DEVELOPMENT_COMPOSE" build "${build_args[@]}"
    fi

    log_success "Docker images built successfully"
}

# Start services
start_services() {
    check_env_file

    log_info "Starting TranslateFlow services..."
    cd "$PROJECT_ROOT"

    local compose_flags=("-d")
    if [ "$VERBOSE" = true ]; then
        compose_flags=()
    fi

    if [ "$MODE" = "production" ]; then
        docker-compose -f "$PRODUCTION_COMPOSE" up "${compose_flags[@]}"
    else
        docker-compose -f "$PRODUCTION_COMPOSE" -f "$DEVELOPMENT_COMPOSE" up "${compose_flags[@]}"
    fi

    if [ "$VERBOSE" = false ]; then
        log_success "Services started in background"
        log_info "Run './scripts/deploy.sh logs' to view logs"
        log_info "Run './scripts/deploy.sh status' to check service status"
    fi

    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    sleep 5

    # Run health check
    if "${SCRIPT_DIR}/health-check.sh" --quick; then
        log_success "All services are healthy and ready!"
    else
        log_warning "Some services may not be fully ready. Check logs for details."
    fi
}

# Stop services
stop_services() {
    log_info "Stopping TranslateFlow services..."
    cd "$PROJECT_ROOT"

    if [ "$MODE" = "production" ]; then
        docker-compose -f "$PRODUCTION_COMPOSE" down
    else
        docker-compose -f "$PRODUCTION_COMPOSE" -f "$DEVELOPMENT_COMPOSE" down
    fi

    log_success "Services stopped successfully"
}

# Restart services
restart_services() {
    log_info "Restarting TranslateFlow services..."
    stop_services
    sleep 2
    start_services
}

# View logs
view_logs() {
    cd "$PROJECT_ROOT"

    local service="${1:-}"
    local follow_flag="-f"

    if [ "$MODE" = "production" ]; then
        if [ -n "$service" ]; then
            docker-compose -f "$PRODUCTION_COMPOSE" logs $follow_flag "$service"
        else
            docker-compose -f "$PRODUCTION_COMPOSE" logs $follow_flag
        fi
    else
        if [ -n "$service" ]; then
            docker-compose -f "$PRODUCTION_COMPOSE" -f "$DEVELOPMENT_COMPOSE" logs $follow_flag "$service"
        else
            docker-compose -f "$PRODUCTION_COMPOSE" -f "$DEVELOPMENT_COMPOSE" logs $follow_flag
        fi
    fi
}

# Check service status
check_status() {
    log_info "Service Status:"
    cd "$PROJECT_ROOT"

    if [ "$MODE" = "production" ]; then
        docker-compose -f "$PRODUCTION_COMPOSE" ps
    else
        docker-compose -f "$PRODUCTION_COMPOSE" -f "$DEVELOPMENT_COMPOSE" ps
    fi

    echo
    log_info "Health Check:"
    "${SCRIPT_DIR}/health-check.sh"
}

# Clean up unused resources
clean_resources() {
    log_warning "This will remove stopped containers and unused images"
    read -p "Continue? (y/N) " -n 1 -r
    echo

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Clean cancelled"
        return
    fi

    log_info "Cleaning up unused resources..."
    cd "$PROJECT_ROOT"

    # Stop and remove containers
    if [ "$MODE" = "production" ]; then
        docker-compose -f "$PRODUCTION_COMPOSE" down --remove-orphans
    else
        docker-compose -f "$PRODUCTION_COMPOSE" -f "$DEVELOPMENT_COMPOSE" down --remove-orphans
    fi

    # Remove unused images
    docker image prune -f

    # Remove unused volumes (be careful!)
    # docker volume prune -f

    log_success "Cleanup complete"
}

# Backup database and volumes
backup_data() {
    check_env_file

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${BACKUP_DIR}/translateflow_backup_${timestamp}.sql"

    mkdir -p "$BACKUP_DIR"

    log_info "Creating backup..."

    # Check if database container is running
    if ! docker ps | grep -q translateflow-postgres; then
        log_error "Database container is not running"
        exit 1
    fi

    # Get database credentials from .env
    source "$ENV_FILE"

    # Create database backup
    docker exec translateflow-postgres pg_dump -U "${DB_USER:-translateflow}" -d "${DB_NAME:-translateflow}" > "$backup_file"

    # Compress backup
    gzip "$backup_file"

    log_success "Backup created: ${backup_file}.gz"

    # Backup volumes (optional)
    log_info "Backing up volume data..."
    local volumes_backup="${BACKUP_DIR}/volumes_${timestamp}.tar.gz"
    docker run --rm \
        -v translateflow_postgres-data:/data \
        -v "${BACKUP_DIR}:/backup" \
        alpine tar czf "/backup/volumes_${timestamp}.tar.gz" /data

    log_success "Volume backup created: $volumes_backup"
    log_info "Backups stored in: $BACKUP_DIR"
}

# Restore from backup
restore_data() {
    check_env_file

    if [ -z "${1:-}" ]; then
        log_error "Please specify backup file to restore"
        log_info "Usage: ./scripts/deploy.sh restore <backup_file.sql.gz>"
        exit 1
    fi

    local backup_file="$1"

    if [ ! -f "$backup_file" ]; then
        log_error "Backup file not found: $backup_file"
        exit 1
    fi

    log_warning "This will replace the current database!"
    read -p "Continue? (y/N) " -n 1 -r
    echo

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Restore cancelled"
        return
    fi

    log_info "Restoring from backup..."

    # Check if database container is running
    if ! docker ps | grep -q translateflow-postgres; then
        log_error "Database container is not running"
        exit 1
    fi

    # Get database credentials from .env
    source "$ENV_FILE"

    # Decompress backup
    local temp_backup="/tmp/restore_$$.sql"
    gunzip -c "$backup_file" > "$temp_backup"

    # Restore database
    docker exec -i translateflow-postgres psql -U "${DB_USER:-translateflow}" -d "${DB_NAME:-translateflow}" < "$temp_backup"

    # Cleanup
    rm "$temp_backup"

    log_success "Database restored successfully"
}

# Update application
update_app() {
    log_info "Updating TranslateFlow..."

    # Check for git
    if [ ! -d "${PROJECT_ROOT}/.git" ]; then
        log_error "Not a git repository. Please update manually."
        exit 1
    fi

    # Backup before update
    log_info "Creating backup before update..."
    backup_data

    # Pull latest code
    log_info "Pulling latest code..."
    cd "$PROJECT_ROOT"
    git pull origin main

    # Rebuild images
    log_info "Rebuilding Docker images..."
    build_images

    # Run migrations
    log_info "Running database migrations..."
    if [ -f "${SCRIPT_DIR}/db-migrate.sh" ]; then
        "${SCRIPT_DIR}/db-migrate.sh" migrate
    fi

    # Restart services
    log_info "Restarting services..."
    restart_services

    log_success "Update complete!"
}

# Show help
show_help() {
    cat << EOF
TranslateFlow Docker Deployment Script

Usage: ./scripts/deploy.sh [OPTIONS] COMMAND [ARGS...]

Options:
    -m, --mode <mode>      Deployment mode: production (default) or development
    -v, --verbose          Enable verbose output
    -h, --help             Show this help message

Commands:
    setup                  Initial setup (create .env, generate secrets, pull images)
    build                  Build Docker images
    start                  Start all services
    stop                   Stop all services
    restart                Restart all services
    logs [service]         View logs (optionally for specific service)
    status                 Check service status and health
    clean                  Remove stopped containers and unused images
    backup                 Backup database and volumes
    restore <file>         Restore database from backup file
    update                 Pull latest code and redeploy (requires git)
    help                   Show this help message

Examples:
    # Initial setup
    ./scripts/deploy.sh setup

    # Start production environment
    ./scripts/deploy.sh start

    # Start development environment
    ./scripts/deploy.sh -m development start

    # View logs for app service
    ./scripts/deploy.sh logs app

    # Backup database
    ./scripts/deploy.sh backup

    # Update to latest version
    ./scripts/deploy.sh update

Environment Variables:
    The script uses .env file for configuration. Run 'setup' to create it.

Deployment Modes:
    - production: Uses docker-compose.yml with production settings
    - development: Uses docker-compose.override.yml with development settings (exposes DB port, etc.)

For more information, see DEPLOYMENT_DOCKER.md
EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -m|--mode)
                MODE="$2"
                shift 2
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

    # Validate mode
    if [ "$MODE" != "production" ] && [ "$MODE" != "development" ]; then
        log_error "Invalid mode: $MODE. Use 'production' or 'development'."
        exit 1
    fi

    log_verbose "Mode: $MODE"
    log_verbose "Command: $COMMAND"

    # Check dependencies (except for help)
    if [ "$COMMAND" != "help" ]; then
        check_dependencies
    fi

    # Execute command
    case $COMMAND in
        setup)
            setup_environment
            ;;
        build)
            check_env_file
            build_images
            ;;
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        logs)
            view_logs "${COMMAND_ARGS[0]:-}"
            ;;
        status)
            check_status
            ;;
        clean)
            clean_resources
            ;;
        backup)
            backup_data
            ;;
        restore)
            restore_data "${COMMAND_ARGS[0]:-}"
            ;;
        update)
            update_app
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
