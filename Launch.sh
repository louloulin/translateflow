#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v uv &> /dev/null; then
    # Try to source cargo env in case it was just installed
    if [ -f "$HOME/.cargo/env" ]; then
        source "$HOME/.cargo/env"
    fi
    
    if ! command -v uv &> /dev/null; then
        echo "[ERROR] uv is not installed."
        echo "Please run './prepare.sh' first to set up the environment."
        exit 1
    fi
fi

echo "Starting AiNiee CLI..."
exec uv run "$SCRIPT_DIR/ainiee_cli.py" "$@"
