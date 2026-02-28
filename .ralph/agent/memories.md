/Users/louloulin/Documents/linchong/ai/AiNiee-Next/.ralph/agent/memories.md
## Patterns

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

### mem-1772206170-88fd
> UI功能验证完成：使用Playwright MCP成功验证TranslateFlow前端UI。主仪表盘/团队管理/设置页面均正常渲染。前后端集成正常，API通信无问题。技术栈：Vite+React19.2.3+Radix UI+Tailwind CSS。运行在4200端口，后端API在8000端口。部分i18n key未翻译但不影响功能使用。
<!-- tags: ui, verification, playwright, mcp, frontend | created: 2026-02-27 -->

### mem-1772205752-dd76
> 成功解决reportlab缺失问题：使用pip install --break-system-packages reportlab安装。macOS externally-managed-environment需要特殊处理。修复后/api/v1/subscriptions/plans端点正常工作，发票PDF生成功能恢复。
<!-- tags: dependencies, pdf, stripe | created: 2026-02-27 -->
