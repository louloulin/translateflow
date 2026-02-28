# TranslateFlow Dokploy Deployment Guide

This guide covers deploying TranslateFlow to Dokploy, a self-hosted PaaS platform similar to Heroku/Vercel.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Detailed Setup](#detailed-setup)
4. [Configuration](#configuration)
5. [Database Setup](#database-setup)
6. [SSL/HTTPS](#sslhttps)
7. [Monitoring & Logging](#monitoring--logging)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

---

## Prerequisites

### System Requirements

- **Dokploy Server**: Self-hosted Dokploy instance (v0.3.0+)
- **Domain**: A domain name pointing to your Dokploy server
- **Resources**:
  - CPU: 2 cores minimum (4 cores recommended)
  - RAM: 2GB minimum (4GB recommended)
  - Storage: 10GB minimum for application + database

### Local Requirements

- Git
- Docker (for local testing)
- SSH access to Dokploy server (optional)

---

## Quick Start

### 1. Deploy Using Dokploy UI

1. **Create Application** in Dokploy:
   - Go to Dokploy Dashboard → Create Application
   - Name: `translateflow`
   - Type: **Docker Compose**
   - Repository: Your TranslateFlow repository URL

2. **Upload docker-compose.dokploy.yml**:
   ```bash
   # In Dokploy UI, paste the contents of:
   docker-compose.dokploy.yml
   ```

3. **Configure Environment Variables**:
   - Copy `.env.dokploy.example` to Dokploy's environment configuration
   - Generate secure values for all secrets (see Configuration section)

4. **Deploy**:
   - Click "Deploy" in Dokploy UI
   - Wait for deployment to complete (~5-10 minutes)

5. **Configure Domain**:
   - Add your domain in Dokploy (e.g., `translateflow.yourdomain.com`)
   - Enable SSL/HTTPS

6. **Access TranslateFlow**:
   - Open `https://translateflow.yourdomain.com` in your browser
   - Default credentials: `admin` / `admin` (⚠️ change immediately!)

---

## Detailed Setup

### Option A: Using Dokploy Managed PostgreSQL (Recommended)

This is the recommended approach for production deployments.

#### Step 1: Create PostgreSQL Service

1. In Dokploy Dashboard → Services → Create Service
2. Select **PostgreSQL**
3. Configure:
   - Name: `translateflow-db`
   - Version: `15`
   - Database: `translateflow`
   - Username: `translateflow`
   - Password: (generate strong password)
4. Save and note the connection details

#### Step 2: Create Application

1. Create new application in Dokploy
2. Type: **Docker Compose**
3. Upload `docker-compose.dokploy.yml` (PostgreSQL service commented out)
4. Configure environment variables:

```bash
# Database (from Step 1)
DATABASE_URL=postgresql://translateflow:<password>@translateflow-db:5432/translateflow

# Application
SECRET_KEY=<generate-secure-key>
HOST=0.0.0.0
PORT=8000

# Email (configure your provider)
EMAIL_PROVIDER=resend
RESEND_API_KEY=<your-key>

# Stripe (optional)
STRIPE_API_KEY=<your-key>
STRIPE_WEBHOOK_SECRET=<your-secret>
```

#### Step 3: Deploy and Configure

1. Click **Deploy**
2. Add domain: `translateflow.yourdomain.com`
3. Enable SSL (Let's Encrypt)
4. Update OAuth redirect URIs if using OAuth

---

### Option B: Using Included PostgreSQL

For smaller deployments or testing.

#### Step 1: Modify docker-compose.dokploy.yml

Uncomment the `postgres` service in `docker-compose.dokploy.yml`:

```yaml
  postgres:
    image: postgres:15-alpine
    container_name: translateflow-postgres
    # ... (rest of configuration)
```

#### Step 2: Configure and Deploy

Same as Option A, but use individual DB parameters instead of DATABASE_URL:

```bash
DB_HOST=postgres
DB_PORT=5432
DB_NAME=translateflow
DB_USER=translateflow
DB_PASSWORD=<strong-password>
```

---

## Configuration

### Generate Secure Secrets

#### SECRET_KEY

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### Database Password

```bash
openssl rand -base64 32
```

### Required Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DATABASE_URL` | Yes* | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `SECRET_KEY` | Yes | JWT encryption key | (32+ char random string) |
| `EMAIL_PROVIDER` | No | Email service | `resend`, `sendgrid`, `smtp` |
| `STRIPE_API_KEY` | No | Stripe API key | `sk_live_...` |

*Required unless using individual DB_* variables

### Optional Configuration

#### Email Providers

**Resend (Recommended)**:
```bash
EMAIL_PROVIDER=resend
RESEND_API_KEY=re_...
```

**SendGrid**:
```bash
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=SG....
```

**SMTP**:
```bash
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=user@example.com
SMTP_PASSWORD=<password>
```

#### OAuth Authentication

**GitHub**:
```bash
GITHUB_CLIENT_ID=<client-id>
GITHUB_CLIENT_SECRET=<client-secret>
OAUTH_REDIRECT_URI=https://translateflow.yourdomain.com/auth/callback
```

**Google**:
```bash
GOOGLE_CLIENT_ID=<client-id>
GOOGLE_CLIENT_SECRET=<client-secret>
OAUTH_REDIRECT_URI=https://translateflow.yourdomain.com/auth/callback
```

---

## Database Setup

### Initial Migration

TranslateFlow automatically creates tables on first startup. No manual migration needed.

### Backup Strategy

#### Using Dokploy Backups

1. Go to Service → Backups
2. Enable automatic backups
3. Configure schedule (recommended: daily)
4. Set retention period (recommended: 7 days)

#### Manual Backup

```bash
# SSH into Dokploy server
docker exec translateflow-postgres pg_dump -U translateflow translateflow > backup_$(date +%Y%m%d).sql
```

### Database Scaling

For high-traffic deployments:

1. Use Dokploy's managed PostgreSQL with connection pooling
2. Configure connection pool size:
   ```bash
   DB_POOL_SIZE=20
   DB_MAX_OVERFLOW=10
   ```

---

## SSL/HTTPS

### Enable Let's Encrypt SSL

1. In Dokploy → Application → Domains
2. Add domain: `translateflow.yourdomain.com`
3. Check "Enable SSL"
4. Select "Let's Encrypt"
5. Click "Save"

Dokploy will automatically:
- Provision SSL certificate
- Configure HTTPS redirect
- Set up automatic renewal

### Force HTTPS

Add to environment variables:
```bash
FORCE_HTTPS=true
```

---

## Monitoring & Logging

### View Logs in Dokploy

1. Application → Logs
2. Real-time log streaming
3. Download logs for analysis

### Log Configuration

Logs are automatically rotated (10MB, 3 files) via docker-compose.dokploy.yml

### Health Monitoring

TranslateFlow exposes health endpoint:
```
GET https://translateflow.yourdomain.com/api/system/status
```

Configure in Dokploy:
1. Application → Health Checks
2. Endpoint: `/api/system/status`
3. Interval: 30s
4. Timeout: 10s

### Resource Monitoring

Monitor in Dokploy Dashboard:
- CPU usage
- Memory usage
- Network I/O
- Disk usage

Set alerts for:
- CPU > 80% for 5 minutes
- Memory > 90% for 5 minutes
- Disk > 85%

---

## Troubleshooting

### Common Issues

#### 1. Application Won't Start

**Symptoms**: Container keeps restarting

**Solutions**:
```bash
# Check logs
docker logs translateflow-app

# Common causes:
# - Missing required environment variables
# - Database connection failure
# - Invalid SECRET_KEY
```

#### 2. Database Connection Failed

**Symptoms**: `psql: could not connect to server`

**Solutions**:
```bash
# Verify database is running
docker ps | grep postgres

# Check connection string
echo $DATABASE_URL

# Test connection
docker exec translateflow-app curl http://postgres:5432
```

#### 3. SSL Certificate Issues

**Symptoms**: Browser shows "Not Secure"

**Solutions**:
- Verify DNS is pointing to Dokploy server
- Check Let's Encrypt rate limits
- Ensure port 80/443 are accessible

#### 4. Email Not Sending

**Symptoms**: No emails being sent

**Solutions**:
```bash
# Verify email provider configuration
echo $EMAIL_PROVIDER
echo $RESEND_API_KEY

# Check logs for errors
docker logs translateflow-app | grep -i email
```

### Debug Mode

Enable debug logging temporarily:

```bash
# In Dokploy environment variables
DEBUG=true
LOG_LEVEL=DEBUG
```

⚠️ **Disable in production!**

### Performance Issues

**Slow Response Times**:

1. Check resource usage in Dokploy
2. Increase resource limits:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '4'
         memory: 4G
   ```
3. Enable database connection pooling
4. Add caching layer (Redis)

---

## Best Practices

### Security

1. **Change Default Credentials**:
   ```bash
   # First login: admin/admin
   # Immediately change password!
   ```

2. **Use Strong Secrets**:
   - SECRET_KEY: 32+ random characters
   - DB_PASSWORD: Strong password
   - API keys: Keep secure and rotate

3. **Enable SSL**:
   - Always use HTTPS in production
   - Configure HSTS headers

4. **Network Isolation**:
   - Use Dokploy's network isolation
   - Don't expose database ports externally

5. **Regular Updates**:
   - Update TranslateFlow regularly
   - Update Dokploy server
   - Apply security patches

### Performance

1. **Resource Allocation**:
   - Start with 2 CPU, 2GB RAM
   - Monitor and adjust as needed

2. **Database Optimization**:
   - Use managed PostgreSQL
   - Enable connection pooling
   - Regular backups

3. **Caching** (Advanced):
   - Add Redis for session caching
   - Configure CDN for static assets

### Reliability

1. **Health Checks**:
   - Configure in Dokploy
   - Set up alerting

2. **Backups**:
   - Daily automated backups
   - Test restore procedure
   - Off-site backup storage

3. **Monitoring**:
   - Resource monitoring
   - Log aggregation
   - Uptime monitoring

4. **Disaster Recovery**:
   - Document recovery procedure
   - Regular backup testing
   - Multiple restore points

---

## Advanced Configuration

### Custom Domain with Subdirectory

Deploy to subdirectory (e.g., `yourdomain.com/translateflow`):

1. Configure reverse proxy in Dokploy
2. Set environment variable:
   ```bash
   BASE_PATH=/translateflow
   ```

### Multiple Environments

Deploy staging and production:

1. **Staging**:
   - Application: `translateflow-staging`
   - Database: `translateflow-staging-db`
   - Domain: `staging.translateflow.yourdomain.com`

2. **Production**:
   - Application: `translateflow`
   - Database: `translateflow-db`
   - Domain: `translateflow.yourdomain.com`

### Horizontal Scaling

For high availability:

1. Use Dokploy's load balancer
2. Deploy multiple app instances
3. Use external PostgreSQL (managed service)
4. Configure session storage (Redis)

---

## Support

### Getting Help

1. **Dokploy Documentation**: https://docs.dokploy.com
2. **TranslateFlow Issues**: https://github.com/ShadowLoveElysia/TranslateFlow/issues
3. **Community Support**: Check README.md for support channels

### Reporting Issues

When reporting issues, include:

1. Dokploy version
2. TranslateFlow version
3. Browser console logs
4. Application logs (from Dokploy)
5. Environment configuration (sanitized)

---

## Next Steps

After successful deployment:

1. ✅ Change default admin password
2. ✅ Configure email notifications
3. ✅ Set up billing (if using Stripe)
4. ✅ Configure OAuth providers (optional)
5. ✅ Invite team members
6. ✅ Set up monitoring and alerts
7. ✅ Configure automated backups
8. ✅ Review security settings

---

**Deployment Guide Version**: 1.0
**Last Updated**: 2026-02-28
**Compatible with**: TranslateFlow v1.0+, Dokploy v0.3.0+
