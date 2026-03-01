#!/bin/bash
# Setup script for Docker volume permissions
# Run this script once before starting the Docker container

set -e

echo "========================================="
echo "TranslateFlow Docker Volume Setup"
echo "========================================="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "[Setup] Creating required directories..."
mkdir -p output updatetemp data Resource/profiles

echo ""
echo "[Setup] Setting directory ownership to UID 1000:1000 (translateflow user)..."
sudo chown -R 1000:1000 output updatetemp data Resource

echo ""
echo "[Setup] Setting directory permissions..."
chmod -R 755 output updatetemp data Resource
chmod -R 644 Resource/* 2>/dev/null || true

echo ""
echo "[Setup] Ensuring Resource subdirectories have correct permissions..."
find Resource -type d -exec chmod 755 {} \;
find Resource -type f -exec chmod 644 {} \;

echo ""
echo "[Setup] Verifying permissions..."
ls -la | grep -E "output|updatetemp|data|Resource"
echo ""
ls -la Resource/

echo ""
echo "✓ Setup complete!"
echo ""
echo "You can now start the container with:"
echo "  docker-compose -f docker-compose.local.yml up -d"
echo ""
