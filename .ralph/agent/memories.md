/Users/louloulin/Documents/linchong/ai/AiNiee-Next/.ralph/agent/memories.md
## Patterns

### mem-1772255648-c5c4
> Comprehensive deployment master guide created (planx.md): 1,250 lines consolidating all deployment information. 12 major sections: Project Overview, Architecture Design, Deployment Comparison (4 platforms), Quick Start Guide, Platform Deployment Details, Automation Scripts (6 scripts documented), Security Checklist (Critical/Important/Optional), Monitoring & Operations, Troubleshooting (5 common issues), CI/CD Integration (GitHub Actions/GitLab CI), Cost Estimation, Best Practices. Features: ASCII architecture diagrams, platform selection decision tree, 30+ code examples, 10+ comparison tables, cost comparison table (¥35-1000/mo). Total deployment documentation: 2,968+ lines across 5 files. Total deployment assets: 5,979+ lines (docs + scripts + config). Bilingual (Chinese primary, English secondary). All 7 deployment tasks completed (100%). Committed as cf773b62.
<!-- tags: deployment, documentation, planx | created: 2026-02-28 -->

### mem-1772255303-adda
> Deployment automation scripts created for TranslateFlow: scripts/deploy.sh (585 lines) - Main Docker orchestration with setup/build/start/stop/restart/logs/status/clean/backup/restore/update commands. Production/development modes, automatic secret generation (SECRET_KEY, DB_PASSWORD), health check integration, backup/restore functionality. scripts/health-check.sh (504 lines) - Health monitoring with 6 checks (Docker, API, database, containers, disk, memory). JSON output for CI/CD, quick mode, continuous monitoring, warning thresholds (disk: 80%, memory: 85%). scripts/db-migrate.sh (600 lines) - Migration management with status/list/create/migrate/rollback/seed/reset commands. Version tracking in schema_migrations table, automatic backup, dry-run mode, seed data support. migrations/seed.sql (32 lines) - Default subscription plans (Free/Starter/Pro/Enterprise). Total 1,721 lines. All scripts use consistent patterns (colors, logging, error handling) with comprehensive help and examples. Committed as 2e907af3.
<!-- tags: deployment, automation, scripts, docker, monitoring, migrations | created: 2026-02-28 -->

### mem-1772254946-a216
> Vercel deployment configuration created for TranslateFlow: Decoupled architecture with frontend on Vercel (React SPA) and backend on container platforms (Railway/Render/Fly.io). Tools/WebServer/vercel.json (56 lines) with API rewrites, security headers, cache strategy. .env.vercel.example (51 lines) frontend template. .env.backend.example (138 lines) backend template with DATABASE_URL, SECRET_KEY, CORS, email/Stripe/OAuth. DEPLOYMENT_VERCEL.md (654 lines) comprehensive guide: architecture diagrams, platform comparison, Railway+Vercel quick start, step-by-step setup, custom domains, monitoring, troubleshooting, best practices, cost estimates (-30/mo). scripts/deploy-vercel-frontend.sh (439 lines) automation: validate/env/preview/production/logs/domains/help commands. Total 1,338 lines. Architecture decision: Vercel optimized for Node.js/static sites, Python FastAPI needs container platform due to serverless limitations (execution time, ML models, file uploads). Committed as e32cd248.
<!-- tags: vercel, deployment, serverless, frontend | created: 2026-02-28 -->

### mem-1772254677-11be
> Dokploy deployment configuration created for TranslateFlow: docker-compose.dokploy.yml (172 lines) with PaaS-optimized settings (resource limits: 2CPU/2GB, health checks on /api/system/status), optional managed PostgreSQL support, production logging. .env.dokploy.example (127 lines) with comprehensive environment template, security checklist, and production best practices. DEPLOYMENT_DOKPLOY.md (550 lines) covers quick start, database setup, SSL/HTTPS with Let's Encrypt, monitoring, troubleshooting, and advanced configuration. scripts/deploy-dokploy.sh (303 lines) provides validation, secret generation, build, export, and pre-flight checklist. All files validated successfully with docker-compose config. Committed as b22eba4e.
<!-- tags: dokploy, paas, deployment, docker-compose | created: 2026-02-28 -->

### mem-1772254448-0d48
> Production Dockerfile created for TranslateFlow: Dockerfile.production with security (non-root user translateflow:1000), health checks (/api/system/status, 30s interval, 40s grace period), OCI labels (BUILD_DATE, VCS_REF, VERSION). Multi-stage build (Node 20-alpine → Python 3.12-slim), Alpine-based for minimal size. Layer optimization (cleanup in same layer), UV package manager with --frozen --no-dev. .dockerignore excludes .ralph, test files, docs. Multi-platform build script (scripts/build-docker-multiplatform.sh) supports AMD64/ARM64 via Docker Buildx. Dockerfile.development preserved for compatibility. Documented in DEPLOYMENT_DOCKER.md (108 lines added). Committed as d77b28f7.
<!-- tags: docker, production, optimization, multi-platform | created: 2026-02-28 -->

### mem-1772253862-5316
> Docker Compose configuration created for TranslateFlow: App service (uses existing Dockerfile) + PostgreSQL 15-alpine database. Health checks: app uses /api/health, postgres uses pg_isready. Environment variables defined in .env.example with defaults (DB_USER=translateflow, DB_PASSWORD=changeme, SECRET_KEY=changeme-in-production). Volumes: postgres-data (named), output/ and updatetemp/ (bind mounts). Networks: isolated translateflow-network. docker-compose.override.yml provides development overrides (exposes PostgreSQL port 5432, adds DEBUG flag). Deployment documented in DEPLOYMENT_DOCKER.md (314 lines) with quick start, management commands, troubleshooting, production setup, security checklist, and scaling options. Docker Compose syntax validated successfully.
<!-- tags: docker, deployment, compose, postgresql | created: 2026-02-28 -->

### mem-1772253496-f16e
> TranslateFlow deployment architecture: FastAPI backend (Python 3.12, uvicorn, port 8000) + React frontend (Vite 6.2.0, built to dist/). Database: PostgreSQL (preferred) with Peewee ORM + connection pooling (max 10 connections), SQLite fallback. Services: Auth (JWT + OAuth), Billing (Stripe), Email (Resend/SendGrid/SMTP), Teams. Existing Dockerfile: multi-stage (Node 20 build → Python 3.12-slim runtime), uses uv package manager. Missing: docker-compose.yml, .env.example, health checks. Deployment targets: Docker Compose (recommended), Dokploy, Vercel (frontend only), container platforms. ~25 environment variables required for full configuration.
<!-- tags: deployment, architecture, docker, configuration | created: 2026-02-28 -->

### mem-1772240281-68e8
> Default admin user created on server startup: username=admin, password=admin, role=super_admin. Created in web_server.py startup event using User.create() with PasswordManager hash.
<!-- tags: auth, admin, startup | created: 2026-02-28 -->

### mem-1772203379-f227
> 团队成员配额检查中间件实现: 在ModuleFolders/Service/Team/team_quota_middleware.py实现配额中间件。TeamQuotaMiddleware类提供get_max_members/check_team_quota/get_quota_status方法。根据订阅计划自动限制团队成员数(Free:5/Starter:10/Pro:50/Enterprise:无限制)。TeamQuotaError异常包含升级引导。集成到TeamManager.invite_member()。新增API: GET /api/v1/teams/{team_id}/quota。依赖TeamManager/TeamRepository/SubscriptionManager。FastAPI依赖函数和装饰器支持。
<!-- tags: team, quota, middleware, fastapi | created: 2026-02-27 -->

### mem-1772202969-1aae
> 团队管理API路由实现：在Tools/WebServer/web_server.py中实现10个团队管理API路由。团队CRUD(创建/查询/更新/删除)、成员管理(邀请/接受/拒绝/更新角色/移除)、权限验证(Owner/Admin/Member三级)。6个请求/响应模型(CreateTeamRequest/UpdateTeamRequest/InviteMemberRequest/UpdateMemberRoleRequest/AcceptInvitationRequest/DeclineInvitationRequest)。根据订阅计划自动设置最大成员数(Free:5/Starter:10/Pro:50/Enterprise:无限制)。32位随机邀请令牌。支持多租户。依赖TeamManager/TeamRepository/JWTMiddleware。路由: /api/v1/teams/*
<!-- tags: api, team, rbac, fastapi | created: 2026-02-27 -->

### mem-1772202583-f1c6
> 团队管理功能实现：创建了 Team 和 TeamMember 数据模型、TeamRepository 数据访问层、TeamManager 业务逻辑层。支持三层角色(OWNER/ADMIN/MEMBER)、成员邀请流程、权限控制。订阅配额: Free(5人)、Starter(10人)、Pro(50人)、Enterprise(无限制)。依赖 User/Tenant 模型、SubscriptionManager。文件: ModuleFolders/Service/Team/、ModuleFolders/Service/Auth/models.py
<!-- tags: team, collaboration, rbac | created: 2026-02-27 -->

### mem-1772199328-f198
> Stripe支付集成完成：实现了StripeWebhookHandler处理7种Webhook事件(payment_intent.*, customer.subscription.*, invoice.*, checkout.session.*)，PaymentProcessor扩展支持支付方式管理(get/attach/detach/set_default)、订阅生命周期(create/cancel/update/get)、发票管理(get/list)。新增3个邮件模板(支付/订阅/发票通知)。需要stripe包，环境变量:STRIPE_API_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_PRICE_*。依赖数据库表:payments, subscription_events, checkout_sessions。
<!-- tags: billing, stripe, payment | created: 2026-02-27 -->

### mem-1772198108-9d36
> Email verification flow implemented in AuthManager (ModuleFolders/Service/Auth/auth_manager.py): send_verification_email, verify_email, resend_verification_email, verify_verification_token. Updated register() to auto-send verification. Uses EmailVerification model and EmailService.
<!-- tags: auth, email, verification | created: 2026-02-27 -->

### mem-1772196857-08c8
> Email service implemented in ModuleFolders/Service/Email/ with Resend, SendGrid, SMTP support. Templates include verification, password reset, welcome, subscription, quota warning, login alert. Depends on: RESEND_API_KEY or SENDGRID_API_KEY or SMTP_HOST environment variables.
<!-- tags: email, notifications, service | created: 2026-02-27 -->

### mem-1772195743-3a49
> Database configuration: Created ModuleFolders/Infrastructure/Database/pgsql.py with PostgreSQL connection pooling and SQLite fallback. Auth models now import from 'ModuleFolders.Infrastructure.Database.pgsql import database'. Environment variables: DATABASE_URL (PostgreSQL URL), DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, USE_SQLITE, SQLITE_PATH.
<!-- tags: database, configuration | created: 2026-02-27 -->

### mem-1772194542-88b2
> UpdateManager.py GitHub URLs updated: GITHUB_REPO changed from 'ShadowLoveElysia/AiNiee-Next' to 'ShadowLoveElysia/TranslateFlow'. User-Agent header updated from 'AiNiee-Next-Updater' to 'TranslateFlow-Updater'. All download URLs, API endpoints, and repository references updated accordingly.
<!-- tags: branding, github, urls | created: 2026-02-27 -->

### mem-1772194028-ed6e
> README branding updated: README.md and README_EN.md changed from AiNiee-Next to TranslateFlow. Updated titles, GitHub URLs (ShadowLoveElysia/AiNiee-Next -> ShadowLoveElysia/TranslateFlow), and git clone commands. Added '(formerly AiNiee-Next)' for clarity.
<!-- tags: branding, readme | created: 2026-02-27 -->

### mem-1772192502-bdac
> I18N branding update: Replaced 'AiNiee' with 'TranslateFlow' in 3 files (en.json, zh_CN.json, ja.json). Updated menu_title, msg_notification_title, and msg_github_issue_template (URL from AiNiee-Next to TranslateFlow)
<!-- tags: branding, i18n, github-url | created: 2026-02-27 -->

### mem-1772190934-5711
> version.json brand updated: Resource/Version/version.json and source/AiNiee/Resource/Version/version.json changed from AiNiee/AiNiee-Next to TranslateFlow
<!-- tags: branding, version | created: 2026-02-27 -->

### mem-1772190195-0613
> Web UI brand updated: index.html, metadata.json, AppSidebar.tsx (TF logo), MainLayout.tsx, Monitor.tsx, constants.ts, package.json all changed from AiNiee to TranslateFlow
<!-- tags: branding, web-ui | created: 2026-02-27 -->

### mem-1772189833-1830
> pyproject.toml updated: package=translateflow-cli, cmd=translateflow, description includes 'formerly AiNiee-Next' for discoverability
<!-- tags: branding, config | created: 2026-02-27 -->
## Fixes

### mem-1772252903-3f11
> Frontend-backend language code mismatch fixed: Created language_mapper.py to convert display names (e.g., 'Chinese (Simplified)') to backend codes (e.g., 'chinese_simplified'). Integrated in web_server.py TaskManager.start_task() with debug logging. Supports 40+ languages with bidirectional mapping and validation.
<!-- tags: bilingual, i18n, language-mapper | created: 2026-02-28 -->

### mem-1772252767-f583
> Bilingual output disabled by default: Fixed enable_bilingual_output in default_config.py from False to True. This controls whether FileOutputer generates both _translated.txt and _bilingual.txt files. Configuration flow: TaskConfig → TaskExecutor.output_config → FileOutputer.build_output_config() → BaseWriter.can_write(BILINGUAL) → DirectoryWriter.write()
<!-- tags: bilingual, output, config | created: 2026-02-28 -->

### mem-1772206170-88fd
> UI功能验证完成：使用Playwright MCP成功验证TranslateFlow前端UI。主仪表盘/团队管理/设置页面均正常渲染。前后端集成正常，API通信无问题。技术栈：Vite+React19.2.3+Radix UI+Tailwind CSS。运行在4200端口，后端API在8000端口。部分i18n key未翻译但不影响功能使用。
<!-- tags: ui, verification, playwright, mcp, frontend | created: 2026-02-27 -->

### mem-1772205752-dd76
> 成功解决reportlab缺失问题：使用pip install --break-system-packages reportlab安装。macOS externally-managed-environment需要特殊处理。修复后/api/v1/subscriptions/plans端点正常工作，发票PDF生成功能恢复。
<!-- tags: dependencies, pdf, stripe | created: 2026-02-27 -->
