#!/bin/bash
# Multi-platform Docker build script for TranslateFlow
# Supports AMD64 and ARM64 architectures

set -e

# Configuration
IMAGE_NAME="${IMAGE_NAME:-translateflow}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
REGISTRY="${REGISTRY:-ghcr.io/}"
PLATFORMS="${PLATFORMS:-linux/amd64,linux/arm64}"

# Build metadata
BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
VCS_REF="$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
VERSION="${VERSION:-$(git describe --tags --abbrev=0 2>/dev/null || echo '1.0.0')}"

echo "🐳 Multi-platform Docker Build for TranslateFlow"
echo "═══════════════════════════════════════════════════"
echo "Image: ${REGISTRY}${IMAGE_NAME}:${IMAGE_TAG}"
echo "Platforms: ${PLATFORMS}"
echo "Version: ${VERSION}"
echo "Build Date: ${BUILD_DATE}"
echo "Git Ref: ${VCS_REF}"
echo ""

# Check if buildx is available
if ! docker buildx version &>/dev/null; then
    echo "❌ Error: docker buildx not available"
    echo "Please ensure you're using Docker Buildx (Docker 19.03+)"
    exit 1
fi

# Create and use buildx builder
echo "🔨 Setting up buildx builder..."
BUILDER_NAME="translateflow-builder"

if ! docker buildx inspect "$BUILDER_NAME" &>/dev/null; then
    docker buildx create --name "$BUILDER_NAME" --driver docker-container --use
    docker buildx inspect --bootstrap
else
    docker buildx use "$BUILDER_NAME"
fi

# Build arguments
BUILD_ARGS=(
    --build-arg "BUILD_DATE=${BUILD_DATE}"
    --build-arg "VCS_REF=${VCS_REF}"
    --build-arg "VERSION=${VERSION}"
)

# Build options
BUILD_OPTIONS=(
    --platform "${PLATFORMS}"
    --file "./Dockerfile"
    --tag "${REGISTRY}${IMAGE_NAME}:${IMAGE_TAG}"
    --tag "${REGISTRY}${IMAGE_NAME}:${VERSION}"
    --progress "plain"
    --push
    "${BUILD_ARGS[@]}"
    "."
)

echo "🚀 Starting build..."
echo "Command: docker buildx build ${BUILD_OPTIONS[@]}"
echo ""

# Execute build
docker buildx build "${BUILD_OPTIONS[@]}"

echo ""
echo "✅ Build completed successfully!"
echo "═══════════════════════════════════════════════════"
echo "Images:"
echo "  - ${REGISTRY}${IMAGE_NAME}:${IMAGE_TAG}"
echo "  - ${REGISTRY}${IMAGE_NAME}:${VERSION}"
echo ""
echo "To test locally, pull and run:"
echo "  docker pull ${REGISTRY}${IMAGE_NAME}:${IMAGE_TAG}"
echo "  docker run -p 8000:8000 ${REGISTRY}${IMAGE_NAME}:${IMAGE_TAG}"
