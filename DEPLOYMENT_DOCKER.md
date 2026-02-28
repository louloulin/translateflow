# TranslateFlow Docker Deployment Guide

This guide explains how to deploy TranslateFlow using Docker and Docker Compose.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Production Dockerfile](#production-dockerfile)
- [Docker Compose Deployment](#docker-compose-deployment)
- [Multi-Platform Builds](#multi-platform-builds)
- [Production Setup](#production-setup)
- [Security Checklist](#security-checklist)
- [Scaling](#scaling)
- [Troubleshooting](#troubleshooting)
- [Support](#support)

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 2GB RAM available
- At least 5GB disk space

## Quick Start

### 1. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env  # or use your preferred editor
```

**Important:** Update these values in `.env` before deploying:
- `DB_PASSWORD` - Set a strong password
- `SECRET_KEY` - Generate with: `openssl rand -hex 32`
- Email provider credentials (optional but recommended)
- Stripe credentials (if using billing features)

### 2. Start the Application

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

### 3. Access TranslateFlow

Open your browser and navigate to:
- **http://localhost:8000** (or your configured PORT)

Default admin credentials:
- Username: `admin`
- Password: `admin` ⚠️ **Change this immediately after first login!**

## Production Dockerfile

TranslateFlow includes an optimized production Dockerfile (`Dockerfile.production`) with the following enhancements:

### Optimizations

1. **Security**
   - ✅ Non-root user execution (runs as `translateflow` user, UID 1000)
   - ✅ Minimal attack surface (Alpine-based images)
   - ✅ No unnecessary system packages

2. **Image Size Reduction**
   - ✅ Multi-stage build (separate build and runtime stages)
   - ✅ Cleanup in same layer (apt cache, build artifacts)
   - ✅ Optimized layer caching

3. **Health Monitoring**
   - ✅ Built-in health check (`/api/system/status` endpoint)
   - ✅ 30s check interval with 10s timeout
   - ✅ 40s startup grace period
   - ✅ 3 retries before marking unhealthy

4. **Build Metadata**
   - ✅ OCI-compliant labels (version, build date, git ref)
   - ✅ Reproducible builds

5. **Performance**
   - ✅ Python memory allocator optimization
   - ✅ UV package manager for fast dependency installation
   - ✅ Optimized environment variables

### Dockerfile Variants

| File | Use Case |
|------|----------|
| `Dockerfile` | Production (symlink to `Dockerfile.production`) |
| `Dockerfile.production` | Optimized for production deployment |
| `Dockerfile.development` | Original Dockerfile for development |

### Building the Production Image

```bash
# Standard build (AMD64 only)
docker build -f Dockerfile.production -t translateflow:latest .

# Build with build arguments
docker build \
  -f Dockerfile.production \
  --build-arg VERSION=1.0.0 \
  --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  --build-arg VCS_REF=$(git rev-parse --short HEAD) \
  -t translateflow:latest .

# Build for specific platform
docker buildx build \
  --platform linux/amd64 \
  -f Dockerfile.production \
  -t translateflow:latest \
  --load \
  .
```

## Multi-Platform Builds

TranslateFlow supports multi-platform builds for AMD64 and ARM64 architectures using the provided build script:

```bash
# Build for multiple platforms and push to registry
./scripts/build-docker-multiplatform.sh

# With custom configuration
IMAGE_NAME=my-translateflow \
IMAGE_TAG=v1.0.0 \
REGISTRY=ghcr.io/myorg/ \
VERSION=1.0.0 \
./scripts/build-docker-multiplatform.sh
```

**Requirements:**
- Docker Buildx (Docker 19.03+)
- QEMU emulator for cross-platform builds: `docker run --privileged --rm tonistiigi/binfmt --install all`

**Supported Platforms:**
- `linux/amd64` - Standard x86_64 servers
- `linux/arm64` - ARM64 servers (Apple Silicon, AWS Graviton, etc.)

## Docker Compose Deployment

The `docker-compose.yml` file orchestrates the following services:

- **app** - TranslateFlow application (FastAPI + React)
- **postgres** - PostgreSQL database

### Starting and Stopping

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart specific service
docker-compose restart app

# Stop and remove all containers, networks, and volumes
docker-compose down -v
```

### Viewing Logs

```bash
# View all logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# View logs for specific service
docker-compose logs app
docker-compose logs postgres
```

### Database Management

```bash
# Access PostgreSQL directly
docker-compose exec postgres psql -U translateflow -d translateflow

# Create database backup
docker-compose exec postgres pg_dump -U translateflow translateflow > backup.sql

# Restore database backup
docker-compose exec -T postgres psql -U translateflow translateflow < backup.sql

# Reset database (⚠️ deletes all data)
docker-compose down -v
docker-compose up -d
```

### Updating TranslateFlow

```bash
# Pull latest changes
git pull

# Rebuild and restart containers
docker-compose up -d --build

# Clean up old images (optional)
docker image prune -f
```

## Troubleshooting

### Service Won't Start

```bash
# Check service status
docker-compose ps

# View detailed logs
docker-compose logs app
docker-compose logs postgres

# Check resource usage
docker stats
```

### Database Connection Issues

1. Verify PostgreSQL is healthy:
```bash
docker-compose exec postgres pg_isready -U translateflow
```

2. Check database logs:
```bash
docker-compose logs postgres
```

3. Ensure database is initialized (tables created automatically on first run)

### Port Already in Use

If port 8000 is already in use, modify the `PORT` in `.env`:
```bash
echo "PORT=8080" >> .env
docker-compose restart app
```

### Permission Issues with Volumes

```bash
# Fix volume permissions (Linux only)
sudo chown -R $USER:$USER ./output ./updatetemp
```

### Reset Everything

If you need to completely reset your deployment:

```bash
# Stop and remove all containers, networks, and volumes
docker-compose down -v

# Remove all images
docker rmi $(docker images -q translateflow*)

# Start fresh
docker-compose up -d
```

## Production Deployment

For production deployments, consider these additional steps:

### 1. Use a Reverse Proxy

Set up Nginx or Traefik as a reverse proxy:
- Handles SSL/TLS certificates
- Provides load balancing
- Adds security headers

Example Nginx configuration:
```nginx
server {
    listen 80;
    server_name translateflow.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name translateflow.example.com;

    ssl_certificate /etc/letsencrypt/live/translateflow.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/translateflow.example.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. Enable SSL/TLS

Use Let's Encrypt with certbot:
```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d translateflow.example.com
```

### 3. Set Up Automated Backups

Create a cron job for daily backups:
```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /path/to/backup-script.sh
```

Example backup script:
```bash
#!/bin/bash
# backup-translateflow.sh

BACKUP_DIR="/backups/translateflow"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"
docker-compose exec -T postgres pg_dump -U translateflow translateflow > "$BACKUP_DIR/translateflow_$DATE.sql"
find "$BACKUP_DIR" -name "translateflow_*.sql" -mtime +7 -delete
```

### 4. Configure Firewall

```bash
# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow SSH (adjust port as needed)
sudo ufw allow 22/tcp

# Enable firewall
sudo ufw enable
```

### 5. Set Up Monitoring

Consider adding monitoring tools:
- **Prometheus + Grafana** for metrics
- **Sentry** for error tracking
- **Uptime Robot** for availability monitoring

## Scaling

### Vertical Scaling

Add more resources to your server:
- Increase Docker resource limits in `docker-compose.yml`:
```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

### Horizontal Scaling (with Docker Swarm)

```bash
# Initialize swarm
docker swarm init

# Deploy with replicas
docker stack deploy -c docker-compose.yml translateflow

# Scale app service
docker service scale translateflow_app=3
```

**Note:** Horizontal scaling requires:
- Load balancer (Traefik, Nginx)
- Shared session storage (Redis)
- Shared file storage (NFS, S3)

## Security Checklist

- [ ] Change default admin password
- [ ] Use strong `SECRET_KEY` (generate with `openssl rand -hex 32`)
- [ ] Set strong database password
- [ ] Enable SSL/TLS in production
- [ ] Configure firewall rules
- [ ] Set up automated backups
- [ ] Review OAuth redirect URIs
- [ ] Configure rate limiting
- [ ] Set up monitoring and alerting
- [ ] Regular security updates (`docker-compose pull && docker-compose up -d --build`)

## Support

- **Documentation:** [Main README](../README.md)
- **Issues:** [GitHub Issues](https://github.com/ShadowLoveElysia/TranslateFlow/issues)
- **Deployment Analysis:** `.ralph/agent/DEPLOYMENT_ANALYSIS.md`
