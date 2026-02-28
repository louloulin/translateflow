#!/bin/bash
# TranslateFlow Health Check Script
# Monitor application health and service status

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

# Default settings
API_URL="http://localhost:8000"
JSON_OUTPUT=false
QUICK_MODE=false
CONTINUOUS=false
INTERVAL=30
WARNING_DISK=80
WARNING_MEMORY=85

# Logging functions
log_info() {
    if [ "$JSON_OUTPUT" = false ]; then
        echo -e "${BLUE}[INFO]${NC} $1"
    fi
}

log_success() {
    if [ "$JSON_OUTPUT" = false ]; then
        echo -e "${GREEN}[OK]${NC} $1"
    fi
}

log_warning() {
    if [ "$JSON_OUTPUT" = false ]; then
        echo -e "${YELLOW}[WARNING]${NC} $1"
    fi
}

log_error() {
    if [ "$JSON_OUTPUT" = false ]; then
        echo -e "${RED}[ERROR]${NC} $1"
    fi
}

# Get environment variable from .env file
get_env_value() {
    local env_file="${PROJECT_ROOT}/.env"
    local key="$1"

    if [ -f "$env_file" ]; then
        grep "^${key}=" "$env_file" | cut -d '=' -f2- | tr -d '"'
    fi
}

# Check API health
check_api_health() {
    local endpoint="${API_URL}/api/system/status"
    local response
    local http_code
    local response_time

    response_time=$(curl -o /dev/null -s -w '%{time_total}' "$endpoint" 2>/dev/null || echo "0")

    response=$(curl -s -o /dev/null -w "%{http_code}" "$endpoint" 2>/dev/null || echo "000")
    http_code="$response"

    if [ "$JSON_OUTPUT" = true ]; then
        echo "{\"check\": \"api_health\", \"status\": $([ "$http_code" = "200" ] && echo "healthy" || echo "unhealthy"), \"http_code\": $http_code, \"response_time\": ${response_time}}"
        return
    fi

    if [ "$http_code" = "200" ]; then
        log_success "API is healthy (HTTP $http_code, ${response_time}s)"
        return 0
    else
        log_error "API is unhealthy (HTTP $http_code)"
        return 1
    fi
}

# Check database connectivity
check_database() {
    local db_host="${DB_HOST:-localhost}"
    local db_port="${DB_PORT:-5432}"
    local db_name="${DB_NAME:-translateflow}"

    if [ "$JSON_OUTPUT" = true ]; then
        local is_healthy
        if docker exec translateflow-postgres pg_isready -U "${DB_USER:-translateflow}" &>/dev/null; then
            is_healthy="healthy"
        else
            is_healthy="unhealthy"
        fi
        echo "{\"check\": \"database\", \"status\": \"${is_healthy}\", \"host\": \"${db_host}\", \"port\": ${db_port}, \"database\": \"${db_name}\"}"
        return
    fi

    if docker exec translateflow-postgres pg_isready -U "${DB_USER:-translateflow}" &>/dev/null; then
        log_success "Database is accessible (${db_host}:${db_port}/${db_name})"
        return 0
    else
        log_error "Database is not accessible"
        return 1
    fi
}

# Check container status
check_containers() {
    local containers=("translateflow-app" "translateflow-postgres")
    local all_running=true
    local container_status=()

    for container in "${containers[@]}"; do
        local status
        if docker ps | grep -q "$container"; then
            status="running"
            container_status+=("{\"name\": \"$container\", \"status\": \"running\"}")
        else
            status="stopped"
            container_status+=("{\"name\": \"$container\", \"status\": \"stopped\"}")
            all_running=false
        fi
    done

    if [ "$JSON_OUTPUT" = true ]; then
        echo "{\"check\": \"containers\", \"status\": $([ "$all_running" = true ] && echo "healthy" || echo "unhealthy"), \"containers\": [$(IFS=,; echo "${container_status[*]}")]}"
        return
    fi

    for container in "${containers[@]}"; do
        if docker ps | grep -q "$container"; then
            log_success "Container $container is running"
        else
            log_error "Container $container is not running"
            all_running=false
        fi
    done

    if [ "$all_running" = true ]; then
        return 0
    else
        return 1
    fi
}

# Check disk space
check_disk_space() {
    local usage_percent
    local available_mb

    usage_percent=$(df / | awk 'NR==2 {print int($5)}')
    available_mb=$(df -m / | awk 'NR==2 {print $4}')

    if [ "$JSON_OUTPUT" = true ]; then
        local status="healthy"
        if [ "$usage_percent" -ge "$WARNING_DISK" ]; then
            status="warning"
        fi
        echo "{\"check\": \"disk_space\", \"status\": \"${status}\", \"usage_percent\": ${usage_percent}, \"available_mb\": ${available_mb}}"
        return
    fi

    if [ "$usage_percent" -ge "$WARNING_DISK" ]; then
        log_warning "Disk space is ${usage_percent}% used (${available_mb}MB available)"
        return 1
    else
        log_success "Disk space is ${usage_percent}% used (${available_mb}MB available)"
        return 0
    fi
}

# Check memory usage
check_memory() {
    local total_mb
    local used_mb
    local usage_percent

    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        total_mb=$(sysctl hw.memsize | awk '{print int($2/1024/1024)}')
        used_mb=$(vm_stat | perl -ne '/page size of (\d+)/ and $ps=$1; /Pages\s+([^ ]+)\s+free/ and printf "%d", $1*$ps/1024/1024; END { print $total_mb - $used_mb }')
        usage_percent=$((used_mb * 100 / total_mb))
    else
        # Linux
        local mem_info
        mem_info=$(free -m | grep Mem)
        total_mb=$(echo $mem_info | awk '{print $2}')
        used_mb=$(echo $mem_info | awk '{print $3}')
        usage_percent=$((used_mb * 100 / total_mb))
    fi

    if [ "$JSON_OUTPUT" = true ]; then
        local status="healthy"
        if [ "$usage_percent" -ge "$WARNING_MEMORY" ]; then
            status="warning"
        fi
        echo "{\"check\": \"memory\", \"status\": \"${status}\", \"usage_percent\": ${usage_percent}, \"used_mb\": ${used_mb}, \"total_mb\": ${total_mb}}"
        return
    fi

    if [ "$usage_percent" -ge "$WARNING_MEMORY" ]; then
        log_warning "Memory usage is ${usage_percent}% (${used_mb}MB / ${total_mb}MB)"
        return 1
    else
        log_success "Memory usage is ${usage_percent}% (${used_mb}MB / ${total_mb}MB)"
        return 0
    fi
}

# Check Docker daemon
check_docker() {
    if [ "$JSON_OUTPUT" = true ]; then
        local status="healthy"
        if ! docker info &>/dev/null; then
            status="unhealthy"
        fi
        echo "{\"check\": \"docker\", \"status\": \"${status}\"}"
        return
    fi

    if docker info &>/dev/null; then
        log_success "Docker daemon is running"
        return 0
    else
        log_error "Docker daemon is not accessible"
        return 1
    fi
}

# Run all health checks
run_all_checks() {
    local exit_code=0
    local results=()

    if [ "$JSON_OUTPUT" = true ]; then
        echo "["
    fi

    # Docker check
    if ! check_docker; then
        exit_code=1
    fi
    if [ "$JSON_OUTPUT" = true ] && [ "$QUICK_MODE" = false ]; then
        echo ","
    fi

    # API health
    if [ "$QUICK_MODE" = false ]; then
        if ! check_api_health; then
            exit_code=1
        fi
        if [ "$JSON_OUTPUT" = true ]; then
            echo ","
        fi
    fi

    # Database
    if ! check_database; then
        exit_code=1
    fi
    if [ "$JSON_OUTPUT" = true ] && [ "$QUICK_MODE" = false ]; then
        echo ","
    fi

    # Containers
    if ! check_containers; then
        exit_code=1
    fi
    if [ "$JSON_OUTPUT" = true ] && [ "$QUICK_MODE" = false ]; then
        echo ","
    fi

    # Disk space (skip in quick mode)
    if [ "$QUICK_MODE" = false ]; then
        if ! check_disk_space; then
            # Disk warnings don't fail the health check
            true
        fi
        if [ "$JSON_OUTPUT" = true ]; then
            echo ","
        fi
    fi

    # Memory (skip in quick mode)
    if [ "$QUICK_MODE" = false ]; then
        if ! check_memory; then
            # Memory warnings don't fail the health check
            true
        fi
    fi

    if [ "$JSON_OUTPUT" = true ]; then
        echo
        echo "]"
    fi

    return $exit_code
}

# Continuous monitoring mode
continuous_monitoring() {
    log_info "Starting continuous monitoring (interval: ${interval}s, press Ctrl+C to stop)"

    local iteration=0
    while true; do
        iteration=$((iteration + 1))

        if [ "$JSON_OUTPUT" = false ]; then
            echo
            echo "=========================================="
            echo "Health Check - Iteration $iteration"
            echo "=========================================="
        fi

        run_all_checks || true

        if [ "$JSON_OUTPUT" = false ]; then
            echo "=========================================="
        fi

        sleep "$INTERVAL"
    done
}

# Show detailed health report
show_detailed_report() {
    echo "=========================================="
    echo "TranslateFlow Health Report"
    echo "=========================================="
    echo

    # Load .env file for configuration
    if [ -f "${PROJECT_ROOT}/.env" ]; then
        set -a
        source "${PROJECT_ROOT}/.env"
        set +a
    fi

    # Docker
    echo -n "Docker Daemon: "
    check_docker
    echo

    # Containers
    echo "Container Status:"
    check_containers
    echo

    # API Health
    echo -n "API Health: "
    check_api_health
    echo

    # Database
    echo -n "Database: "
    check_database
    echo

    # Resources
    echo "Resource Usage:"
    check_disk_space
    check_memory
    echo

    echo "=========================================="
}

# Show help
show_help() {
    cat << EOF
TranslateFlow Health Check Script

Usage: ./scripts/health-check.sh [OPTIONS]

Options:
    -u, --url <url>          API URL to check (default: http://localhost:8000)
    -j, --json               Output in JSON format
    -q, --quick              Quick mode (only essential checks)
    -c, --continuous         Continuous monitoring mode
    -i, --interval <seconds> Check interval for continuous mode (default: 30)
    -w, --warning-disk <pct> Disk usage warning threshold (default: 80)
    -m, --warning-mem <pct>  Memory usage warning threshold (default: 85)
    -h, --help               Show this help message

Exit Codes:
    0 - All checks passed
    1 - One or more checks failed

Examples:
    # Run all health checks
    ./scripts/health-check.sh

    # Quick health check (essential only)
    ./scripts/health-check.sh --quick

    # JSON output for monitoring systems
    ./scripts/health-check.sh --json

    # Check custom API URL
    ./scripts/health-check.sh --url https://api.translateflow.com

    # Continuous monitoring
    ./scripts/health-check.sh --continuous --interval 60

    # CI/CD integration
    ./scripts/health-check.sh --quick --json || exit 1

Checks Performed:
    1. Docker Daemon - Verify Docker is accessible
    2. API Health - Check /api/system/status endpoint
    3. Database - Verify PostgreSQL connectivity
    4. Containers - Check all service containers are running
    5. Disk Space - Monitor disk usage (warning threshold)
    6. Memory - Monitor memory usage (warning threshold)

For CI/CD Integration:
    Use --quick --json flags for fast, machine-readable output:
        ./scripts/health-check.sh --quick --json

    The script returns exit code 0 on success, 1 on failure.
EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -u|--url)
                API_URL="$2"
                shift 2
                ;;
            -j|--json)
                JSON_OUTPUT=true
                shift
                ;;
            -q|--quick)
                QUICK_MODE=true
                shift
                ;;
            -c|--continuous)
                CONTINUOUS=true
                shift
                ;;
            -i|--interval)
                INTERVAL="$2"
                shift 2
                ;;
            -w|--warning-disk)
                WARNING_DISK="$2"
                shift 2
                ;;
            -m|--warning-mem)
                WARNING_MEMORY="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Main execution
main() {
    parse_args "$@"

    # Load environment for database checks
    if [ -f "${PROJECT_ROOT}/.env" ]; then
        set -a
        source "${PROJECT_ROOT}/.env"
        set +a
    fi

    # Continuous monitoring mode
    if [ "$CONTINUOUS" = true ]; then
        continuous_monitoring
        exit 0
    fi

    # Show detailed report unless JSON output
    if [ "$JSON_OUTPUT" = false ] && [ "$QUICK_MODE" = false ]; then
        show_detailed_report
        exit
    fi

    # Run health checks
    run_all_checks
}

# Run main function
main "$@"
