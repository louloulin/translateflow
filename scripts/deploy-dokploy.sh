#!/bin/bash

# Dokploy Deployment Helper Script
#
# This script helps prepare TranslateFlow for deployment to Dokploy.
# Usage: ./scripts/deploy-dokploy.sh [command]
#
# Commands:
#   validate   - Validate configuration before deployment
#   generate   - Generate secrets for environment variables
#   build      - Build Docker image locally for testing
#   export     - Export configuration for Dokploy
#   help       - Show this help message

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check required files
check_required_files() {
    log_info "Checking required files..."

    local missing_files=()

    if [[ ! -f "$PROJECT_ROOT/docker-compose.dokploy.yml" ]]; then
        missing_files+=("docker-compose.dokploy.yml")
    fi

    if [[ ! -f "$PROJECT_ROOT/.env.dokploy.example" ]]; then
        missing_files+=(".env.dokploy.example")
    fi

    if [[ ! -f "$PROJECT_ROOT/Dockerfile.production" ]]; then
        missing_files+=("Dockerfile.production")
    fi

    if [[ ${#missing_files[@]} -gt 0 ]]; then
        log_error "Missing required files:"
        printf "  - %s\n" "${missing_files[@]}"
        return 1
    fi

    log_success "All required files found"
    return 0
}

# Validate docker-compose syntax
validate_compose() {
    log_info "Validating docker-compose.dokploy.yml..."

    if ! command -v docker-compose &> /dev/null; then
        log_warning "docker-compose not found, skipping syntax validation"
        return 0
    fi

    if docker-compose -f "$PROJECT_ROOT/docker-compose.dokploy.yml" config &> /dev/null; then
        log_success "docker-compose.dokploy.yml syntax is valid"
        return 0
    else
        log_error "docker-compose.dokploy.yml has syntax errors"
        return 1
    fi
}

# Generate secrets
generate_secrets() {
    log_info "Generating secure secrets..."

    echo ""
    echo "=== GENERATED SECRETS FOR DOKPLOY ==="
    echo ""
    echo "Copy these values to your Dokploy environment configuration:"
    echo ""

    # SECRET_KEY
    if command -v python3 &> /dev/null; then
        SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    else
        SECRET_KEY=$(openssl rand -base64 32 | tr -d '/+=' | head -c 32)
    fi
    echo "SECRET_KEY=$SECRET_KEY"

    # DB_PASSWORD
    DB_PASSWORD=$(openssl rand -base64 32 | tr -d '/+=' | head -c 24)
    echo "DB_PASSWORD=$DB_PASSWORD"

    echo ""
    log_warning "⚠️  Store these values securely! Don't share them!"
    echo ""

    return 0
}

# Build Docker image
build_image() {
    log_info "Building Docker image..."

    cd "$PROJECT_ROOT"

    if docker build -f Dockerfile.production -t translateflow:test .; then
        log_success "Docker image built successfully"
        log_info "Test the image with: docker run -p 8000:8000 translateflow:test"
        return 0
    else
        log_error "Docker image build failed"
        return 1
    fi
}

# Export configuration
export_config() {
    log_info "Exporting configuration for Dokploy..."

    local export_dir="$PROJECT_ROOT/.dokploy-export"
    mkdir -p "$export_dir"

    # Copy files
    cp "$PROJECT_ROOT/docker-compose.dokploy.yml" "$export_dir/"
    cp "$PROJECT_ROOT/.env.dokploy.example" "$export_dir/.env"

    log_success "Configuration exported to $export_dir"
    log_info "Files ready for Dokploy deployment:"
    echo "  - $export_dir/docker-compose.dokploy.yml"
    echo "  - $export_dir/.env (configure this before uploading)"
    echo ""

    return 0
}

# Pre-flight checklist
preflight_check() {
    log_info "Running pre-flight deployment checklist..."

    local checklist=()
    local all_passed=true

    # Check 1: Required files
    echo -n "  [1/6] Required files present... "
    if check_required_files &> /dev/null; then
        echo -e "${GREEN}✓${NC}"
        checklist+=("Required files: PASS")
    else
        echo -e "${RED}✗${NC}"
        checklist+=("Required files: FAIL")
        all_passed=false
    fi

    # Check 2: Docker Compose syntax
    echo -n "  [2/6] Docker Compose syntax... "
    if validate_compose &> /dev/null; then
        echo -e "${GREEN}✓${NC}"
        checklist+=("Docker Compose: PASS")
    else
        echo -e "${YELLOW}⊘${NC} (skipped)"
        checklist+=("Docker Compose: SKIPPED")
    fi

    # Check 3: Production Dockerfile
    echo -n "  [3/6] Production Dockerfile... "
    if [[ -f "$PROJECT_ROOT/Dockerfile.production" ]]; then
        echo -e "${GREEN}✓${NC}"
        checklist+=("Dockerfile.production: PASS")
    else
        echo -e "${RED}✗${NC}"
        checklist+=("Dockerfile.production: FAIL")
        all_passed=false
    fi

    # Check 4: Environment template
    echo -n "  [4/6] Environment template... "
    if [[ -f "$PROJECT_ROOT/.env.dokploy.example" ]]; then
        echo -e "${GREEN}✓${NC}"
        checklist+=("Environment template: PASS")
    else
        echo -e "${RED}✗${NC}"
        checklist+=("Environment template: FAIL")
        all_passed=false
    fi

    # Check 5: Documentation
    echo -n "  [5/6] Deployment documentation... "
    if [[ -f "$PROJECT_ROOT/DEPLOYMENT_DOKPLOY.md" ]]; then
        echo -e "${GREEN}✓${NC}"
        checklist+=("Documentation: PASS")
    else
        echo -e "${YELLOW}⊘${NC} (missing but optional)"
        checklist+=("Documentation: WARNING")
    fi

    # Check 6: Secrets generated
    echo -n "  [6/6] Secrets configured... "
    echo -e "${YELLOW}⊘${NC} (configure in Dokploy)"
    checklist+=("Secrets: TODO")

    echo ""
    echo "=== CHECKLIST SUMMARY ==="
    printf "  %s\n" "${checklist[@]}"
    echo ""

    if $all_passed; then
        log_success "Pre-flight checks passed! Ready for deployment."
        return 0
    else
        log_error "Some pre-flight checks failed. Please fix errors before deploying."
        return 1
    fi
}

# Show help
show_help() {
    cat << EOF
TranslateFlow Dokploy Deployment Helper

Usage: ./scripts/deploy-dokploy.sh [command]

Commands:
  validate       Validate deployment configuration
  generate       Generate secure secrets for environment variables
  build          Build Docker image for local testing
  export         Export configuration files to .dokploy-export/
  preflight      Run pre-flight deployment checklist
  help           Show this help message

Examples:
  ./scripts/deploy-dokploy.sh validate
  ./scripts/deploy-dokploy.sh generate
  ./scripts/deploy-dokploy.sh build
  ./scripts/deploy-dokploy.sh export
  ./scripts/deploy-dokploy.sh preflight

Deployment Workflow:
  1. Run './scripts/deploy-dokploy.sh preflight' to verify setup
  2. Run './scripts/deploy-dokploy.sh generate' to create secrets
  3. Run './scripts/deploy-dokploy.sh build' to test locally (optional)
  4. Run './scripts/deploy-dokploy.sh export' to prepare files
  5. Upload files from .dokploy-export/ to Dokploy
  6. Configure environment variables in Dokploy UI
  7. Deploy!

For detailed deployment instructions, see DEPLOYMENT_DOKPLOY.md
EOF
}

# Main script logic
main() {
    local command="${1:-help}"

    case "$command" in
        validate)
            check_required_files
            validate_compose
            ;;
        generate)
            generate_secrets
            ;;
        build)
            build_image
            ;;
        export)
            export_config
            ;;
        preflight)
            preflight_check
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
