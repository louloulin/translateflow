# TranslateFlow Deployment Analysis Report

## Executive Summary

TranslateFlow (formerly AiNiee-Next) is a high-performance AI translation platform with a modern web interface. The application consists of a Python FastAPI backend, React frontend, and supports multiple deployment scenarios including containerized and serverless environments.

**Architecture Type:** Monolithic web application with modular service architecture
**Primary Language:** Python 3.12 (backend), TypeScript/JavaScript (frontend)
**Framework Stack:** FastAPI + React 19.2.3 + Vite
**Database:** PostgreSQL (primary) with SQLite fallback
**Deployment Ready:** ✅ Has existing Dockerfile

---

## 1. Application Architecture

### 1.1 Backend Components

**Entry Point:** `ainiee_cli.py` (CLI launcher)
**Web Server:** `Tools/WebServer/web_server.py` (FastAPI application)

**Core Modules:**
```
ModuleFolders/
├── Base/              # Core framework and TUI handlers
├── CLI/               # Command-line interface components
├── Domain/            # Business domain models
├── Infrastructure/    # Database and external integrations
│   └── Database/      # PostgreSQL/SQLite abstraction layer
├── Service/           # Business logic services
│   ├── Auth/          # Authentication, JWT, OAuth (GitHub/Google)
│   ├── Billing/       # Stripe payment integration
│   ├── Email/         # Email service (Resend/SendGrid/SMTP)
│   ├── Team/          # Team management and quotas
│   └── User/          # User management
└── UserInterface/     # TUI components
```

**Startup Process:**
1. CLI launches via `ainiee_cli.py`
2. Web server starts via `Tools/WebServer/web_server.py:run_server()`
3. Uses `uvicorn` ASGI server on port 8000 (configurable)
4. Frontend served from `Tools/WebServer/dist/` as static files

### 1.2 Frontend Components

**Location:** `Tools/WebServer/`
**Framework:** React 19.2.3 with TypeScript
**Build Tool:** Vite 6.2.0
**UI Library:** Radix UI + Tailwind CSS
**Editor:** Monaco Editor

**Build Process:**
```bash
cd Tools/WebServer
npm install
npm run build  # Outputs to dist/
```

**Deployment Assets:**
- Static files in `Tools/WebServer/dist/`
- Served by FastAPI `StaticFiles` mount at root `/`
- SPA fallback to `index.html` for client-side routing

---

## 2. Dependencies & Services

### 2.1 Database Layer

**Primary:** PostgreSQL with connection pooling
**Fallback:** SQLite for development

**Environment Variables:**
```bash
# PostgreSQL (preferred)
DATABASE_URL="postgresql://user:pass@host:5432/dbname"
# OR individual parameters
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ainiee
DB_USER=postgres
DB_PASSWORD=secret

# SQLite fallback
USE_SQLITE=true
SQLITE_PATH=ainiee.db
```

**Connection Pool:**
- Max connections: 10
- Connection timeout: 10s
- Stale timeout: 300s (5 minutes)

**Models:** Peewee ORM with auto-initialization
**Tables:**
- Users, Tenants, Roles
- Teams, TeamMembers
- Subscriptions, Payments
- Cache data, Projects

### 2.2 External Services

**Email Service (Optional but Recommended):**
```bash
EMAIL_PROVIDER=resend|sendgrid|smtp
RESEND_API_KEY=...
SENDGRID_API_KEY=...
SMTP_HOST=...
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...
EMAIL_FROM=noreply@translateflow.example.com
EMAIL_FROM_NAME=TranslateFlow
EMAIL_REPLY_TO=...
```

**Payment Integration (Stripe):**
```bash
STRIPE_API_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_FREE=price_...
STRIPE_PRICE_STARTER=price_...
STRIPE_PRICE_PRO=price_...
STRIPE_PRICE_ENTERPRISE=price_...
```

**OAuth Providers (Optional):**
```bash
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
OAUTH_REDIRECT_URI=https://yourdomain.com/auth/callback
```

### 2.3 Python Dependencies

**Core Runtime:**
- Python 3.12 (exact version required)
- FastAPI + Uvicorn (ASGI server)
- Pydantic (data validation)
- python-multipart (file uploads)

**AI/ML Libraries:**
- openai, anthropic, cohere, google-genai (LLM providers)
- tiktoken (token counting)
- spacy, sudachipy (NER/segmentation)
- mediapipe, onnxruntime (OCR/processing)
- transformers, huggingface-hub (ML models)

**Utilities:**
- peewee (ORM)
- rich (TUI)
- httpx (HTTP client with HTTP/2)
- rapidjson, orjson (JSON parsing)
- pdfminer-six, pymupdf (PDF parsing)
- python-pptx, openpyxl, polib (Office formats)

**System Requirements:**
- ~2GB RAM minimum (for ML models)
- ~5GB disk space (including models)
- Linux/macOS/Windows support

---

## 3. Data Persistence

### 3.1 Database Volumes

**PostgreSQL Data:** `/var/lib/postgresql/data`
**SQLite File:** `ainiee.db` (in project root or mounted volume)

### 3.2 File Storage

**Upload Directory:** `updatetemp/` (project root)
**Output Directory:** `output/` (project root)
**Cache Files:** User project directories

**Recommendation:** Use Docker volumes or bind mounts for persistence.

---

## 4. Network Architecture

### 4.1 Ports

| Service | Port | Notes |
|---------|------|-------|
| Backend API | 8000 | FastAPI/Uvicorn |
| Frontend Dev | 4200 | Vite dev server (not needed in prod) |
| PostgreSQL | 5432 | Internal only |

### 4.2 Health Endpoints

```
GET /api/health        # Basic health check
GET /api/proofread/status  # Service status
GET /api/translate/status   # Task status
```

---

## 5. Security Considerations

### 5.1 Authentication

- JWT-based authentication (`ModuleFolders/Service/Auth/jwt_handler.py`)
- OAuth integration (GitHub, Google)
- Password hashing with PasswordManager
- Default admin user created on startup: `admin/admin` (CHANGE IN PRODUCTION!)

### 5.2 API Security

- CORS middleware configured
- OAuth2PasswordBearer for API endpoints
- Team-based access control
- Rate limiting (should be added)

### 5.3 Production Checklist

- [ ] Change default admin password
- [ ] Set strong `SECRET_KEY` for JWT signing
- [ ] Configure HTTPS/TLS
- [ ] Enable database SSL
- [ ] Set up firewall rules
- [ ] Configure backup strategy
- [ ] Review OAuth redirect URIs
- [ ] Set up monitoring and logging

---

## 6. Current Deployment Status

### 6.1 Existing Docker Configuration

**Dockerfile:** ✅ Present (multi-stage build)
- Stage 1: Node.js 20 for frontend build
- Stage 2: Python 3.12-slim for runtime
- Uses `uv` package manager for dependencies
- Exposes port 8000
- Health checks: ❌ Not configured

**Docker Publish Workflow:** ✅ GitHub Actions configured
- `.github/workflows/docker-publish.yml`
- Builds and pushes to `ghcr.io`
- Supports tags and releases
- Includes Cosign signing

**Missing:**
- ❌ docker-compose.yml
- ❌ Production environment variables template
- ❌ Health check endpoints in Dockerfile
- ❌ Non-root user configuration
- ❌ Multi-platform builds (ARM64)

### 6.2 Vercel Configuration

**Current Status:** ⚠️ Partially configured
- `.vercel/project.json` present (minimal config)
- No serverless adapter
- FastAPI → Vercel requires adapter (e.g., Mangum)

**Challenges:**
- Vercel is Node.js/serverless optimized
- Python FastAPI needs:
  1. Serverless adapter (Mangum/Vercel Python Runtime)
  2. External database (cannot use SQLite)
  3. File storage (S3 compatible)
  4. Static asset handling (separate frontend deployment)

**Recommended:** Use Vercel for frontend only, deploy backend to container platform (Railway, Render, or Docker).

### 6.3 Dokploy Configuration

**Current Status:** ❌ Not configured
- Dokploy is a self-hosted PaaS (similar to CapRover/PeliCAN)
- Requires docker-compose.yml
- Will work well with existing Dockerfile

---

## 7. Deployment Scenarios

### 7.1 Docker Compose (Recommended for Production)

**Use Case:** Self-hosted production deployment
**Complexity:** Medium
**Cost:** Low (server cost only)

**Requirements:**
- docker-compose.yml
- Environment variables (.env)
- Persistent volumes
- Reverse proxy (Nginx/Traefik) optional

**Advantages:**
- Full control over environment
- Easy local development
- Simple scaling with Docker Swarm
- Works with Dokploy/CapRover

### 7.2 Container Hosting (Railway, Render, DigitalOcean App Platform)

**Use Case:** Managed container deployment
**Complexity:** Low
**Cost:** Medium ($5-20/month starting)

**Requirements:**
- Existing Dockerfile works
- Environment variables in platform UI
- Managed database add-on
- Domain configuration

**Advantages:**
- No server management
- Auto-scaling
- Built-in SSL
- Easy rollbacks

### 7.3 Vercel (Frontend Only)

**Use Case:** Static frontend deployment with external API
**Complexity:** Low
**Cost:** Free tier available

**Requirements:**
- Build frontend separately
- Deploy backend elsewhere
- Configure CORS properly

**Advantages:**
- Global CDN
- Automatic HTTPS
- Preview deployments
- Fast builds

### 7.4 Self-Hosted VPS (Dokploy, CapRover, PeliCAN)

**Use Case:** Full control on own infrastructure
**Complexity:** High
**Cost:** Low ($5-10/month VPS)

**Requirements:**
- VPS with Docker installed
- Dokploy/CapRover installation
- Domain with DNS configured
- SSL certificate (Let's Encrypt)

**Advantages:**
- Complete control
- Unlimited apps on same server
- Privacy-focused
- Cost-effective for multiple services

---

## 8. Recommended Deployment Strategy

### Phase 1: Docker Compose (Foundation)
1. Create docker-compose.yml with all services
2. Create .env.example with all required variables
3. Add health checks to Dockerfile
4. Test locally and document

### Phase 2: Production Optimizations
1. Add Nginx reverse proxy
2. Configure SSL with Let's Encrypt
3. Set up automated backups
4. Add monitoring (Prometheus/Grafana)

### Phase 3: Platform-Specific Deployments
1. Create Dokploy configuration
2. Optimize for Vercel (frontend only)
3. Create deployment scripts
4. Write comprehensive documentation

---

## 9. Critical Next Steps

1. ✅ **Analysis Complete** (This document)
2. ⏳ **Create Docker Compose** - High priority
3. ⏳ **Optimize Dockerfile** - High priority
4. ⏳ **Environment Template** - High priority
5. ⏳ **Deployment Scripts** - Medium priority
6. ⏳ **Platform Configurations** - Medium priority
7. ⏳ **Documentation** (planx.md) - High priority

---

## 10. File Inventory

### Configuration Files
- ✅ `Dockerfile` - Multi-stage container build
- ✅ `pyproject.toml` - Python dependencies (uv format)
- ✅ `requirements.txt` - Fallback pip requirements
- ✅ `Tools/WebServer/package.json` - Frontend dependencies
- ✅ `.github/workflows/docker-publish.yml` - CI/CD pipeline
- ❌ `docker-compose.yml` - **NEEDS CREATION**
- ❌ `.env.example` - **NEEDS CREATION**

### Deployment Scripts
- ❌ `deploy.sh` - **NEEDS CREATION**
- ❌ `scripts/health-check.sh` - **NEEDS CREATION**
- ❌ `scripts/migrate-db.sh` - **NEEDS CREATION**

### Documentation
- ✅ `README.md` - User documentation
- ❌ `planx.md` - **NEEDS CREATION** (Deployment guide)
- ❌ `DEPLOYMENT.md` - **NEEDS CREATION** (Platform-specific guides)

---

## Appendix A: Complete Environment Variable Reference

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/ainiee
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ainiee
DB_USER=postgres
DB_PASSWORD=changeme
USE_SQLITE=false
SQLITE_PATH=ainiee.db

# Application
SECRET_KEY=changeme-in-production
PYTHONUNBUFFERED=1
RUNNING_IN_DOCKER=true

# Email (choose one provider)
EMAIL_PROVIDER=resend
RESEND_API_KEY=re_...
SENDGRID_API_KEY=SG....
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=user@example.com
SMTP_PASSWORD=changeme
SMTP_USE_TLS=true
EMAIL_FROM=noreply@translateflow.example.com
EMAIL_FROM_NAME=TranslateFlow
EMAIL_REPLY_TO=support@example.com

# Stripe (billing)
STRIPE_API_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_FREE=price_...
STRIPE_PRICE_STARTER=price_...
STRIPE_PRICE_PRO=price_...
STRIPE_PRICE_ENTERPRISE=price_...

# OAuth (optional)
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
OAUTH_REDIRECT_URI=https://yourdomain.com/auth/callback

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

---

**Analysis Date:** 2026-02-28
**Analyzed By:** Ralph (Automated Analysis)
**Version:** Based on commit 793b2b01
