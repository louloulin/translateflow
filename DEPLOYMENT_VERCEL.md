# TranslateFlow Vercel Deployment Guide

This guide covers deploying TranslateFlow to Vercel and compatible container platforms. TranslateFlow uses a **decoupled architecture**: frontend on Vercel (React SPA) and backend on a container platform (FastAPI/Python).

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Deployment Options](#deployment-options)
3. [Quick Start - Recommended Setup](#quick-start---recommended-setup)
4. [Step-by-Step Guide](#step-by-step-guide)
5. [Platform-Specific Instructions](#platform-specific-instructions)
6. [Configuration & Environment Variables](#configuration--environment-variables)
7. [Custom Domains](#custom-domains)
8. [Monitoring & Analytics](#monitoring--analytics)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)

---

## Architecture Overview

TranslateFlow is a full-stack application with separate frontend and backend:

```
┌─────────────────┐         ┌─────────────────┐
│   Vercel CDN    │         │   Container     │
│                 │         │   Platform      │
│  React Frontend │◄───────►│  FastAPI Backend│
│  (Static SPA)   │  HTTPS  │  (Python 3.12)  │
└─────────────────┘         └─────────────────┘
                                      │
                                      ▼
                              ┌───────────────┐
                              │ Managed       │
                              │ PostgreSQL    │
                              └───────────────┘
```

### Why This Architecture?

**Frontend on Vercel:**
- ✅ Global CDN distribution
- ✅ Automatic HTTPS
- ✅ Preview deployments
- ✅ Fast build times
- ✅ Free tier available

**Backend on Container Platform:**
- ✅ Long-running processes (ML models, OCR)
- ✅ File upload handling
- ✅ WebSocket support (if needed)
- ✅ Full Python environment control
- ✅ Persistent connections

---

## Deployment Options

| Option | Frontend | Backend | Complexity | Cost | Best For |
|--------|----------|---------|------------|------|----------|
| **A: Recommended** | Vercel | Railway | Low | $5-20/mo | Production, ease of use |
| B: Vercel | Vercel | Render | Low | $7-25/mo | Alternative to Railway |
| C: Vercel | Vercel | Fly.io | Medium | $5-30/mo | Global edge deployment |
| D: Vercel Only | Vercel | Vercel (Mangum) | High | $0-20/mo | Serverless-only, limited |

**This guide covers Option A (Recommended).**

---

## Quick Start - Recommended Setup

### Prerequisites

- GitHub account (for Vercel/Railway integration)
- Vercel account (free tier available)
- Railway account (or Render/Fly.io)
- Domain name (optional, for custom domains)

### 5-Minute Overview

1. **Deploy Backend** (~3 min): Connect Railway repository → Deploy
2. **Deploy Frontend** (~2 min): Connect Vercel repository → Configure API URL → Deploy
3. **Configure DNS** (optional): Point custom domain to both services

---

## Step-by-Step Guide

## Part 1: Backend Deployment (Railway)

### Step 1.1: Create Railway Account

1. Go to [railway.app](https://railway.app/)
2. Sign up with GitHub
3. Verify email address

### Step 1.2: Create New Project

1. Click **"New Project"** → **"Deploy from GitHub repo"**
2. Select your TranslateFlow repository
3. Configure settings:

```yaml
Root Directory: .                     # Repository root
Build Command: (empty)                # Using Dockerfile
Start Command: (empty)                # Using Dockerfile
```

4. Click **"Deploy"**

### Step 1.3: Add PostgreSQL Database

1. In your Railway project, click **"New Service"** → **"Database"** → **"Add PostgreSQL"**
2. Railway will automatically:
   - Provision PostgreSQL database
   - Set `DATABASE_URL` environment variable
   - Connect to your backend service

### Step 1.4: Configure Environment Variables

Go to your backend service → **Variables** tab, add:

```bash
# Required
SECRET_KEY=your-generated-secret-key    # openssl rand -hex 32
ALLOWED_ORIGINS=https://your-frontend.vercel.app
RUNNING_IN_DOCKER=true

# Optional (for email, payments, OAuth)
EMAIL_PROVIDER=resend
RESEND_API_KEY=re_xxx
STRIPE_API_KEY=sk_test_xxx
# ... etc (see .env.backend.example)
```

### Step 1.5: Enable Health Checks

In your service settings:

```yaml
Healthcheck Path: /api/system/status
Healthcheck Interval: 30s
```

### Step 1.6: Deploy & Get Backend URL

1. Railway will redeploy automatically
2. Wait for deployment to complete (~2-3 minutes)
3. Copy your backend URL:
   ```
   https://translateflow-backend.up.railway.app
   ```

---

## Part 2: Frontend Deployment (Vercel)

### Step 2.1: Install Vercel CLI

```bash
npm install -g vercel
```

### Step 2.2: Login to Vercel

```bash
vercel login
```

### Step 2.3: Deploy Frontend

From the `Tools/WebServer/` directory:

```bash
cd Tools/WebServer
vercel
```

Follow prompts:
- **Set up and deploy?** Y
- **Which scope?** Your account
- **Link to existing project?** N
- **Project name:** translateflow-frontend
- **In which directory is your code?** . (current)
- **Override settings?** N (uses vercel.json)

### Step 2.4: Configure Environment Variables

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your project
3. Go to **Settings** → **Environment Variables**
4. Add:

```bash
VITE_API_URL=https://your-backend-url.railway.app
VITE_APP_NAME=TranslateFlow
```

5. Select environments: Production, Preview, Development

### Step 2.6: Redeploy with Environment Variables

```bash
vercel --env=production
```

Or push a commit to trigger redeployment.

### Step 2.7: Verify Deployment

1. Visit your Vercel URL:
   ```
   https://translateflow-frontend.vercel.app
   ```

2. Check browser console for API errors
3. Test login functionality
4. Create a test translation task

---

## Platform-Specific Instructions

### Railway (Recommended)

**Pros:**
- Simple GitHub integration
- Automatic DATABASE_URL
- Built-in PostgreSQL
- Generous free tier ($5 credit/month)

**Configuration:**
```yaml
Backend:
  - Service Type: Docker (Dockerfile.production)
  - Health Check: /api/system/status
  - Port: 8000 (auto-detected)

Database:
  - PostgreSQL (included)
  - Connection pooling: Auto
```

**Backend URL Format:**
```
https://<project-name>.up.railway.app
```

### Render

**Pros:**
- Free tier available
- Automatic SSL
- Easy PostgreSQL setup

**Configuration:**
```yaml
Backend:
  - Service Type: Web Service
  - Runtime: Docker
  - Health Check: /api/system/status
  - Region: Oregon (us-west)

Database:
  - PostgreSQL (separate service)
  - Connection: Internal URL
```

**Backend URL Format:**
```
https://<project-name>.onrender.com
```

### Fly.io

**Pros:**
- Global edge deployment
- Competitive pricing
- Fast cold starts

**Configuration:**
```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
flyctl auth login

# Launch app
flyctl launch --dockerfile Dockerfile.production

# Add PostgreSQL
flyctl postgres create

# Set secrets
flyctl secrets set SECRET_KEY=xxx
flyctl secrets set DATABASE_URL=xxx

# Deploy
flyctl deploy
```

**Backend URL Format:**
```
https://<app-name>.fly.dev
```

---

## Configuration & Environment Variables

### Frontend Variables (Vercel)

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `VITE_API_URL` | ✅ Yes | Backend API URL | `https://api.railway.app` |
| `VITE_APP_NAME` | No | Application display name | `TranslateFlow` |

**Security Note:** Variables prefixed with `VITE_` are exposed to the browser. Never put secrets here!

### Backend Variables (Container Platform)

See `.env.backend.example` for complete list. Required minimum:

```bash
# Database (Railway provides this automatically)
DATABASE_URL=postgresql://...

# Security
SECRET_KEY=<generate with openssl rand -hex 32>
ALLOWED_ORIGINS=https://your-frontend.vercel.app

# Docker
RUNNING_IN_DOCKER=true
```

---

## Custom Domains

### Frontend (Vercel)

1. Go to **Settings** → **Domains**
2. Click **Add Domain**
3. Enter your domain: `app.translateflow.com`
4. Configure DNS:
   ```
   CNAME app cname.vercel-dns.com
   ```
5. Vercel will automatically provision SSL certificate

### Backend (Railway)

1. Go to **Settings** → **Networking**
2. Click **Add Custom Domain**
3. Enter your domain: `api.translateflow.com`
4. Configure DNS:
   ```
   CNAME api up.railway.app
   ```
5. Railway will automatically provision SSL certificate

### Update CORS Configuration

Add your custom domains to backend `ALLOWED_ORIGINS`:

```bash
ALLOWED_ORIGINS=https://app.translateflow.com,https://translateflow-frontend.vercel.app
```

---

## Monitoring & Analytics

### Vercel Analytics (Frontend)

1. Install Vercel Analytics package:
   ```bash
   cd Tools/WebServer
   npm install @vercel/analytics
   ```

2. Add to `App.tsx`:
   ```tsx
   import { Analytics } from '@vercel/analytics/react';

   function App() {
     return (
       <>
         <YourApp />
         <Analytics />
       </>
     );
   }
   ```

3. View analytics in Vercel Dashboard → **Analytics**

### Railway Monitoring (Backend)

1. Go to your service → **Metrics** tab
2. View:
   - CPU usage
   - Memory usage
   - Network I/O
   - Restart count
3. Set up alerts: **Settings** → **Notifications**

### Error Tracking (Optional - Sentry)

```bash
# Frontend
npm install @sentry/react

# Backend (add to pyproject.toml dependencies)
sentry-sdk
```

---

## Troubleshooting

### Common Issues

#### 1. CORS Errors

**Symptom:** Browser console shows CORS policy errors

**Solution:**
```bash
# Check backend ALLOWED_ORIGINS includes your frontend URL
# On Railway: Variables tab → ALLOWED_ORIGINS
# Should include: https://your-frontend.vercel.app
```

#### 2. API Connection Refused

**Symptom:** Frontend can't reach backend API

**Solutions:**
- Verify `VITE_API_URL` is set correctly in Vercel
- Check backend health: `https://your-backend/api/system/status`
- Ensure backend service is running (not sleeping)
- Check Railway/Render logs for errors

#### 3. Environment Variables Not Working

**Symptom:** App behaves like variables aren't set

**Solutions:**
- Vercel: Redeploy after adding variables
- Railway: Variables apply on next deployment
- Check variable names match exactly (case-sensitive)
- Verify no extra spaces or quotes

#### 4. Build Failures

**Vercel Build Failures:**
```bash
# Check build logs in Vercel Dashboard
# Common issues:
# - Node version mismatch (package.json specifies >=18)
# - Missing dependencies (npm install failed)
```

**Railway Build Failures:**
```bash
# Check deployment logs in Railway
# Common issues:
# - Dockerfile syntax error
# - Missing .dockerignore file
# - Port mismatch (should be 8000)
```

#### 5. Database Connection Errors

**Symptom:** Backend can't connect to database

**Solutions:**
- Verify DATABASE_URL is set
- Check database service is running
- Ensure database and backend are in same region
- Check for connection pool exhaustion

### Debug Mode

Enable detailed logging:

```bash
# Backend (Railway Variables)
LOG_LEVEL=debug
DEBUG=true

# Frontend (Vercel Variables)
VITE_DEBUG=true
```

---

## Best Practices

### Security

1. **Never commit secrets** to Git
2. **Use environment variables** for all sensitive data
3. **Enable HTTPS** everywhere (automatic on Vercel/Railway)
4. **Rotate SECRET_KEY** periodically
5. **Limit ALLOWED_ORIGINS** to specific domains
6. **Enable rate limiting** on API endpoints
7. **Review audit logs** regularly

### Performance

1. **Enable Vercel Edge Network** for global distribution
2. **Use CDN caching** for static assets
3. **Optimize images** (WebP format, lazy loading)
4. **Minimize JavaScript bundle size**
5. **Enable gzip/brotli** compression
6. **Monitor memory usage** on backend

### Cost Optimization

1. **Use free tiers** during development
2. **Set up alerts** for billing thresholds
3. **Right-size resources** (CPU, RAM)
4. **Remove unused services**
5. **Optimize database queries**
6. **Enable caching** where possible

### Development Workflow

1. **Use Preview Deployments** for testing
2. **Test locally** before deploying
3. **Use feature flags** for gradual rollouts
4. **Automate deployments** via GitHub
5. **Monitor errors** in production
6. **Have rollback plan** ready

---

## Advanced Configuration

### Continuous Deployment

**Vercel:** Automatically deploys on git push to main branch

**Railway:** Automatically deploys on git push to configured branch

To configure:
1. Go to project settings
2. Select **GitHub** integration
3. Choose branch to watch (main/master)
4. Deploy automatically on push

### Preview Deployments

**Vercel:** Every PR gets a unique preview URL

**Railway:** Enable in Settings → Deployments → Preview Deployments

### Staging Environment

Create separate projects for staging:

```
translateflow-frontend-prod  → Vercel
translateflow-frontend-staging → Vercel
translateflow-backend-prod   → Railway
translateflow-backend-staging → Railway
```

### Database Backups

**Railway:**
- Automatic backups included
- Restore from Railway dashboard
- Export: `railway export`

**Render:**
- Automated backups available
- Backup frequency: Daily
- Retention: 7 days (free tier)

---

## Migration from Local Development

### 1. Export Local Database

```bash
# If using SQLite locally
sqlite3 ainiee.db .dump > backup.sql

# Import to Railway PostgreSQL
railway import --service postgresql backup.sql
```

### 2. Update Environment Variables

Copy from local `.env` to Railway/Vercel dashboards.

### 3. Update API Client Configuration

Frontend needs to use production API URL:

```typescript
// vite.config.ts - for development only
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',  // Development
      // Production uses VITE_API_URL
    }
  }
}
```

---

## Cost Estimates

### Production Usage (10k users/month)

| Service | Plan | Cost |
|---------|------|------|
| Vercel Frontend | Pro | $20/month |
| Railway Backend | Starter | $5/month |
| Railway PostgreSQL | Starter | $5/month |
| **Total** | | **~$30/month** |

### Development/Testing

| Service | Plan | Cost |
|---------|------|------|
| Vercel Frontend | Hobby | Free |
| Railway Backend | Free Tier | $5 credit/month |
| Railway PostgreSQL | Free Tier | Included |
| **Total** | | **Free** |

---

## Support & Resources

- **Vercel Docs:** https://vercel.com/docs
- **Railway Docs:** https://docs.railway.app
- **TranslateFlow Repo:** https://github.com/ShadowLoveElysia/TranslateFlow
- **Issues:** https://github.com/ShadowLoveElysia/TranslateFlow/issues

---

**Last Updated:** 2026-02-28
**Version:** 1.0.0
