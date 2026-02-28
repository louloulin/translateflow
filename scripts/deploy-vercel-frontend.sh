#!/bin/bash

# ========================================
# TranslateFlow Vercel Frontend Deployment Script
# ========================================
# This script automates the deployment of the TranslateFlow frontend to Vercel
#
# Usage:
#   ./deploy-vercel-frontend.sh [command]
#
# Commands:
#   validate   - Check required files and configuration
#   deploy     - Deploy to Vercel
#   env        - Set up environment variables
#   preview    - Create preview deployment
#   production - Deploy to production
#   logs       - View deployment logs
#   domains    - Configure custom domains
#   help       - Show usage information
#
# Requirements:
#   - Vercel CLI installed (npm install -g vercel)
#   - Vercel account (vercel login)
#   - Node.js 18+ and npm
#   - Backend API URL (Railway, Render, etc.)
# ========================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WEBSERVER_DIR="$PROJECT_ROOT/Tools/WebServer"

# ========================================
# Utility Functions
# ========================================

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# ========================================
# Validation Functions
# ========================================

check_vercel_cli() {
    if ! command -v vercel &> /dev/null; then
        print_error "Vercel CLI not installed"
        echo ""
        echo "Install Vercel CLI:"
        echo "  npm install -g vercel"
        echo ""
        echo "Then login:"
        echo "  vercel login"
        return 1
    fi

    print_success "Vercel CLI installed: $(vercel --version)"
    return 0
}

check_node_version() {
    if ! command -v node &> /dev/null; then
        print_error "Node.js not installed"
        return 1
    fi

    local node_version=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$node_version" -lt 18 ]; then
        print_error "Node.js version 18+ required, found $(node -v)"
        return 1
    fi

    print_success "Node.js version: $(node -v)"
    return 0
}

check_required_files() {
    local missing_files=()

    cd "$WEBSERVER_DIR"

    [ ! -f "package.json" ] && missing_files+=("package.json")
    [ ! -f "vercel.json" ] && missing_files+=("vercel.json")
    [ ! -f "vite.config.ts" ] && missing_files+=("vite.config.ts")
    [ ! -f "index.html" ] && missing_files+=("index.html")

    if [ ${#missing_files[@]} -gt 0 ]; then
        print_error "Missing required files:"
        printf '  - %s\n' "${missing_files[@]}"
        return 1
    fi

    print_success "All required files present"
    return 0
}

check_dependencies() {
    cd "$WEBSERVER_DIR"

    if [ ! -d "node_modules" ]; then
        print_warning "Dependencies not installed"
        echo ""
        echo "Installing dependencies..."
        npm install

        if [ $? -eq 0 ]; then
            print_success "Dependencies installed"
        else
            print_error "Failed to install dependencies"
            return 1
        fi
    else
        print_success "Dependencies already installed"
    fi

    return 0
}

check_environment_variables() {
    cd "$PROJECT_ROOT"

    local missing_vars=()

    if [ -f ".env.local" ]; then
        source .env.local

        [ -z "$VITE_API_URL" ] && missing_vars+=("VITE_API_URL")
    else
        print_warning "No .env.local file found"
        missing_vars+=("VITE_API_URL")
    fi

    if [ ${#missing_vars[@]} -gt 0 ]; then
        print_error "Missing environment variables:"
        printf '  - %s\n' "${missing_vars[@]}"
        echo ""
        echo "Create .env.local with:"
        echo "  VITE_API_URL=https://your-backend-url.com"
        return 1
    fi

    print_success "Environment variables configured"
    return 0
}

# ========================================
# Deployment Functions
# ========================================

cmd_validate() {
    print_header "Validating Vercel Frontend Deployment"

    local all_good=true

    check_vercel_cli || all_good=false
    check_node_version || all_good=false
    check_required_files || all_good=false
    check_dependencies || all_good=false

    echo ""

    if [ "$all_good" = true ]; then
        print_success "All validation checks passed!"
        echo ""
        echo "Next steps:"
        echo "  1. Set environment variables: ./deploy-vercel-frontend.sh env"
        echo "  2. Deploy to preview: ./deploy-vercel-frontend.sh preview"
        echo "  3. Deploy to production: ./deploy-vercel-frontend.sh production"
        return 0
    else
        print_error "Validation failed. Please fix the errors above."
        return 1
    fi
}

cmd_env() {
    print_header "Configure Environment Variables"

    check_vercel_cli || return 1

    echo ""
    print_info "Backend API URL (e.g., https://translateflow.up.railway.app)"
    read -p "Backend API URL: " backend_url

    if [ -z "$backend_url" ]; then
        print_error "Backend API URL is required"
        return 1
    fi

    # Create .env.local
    cd "$WEBSERVER_DIR"
    cat > .env.local << ENV_EOF
# TranslateFlow Frontend Environment Variables
# Auto-generated by deploy-vercel-frontend.sh

# Backend API URL
VITE_API_URL=$backend_url

# Application Name
VITE_APP_NAME=TranslateFlow
ENV_EOF

    print_success "Created .env.local"

    # Ask to set in Vercel dashboard
    echo ""
    print_warning "IMPORTANT: Also set these in Vercel Dashboard:"
    echo ""
    echo "  1. Go to https://vercel.com/dashboard"
    echo "  2. Select your project"
    echo "  3. Go to Settings → Environment Variables"
    echo "  4. Add:"
    echo "     - VITE_API_URL = $backend_url"
    echo "     - VITE_APP_NAME = TranslateFlow"
    echo ""
    echo "  5. Select all environments (Production, Preview, Development)"
    echo ""

    return 0
}

cmd_preview() {
    print_header "Deploy to Preview Environment"

    cmd_validate || return 1

    cd "$WEBSERVER_DIR"

    echo ""
    print_info "Deploying to Vercel preview..."
    echo ""

    vercel

    if [ $? -eq 0 ]; then
        echo ""
        print_success "Preview deployment successful!"
        echo ""
        echo "Test your preview deployment before deploying to production."
        return 0
    else
        print_error "Preview deployment failed"
        return 1
    fi
}

cmd_production() {
    print_header "Deploy to Production"

    cmd_validate || return 1

    cd "$WEBSERVER_DIR"

    echo ""
    print_warning "This will deploy to PRODUCTION"
    echo ""
    read -p "Continue? (y/N): " confirm

    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        print_info "Deployment cancelled"
        return 0
    fi

    echo ""
    print_info "Deploying to Vercel production..."
    echo ""

    vercel --prod

    if [ $? -eq 0 ]; then
        echo ""
        print_success "Production deployment successful!"
        echo ""
        print_info "Don't forget to:"
        echo "  1. Set up custom domain (./deploy-vercel-frontend.sh domains)"
        echo "  2. Configure analytics"
        echo "  3. Set up monitoring"
        return 0
    else
        print_error "Production deployment failed"
        return 1
    fi
}

cmd_logs() {
    print_header "View Deployment Logs"

    check_vercel_cli || return 1

    cd "$WEBSERVER_DIR"

    echo ""
    print_info "Opening logs in browser..."
    echo ""

    vercel logs

    return 0
}

cmd_domains() {
    print_header "Configure Custom Domains"

    check_vercel_cli || return 1

    echo ""
    print_info "To add a custom domain:"
    echo ""
    echo "  1. Go to https://vercel.com/dashboard"
    echo "  2. Select your project"
    echo "  3. Go to Settings → Domains"
    echo "  4. Click 'Add Domain'"
    echo "  5. Enter your domain (e.g., app.translateflow.com)"
    echo ""
    echo "Vercel will provide DNS instructions:"
    echo "  - CNAME app → cname.vercel-dns.com"
    echo ""
    echo "6. Update DNS at your domain registrar"
    echo "7. Vercel will automatically provision SSL certificate"
    echo ""

    read -p "Open Vercel dashboard in browser? (Y/n): " open_dashboard

    if [ "$open_dashboard" != "n" ] && [ "$open_dashboard" != "N" ]; then
        open "https://vercel.com/dashboard" 2>/dev/null || \
        xdg-open "https://vercel.com/dashboard" 2>/dev/null || \
        print_info "Manual open required: https://vercel.com/dashboard"
    fi

    return 0
}

cmd_help() {
    cat << HELP_EOF
${BLUE}TranslateFlow Vercel Frontend Deployment Script${NC}

${YELLOW}Usage:${NC}
  ./deploy-vercel-frontend.sh [command]

${YELLOW}Commands:${NC}
  validate    Check required files and configuration
  deploy      Deploy to Vercel preview environment
  env         Set up environment variables
  preview     Create preview deployment (alias for 'deploy')
  production  Deploy to production environment
  logs        View deployment logs
  domains     Configure custom domains
  help        Show this help message

${YELLOW}Examples:${NC}
  ./deploy-vercel-frontend.sh validate
  ./deploy-vercel-frontend.sh env
  ./deploy-vercel-frontend.sh preview
  ./deploy-vercel-frontend.sh production

${YELLOW}Requirements:${NC}
  - Vercel CLI: npm install -g vercel
  - Node.js 18+ and npm
  - Backend API URL (Railway, Render, Fly.io, etc.)

${YELLOW}Documentation:${NC}
  See DEPLOYMENT_VERCEL.md for complete guide

${YELLOW}Quick Start:${NC}
  1. ./deploy-vercel-frontend.sh validate
  2. ./deploy-vercel-frontend.sh env
  3. ./deploy-vercel-frontend.sh preview
  4. ./deploy-vercel-frontend.sh production

HELP_EOF
}

# ========================================
# Main Script
# ========================================

main() {
    local command="${1:-help}"

    case "$command" in
        validate)
            cmd_validate
            ;;
        env|environment)
            cmd_env
            ;;
        deploy|preview)
            cmd_preview
            ;;
        production|prod)
            cmd_production
            ;;
        logs)
            cmd_logs
            ;;
        domains)
            cmd_domains
            ;;
        help|--help|-h)
            cmd_help
            ;;
        *)
            print_error "Unknown command: $command"
            echo ""
            cmd_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
