/Users/louloulin/Documents/linchong/ai/AiNiee-Next/.ralph/agent/memories.md
## Patterns

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
