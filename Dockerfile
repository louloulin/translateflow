# Stage 1: Build the React Frontend
FROM node:20-alpine AS builder

WORKDIR /web

# Copy package files first to leverage Docker cache
COPY Tools/WebServer/package.json Tools/WebServer/package-lock.json ./

# Install dependencies
RUN npm ci --production=false

# Copy the rest of the frontend source code
COPY Tools/WebServer/ ./

# Build the frontend (production mode)
RUN npm run build && \
    # Clean up build artifacts to reduce layer size
    rm -rf node_modules cache .vite

# Stage 2: Final Python Image (Production Optimized)
FROM python:3.12-slim

# Set build-time arguments for metadata
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=1.0.0

# Add labels for metadata
LABEL org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.title="TranslateFlow" \
      org.opencontainers.image.description="AI-powered translation tool with team collaboration" \
      org.opencontainers.image.authors="TranslateFlow Team" \
      org.opencontainers.image.source="https://github.com/ShadowLoveElysia/TranslateFlow"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    RUNNING_IN_DOCKER=true \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # Optimize Python memory
    PYTHONMALLOC=malloc \
    # Path configuration
    PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    # Increase UV HTTP timeout for large package downloads
    UV_HTTP_TIMEOUT=600 \
    UV_REQUEST_TIMEOUT=600

# Set working directory
WORKDIR /app

# Install system dependencies and cleanup in a single layer
# Minimal dependencies for headless server (no X11/display needed)
# - libgomp1: OpenMP support (for NumPy, pandas)
# - libjpeg-dev, zlib1g, libfreetype6, liblcms2-2, libwebp-dev, libtiff-dev: Image codecs for Pillow
# - curl, ca-certificates: For HTTP requests and SSL
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    libjpeg-dev \
    zlib1g \
    libfreetype6 \
    liblcms2-2 \
    libwebp-dev \
    libtiff-dev \
    curl \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create non-root user for security
RUN groupadd -r translateflow && \
    useradd -r -g translateflow -u 1000 -m -s /sbin/nologin translateflow

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy project definition files (no ownership change, root will install)
COPY pyproject.toml uv.lock README.md LICENSE ./

# Install Python dependencies as root
RUN uv sync --frozen --no-install-project --no-dev && \
    # Change ownership to translateflow user
    chown -R translateflow:translateflow /app && \
    # Clean up uv cache
    rm -rf /root/.cache/uv /tmp/*

# Copy application source code with proper ownership
COPY --chown=translateflow:translateflow ainiee_cli.py ./
COPY --chown=translateflow:translateflow 批量电子书整合.py ./
COPY --chown=translateflow:translateflow ModuleFolders/ ./ModuleFolders/
COPY --chown=translateflow:translateflow Resource/ ./Resource/
COPY --chown=translateflow:translateflow PluginScripts/ ./PluginScripts/
COPY --chown=translateflow:translateflow StevExtraction/ ./StevExtraction/
COPY --chown=translateflow:translateflow I18N/ ./I18N/
COPY --chown=translateflow:translateflow Tools/ ./Tools/

# Copy the built frontend assets from the builder stage
COPY --from=builder --chown=translateflow:translateflow /web/dist ./Tools/WebServer/dist

# Create necessary directories for data and set permissions
RUN mkdir -p /app/output /app/updatetemp && \
    chown -R translateflow:translateflow /app/output /app/updatetemp

# Switch to non-root user
USER translateflow

# Expose Web Server port
EXPOSE 8000

# Health check using the /api/system/status endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/system/status || exit 1

# Set entrypoint - run FastAPI web server directly (not interactive CLI)
ENTRYPOINT ["uv", "run", "python", "-m", "uvicorn", "Tools.WebServer.web_server:app", "--host", "0.0.0.0", "--port", "8000"]
