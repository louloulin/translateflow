# TranslateFlow 用户管理与商业化功能实现进度

## 实现进度概览

| 模块 | 功能 | 进度 | 状态 |
|------|------|------|------|
| 认证系统 | 邮箱/密码注册登录 | 100% | ✅ 完成 |
| 认证系统 | JWT Token 认证 | 100% | ✅ 完成 |
| 认证系统 | 刷新Token机制 | 100% | ✅ 完成 |
| 认证系统 | 密码重置流程 | 100% | ✅ 完成 |
| 认证系统 | **邮箱验证流程** | 100% | ✅ 完成 |
| 认证系统 | **OAuth第三方登录** | 100% | ✅ 完成 |
| 用户管理 | 用户CRUD操作 | 100% | ✅ 完成 |
| 用户管理 | 用户资料管理 | 100% | ✅ 完成 |
| 用户管理 | **邮箱通知扩展** | 100% | ✅ 完成 |
| 用户管理 | **用户管理 API 路由** | 100% | ✅ 完成 |
| 订阅计费 | Stripe支付集成 | 50% | 🔄 部分完成 |
| 订阅计费 | 订阅计划管理 | 50% | 🔄 部分完成 |
| 订阅计费 | **Stripe Webhook 集成** | 100% | ✅ 完成 |
| 订阅计费 | **支付方式管理** | 100% | ✅ 完成 |
| 订阅计费 | **订阅生命周期管理** | 100% | ✅ 完成 |
| 订阅计费 | **发票邮件通知** | 100% | ✅ 完成 |
| 订阅计费 | 用量追踪系统 | 100% | ✅ 完成 |
| 订阅计费 | 配额执行中间件 | 100% | ✅ 完成 |
| 订阅计费 | 发票生成 | 50% | 🔄 部分完成 |

---

## 详细实现记录

### 阶段一：基础认证系统 ✅

#### 1.1 数据模型设计 ✅ (100%)
- [x] User 用户模型
- [x] Tenant 租户模型
- [x] ApiKey API密钥模型
- [x] LoginHistory 登录历史模型
- [x] PasswordReset 密码重置模型
- [x] EmailVerification 邮箱验证模型
- [x] RefreshToken 刷新令牌模型

#### 1.2 认证服务实现 ✅ (100%)
- [x] 用户注册 (register)
- [x] 用户登录 (login)
- [x] 用户登出 (logout)
- [x] Token刷新 (refresh_access_token)
- [x] 密码重置 (forgot_password, reset_password)

#### 1.3 邮箱验证流程 ✅ (100%) - 本次实现
- [x] 发送验证邮件 (send_verification_email)
- [x] 验证邮箱 (verify_email)
- [x] 重发验证邮件 (resend_verification_email)
- [x] 验证令牌校验 (verify_verification_token)
- [x] 注册时自动发送验证邮件

### 阶段二：用户管理系统 ✅

#### 2.1 用户服务 (100%)
- [x] 创建 User 服务目录
- [x] UserManager - 用户管理器
- [x] UserRepository - 数据访问层
- [x] 用户资料管理
- [x] 用户CRUD操作
- [x] 用户列表和搜索
- [x] 角色和状态管理
- [x] 登录历史查询
- [x] 偏好设置管理

#### 2.2 用户管理 API 路由 ✅ (100%) - 本次实现

在 `Tools/WebServer/web_server.py` 中实现了完整的用户管理 API 路由系统。

**请求/响应模型 (8个)**
- `UpdateProfileRequest` - 用户资料更新请求（用户名、全名、简介、头像）
- `UpdateEmailRequest` - 邮箱更新请求（新邮箱 + 密码验证）
- `UpdatePasswordRequest` - 密码更新请求（当前密码 + 新密码）
- `DeleteAccountRequest` - 账户删除请求（可选密码确认）
- `UpdateUserRoleRequest` - 角色更新请求（管理员）
- `UpdateUserStatusRequest` - 状态更新请求（管理员 + 可选原因）
- `UserListResponse` - 用户列表响应（包含分页信息）
- `LoginHistoryResponse` - 登录历史响应（包含分页信息）

**当前用户 API (8个路由)**

用户资料管理：
- `GET /api/v1/users/me` - 获取当前用户完整资料
- `PUT /api/v1/users/me` - 更新用户资料（支持部分字段更新）
- `PUT /api/v1/users/me/email` - 更新邮箱（需密码验证，自动发送验证邮件）
- `PUT /api/v1/users/me/password` - 更新密码（需当前密码验证，自动撤销刷新令牌）
- `DELETE /api/v1/users/me` - 删除账户（需密码确认，不可撤销）

偏好设置：
- `GET /api/v1/users/me/preferences` - 获取用户偏好设置
- `PUT /api/v1/users/me/preferences` - 更新用户偏好设置

登录历史：
- `GET /api/v1/users/me/login-history` - 获取登录历史（支持分页，包含 IP、User Agent、状态）

**管理员 API (4个路由)**

- `GET /api/v1/users` - 获取用户列表
  - 支持分页（page, per_page）
  - 支持搜索（search：在用户名和邮箱中搜索）
  - 支持过滤（role：按角色过滤，status：按状态过滤）
- `GET /api/v1/users/{user_id}` - 获取指定用户详情
- `PUT /api/v1/users/{user_id}/role` - 更新用户角色（支持 6 种角色）
- `PUT /api/v1/users/{user_id}/status` - 更新用户状态（active/inactive/suspended，支持原因说明）

**安全特性**
- JWT 认证：所有路由使用 `jwt_middleware.get_current_user` 获取当前用户
- 权限控制：管理员路由使用 `jwt_middleware.require_admin()` 中间件
- 密码验证：敏感操作（邮箱更改、密码更改、账户删除）需要密码验证
- 错误处理：适当的 HTTP 状态码和友好的错误消息
- 参数验证：使用 Pydantic 模型进行请求参数验证

**中文文档**
- 所有路由都包含详细的中文 docstring
- 文档说明功能、参数、返回值和注意事项

### 阶段三：订阅计费系统 🔄

#### 3.1 Stripe 支付集成 ✅ (90%)
- [x] PaymentProcessor - 基础支付处理
- [x] StripeWebhookHandler - Webhook 事件处理
- [x] 支付方式管理 (get/attach/detach/set_default)
- [x] 订阅生命周期管理 (create/cancel/update/get)
- [x] 发票管理 (get/list)
- [x] 邮件通知集成 (支付/订阅/发票)
- [ ] 完整 API 路由集成
- [ ] 前端支付界面

#### 3.2 用量追踪系统 ✅ (100%) - 本次实现
- [x] UsageTracker - 完整的用量追踪服务
- [x] record_usage - 记录使用事件
- [x] get_today_usage - 今日使用量查询
- [x] get_month_usage - 本月使用量查询
- [x] get_usage_history - 历史记录查询（分页、时间范围）
- [x] get_daily_usage_stats - 每日使用统计（趋势图）
- [x] get_usage_summary - 使用量汇总（今日/本月/总计）
- [x] get_top_users_by_usage - 使用量排名（管理员）
- [x] delete_old_records - 旧数据清理
- [x] 支持多种指标类型 (characters, api_calls, storage_mb, etc.)

#### 3.3 配额执行中间件 ✅ (100%) - 本次实现
- [x] QuotaEnforcer - 完整的配额执行器
- [x] check_before_operation - 操作前配额检查
- [x] record_and_check - 记录并返回配额状态
- [x] check_and_record - 检查并记录（原子操作）
- [x] is_quota_available - 简单配额检查
- [x] get_usage_percentage - 使用百分比计算
- [x] 配额缓存机制（减少数据库查询）
- [x] 详细错误消息和升级引导
- [x] QuotaExceededError - 完整的异常信息
- [x] require_quota 装饰器（FastAPI 集成）

#### 3.4 发票生成 (50%)
- [x] InvoiceGenerator - 基础结构
- [ ] PDF 生成功能

### 阶段四：高级功能 ✅

#### 4.1 OAuth登录 ✅ (100%) - 本次实现
- [x] OAuthManager - 第三方登录管理器
- [x] GitHub OAuth
- [x] Google OAuth
- [x] OAuthAccount 数据模型
- [x] 账户关联和解绑
- [x] 已登录账户列表查询

---

## 本次更新 (2026-02-27) - OAuth 第三方登录

### 实现内容：完整的 OAuth 第三方登录系统

实现了完整的 GitHub 和 Google OAuth 第三方登录功能，包括账户关联、解绑和管理。

#### 1. OAuthManager (`ModuleFolders/Service/Auth/oauth_manager.py`)

完整的 OAuth 管理器，支持 GitHub 和 Google 登录：

**OAuth 流程管理**
- `get_authorization_url()` - 生成 OAuth 授权 URL
- `exchange_code_for_token()` - 交换授权码获取访问令牌
- `get_user_info()` - 从 OAuth 提供商获取用户信息
- `oauth_login()` - 完整的 OAuth 登录流程

**账户管理**
- `link_oauth_account()` - 将 OAuth 账户关联到现有用户
- `unlink_oauth_account()` - 解除 OAuth 账户关联
- `get_linked_accounts()` - 获取用户的所有关联账户

**支持的提供商**
- GitHub OAuth (scope: user:email)
- Google OAuth (scope: userinfo.email, userinfo.profile)

#### 2. OAuthAccount 模型 (`ModuleFolders/Service/Auth/models.py`)

新增 OAuth 账户关联数据模型：

**字段说明**
- `provider` - OAuth 提供商 (github/google)
- `oauth_id` - 提供商的用户 ID
- `access_token` - OAuth 访问令牌
- `refresh_token` - OAuth 刷新令牌（可选）
- `token_expires_at` - 令牌过期时间
- `account_email` - OAuth 账户邮箱
- `account_username` - OAuth 账户用户名
- `account_data` - 完整账户数据（JSON）
- `linked_at` - 关联时间
- `last_login_at` - 最后登录时间

**唯一索引**
- (user_id, provider) - 每个用户每个提供商只能关联一次
- (provider, oauth_id) - 每个提供商的每个账户只能关联一次

#### 3. OAuth 登录流程

**新用户登录流程**:
1. 用户点击 GitHub/Google 登录按钮
2. 重定向到 OAuth 提供商授权页面
3. 用户授权后，重定向回应用并带上授权码
4. 系统使用授权码交换访问令牌
5. 获取用户信息（邮箱、用户名、头像）
6. 创建新用户账户（自动邮箱已验证）
7. 生成 JWT 令牌并返回

**已存在账户登录流程**:
1-5. 同新用户流程
6. 查找已存在的 OAuth 账户关联
7. 更新 OAuth 令牌和登录时间
8. 生成 JWT 令牌并返回

**账户关联功能**:
- 已登录用户可以关联其他 OAuth 提供商
- 支持同一提供商的不同账户
- 防止重复关联

#### 4. 环境变量配置

需要在 `.env` 文件中配置以下变量：

```bash
# GitHub OAuth
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# OAuth 回调 URL
OAUTH_REDIRECT_URI=http://localhost:8000/api/v1/auth/oauth/callback
```

#### 5. GitHub OAuth 应用设置

1. 访问 [GitHub Developer Settings](https://github.com/settings/developers)
2. 点击 "New OAuth App"
3. 配置：
   - Application name: TranslateFlow
   - Homepage URL: `http://localhost:8000`
   - Authorization callback URL: `http://localhost:8000/api/v1/auth/oauth/callback`
4. 获取 Client ID 和 Client Secret

#### 6. Google OAuth 应用设置

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目或选择现有项目
3. 启用 Google+ API
4. 配置 OAuth 同意屏幕
5. 创建 OAuth 2.0 客户端 ID：
   - 应用类型: Web 应用
   - 授权重定向 URI: `http://localhost:8000/api/v1/auth/oauth/callback`
6. 获取 Client ID 和 Client Secret

#### 7. API 使用示例

#### 获取授权 URL

```python
from ModuleFolders.Service.Auth import get_oauth_manager

oauth_manager = get_oauth_manager()

# 生成 GitHub 授权 URL
auth_url, state = oauth_manager.get_authorization_url("github")

# 保存 state 到 session，用于后续验证
# 重定向用户到 auth_url
```

#### 处理 OAuth 回调

```python
from ModuleFolders.Service.Auth import get_oauth_manager

oauth_manager = get_oauth_manager()

# 用户授权后，从回调参数获取 code 和 state
result = await oauth_manager.oauth_login(
    provider="github",
    code=code_from_callback,
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent"),
)

# 返回 JWT 令牌给用户
# {
#   "user": {...},
#   "access_token": "...",
#   "refresh_token": "...",
#   "provider": "github"
# }
```

#### 关联 OAuth 账户

```python
from ModuleFolders.Service.Auth import get_oauth_manager

oauth_manager = get_oauth_manager()

# 已登录用户关联 GitHub 账户
result = oauth_manager.link_oauth_account(
    user_id=current_user.id,
    provider="github",
    oauth_id="github_user_id",
    access_token="github_access_token",
    account_data={
        "email": "user@example.com",
        "username": "githubuser",
        "name": "GitHub User",
        "avatar_url": "https://..."
    },
)
```

#### 查询已关联账户

```python
from ModuleFolders.Service.Auth import get_oauth_manager

oauth_manager = get_oauth_manager()

# 获取用户所有已关联的 OAuth 账户
accounts = oauth_manager.get_linked_accounts(user_id=current_user.id)

# [
#   {
#     "provider": "github",
#     "account_email": "user@example.com",
#     "account_username": "githubuser",
#     "linked_at": "2026-02-27T...",
#     "last_login_at": "2026-02-27T..."
#   },
#   {
#     "provider": "google",
#     ...
#   }
# ]
```

#### 解除关联

```python
from ModuleFolders.Service.Auth import get_oauth_manager

oauth_manager = get_oauth_manager()

# 解除 GitHub 账户关联
result = oauth_manager.unlink_oauth_account(
    user_id=current_user.id,
    provider="github",
)
```

#### 8. 安全特性

**CSRF 保护**
- 使用 state 参数防止 CSRF 攻击
- 建议将 state 存储在 session 中进行验证

**令牌安全**
- OAuth 访问令牌安全存储在数据库
- 支持令牌过期时间
- 支持刷新令牌

**账户安全**
- OAuth 账户自动邮箱验证
- OAuth 用户可以设置密码（支持混合登录）
- 防止最后一个 OAuth 账户被解绑（需先设置密码）

#### 9. 数据库迁移

运行数据库初始化以创建 `oauth_accounts` 表：

```python
from ModuleFolders.Service.Auth import init_database

db = init_database()
```

或使用迁移脚本：

```sql
CREATE TABLE oauth_accounts (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    oauth_id VARCHAR(255) NOT NULL,
    access_token VARCHAR(500) NOT NULL,
    refresh_token VARCHAR(500),
    token_expires_at TIMESTAMP,
    account_email VARCHAR(255),
    account_username VARCHAR(255),
    account_data TEXT,
    linked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, provider),
    UNIQUE(provider, oauth_id)
);

CREATE INDEX idx_oauth_accounts_provider ON oauth_accounts(provider);
CREATE INDEX idx_oauth_accounts_oauth_id ON oauth_accounts(oauth_id);
```

#### 10. 依赖项

OAuth 功能需要以下依赖：
- `httpx` - 异步 HTTP 客户端（已在 pyproject.toml 中）
- `peewee` - ORM（已在 pyproject.toml 中）

无需额外安装依赖。

#### 11. 错误处理

OAuth 管理器会抛出 `OAuthError` 异常，包含以下错误情况：
- 不支持的 OAuth 提供商
- OAuth 令牌交换失败
- OAuth 用户信息获取失败
- 账户已存在或重复关联
- 尝试解绑最后一个 OAuth 账户

### 集成说明

OAuth 系统依赖以下模块：
- Auth models (ModuleFolders/Service/Auth/models.py)
- JWT Handler (ModuleFolders/Service/Auth/jwt_handler.py)
- Database (PostgreSQL/SQLite)

### 下一步

OAuth 系统已完成，可以：
1. 实现 API 路由（/api/v1/auth/oauth/github, /api/v1/auth/oauth/google）
2. 实现前端 OAuth 登录按钮
3. 实现用户账户管理界面（显示已关联账户，支持解绑）

---

## 总体进度

**整体完成度: 80%**

- 认证系统: 100% ✅ **完成**
- 用户管理: 100% ✅ **完成**
- 订阅计费: 85% (Stripe 集成完成，用量追踪和配额执行完成，缺 API 路由和前端)
- 高级功能: 20% (OAuth 完成，缺多租户和团队管理)

---

## 本次更新 (2026-02-27) - 用量追踪与配额执行系统

### 实现内容：完整的用量追踪与配额执行系统

实现了完整的用量追踪系统（UsageTracker）和配额执行中间件（QuotaEnforcer），支持多种指标类型、缓存优化和 FastAPI 集成。

#### 1. UsageTracker (`ModuleFolders/Service/Billing/UsageTracker.py`)

完整的用量追踪服务，提供以下功能：

**支持的指标类型**
- `characters` - 翻译字符数
- `api_calls` - API调用次数
- `storage_mb` - 存储使用(MB)
- `concurrent_tasks` - 并发任务数
- `team_members` - 团队成员数

**核心方法**
- `record_usage()` - 记录使用事件（支持元数据）
- `get_today_usage()` - 今日使用量查询
- `get_month_usage()` - 本月使用量查询

**高级分析**
- `get_usage_history()` - 历史记录查询（分页、时间范围过滤）
- `get_daily_usage_stats()` - 每日使用统计（用于趋势图，支持自定义天数）
- `get_usage_summary()` - 使用量汇总（今日/本月/总计，所有指标）

**管理功能**
- `get_top_users_by_usage()` - 使用量排名（管理员功能）
- `delete_old_records()` - 旧数据清理（数据保留策略）

#### 2. QuotaEnforcer (`ModuleFolders/Service/Billing/QuotaEnforcer.py`)

完整的配额执行中间件，提供以下功能：

**配额检查**
- `check_before_operation()` - 操作前配额检查（支持预估使用量）
- `is_quota_available()` - 简单配额可用性检查
- `get_usage_percentage()` - 配额使用百分比计算

**原子操作**
- `record_and_check()` - 记录使用量并返回更新后配额
- `check_and_record()` - 先检查后记录（原子操作，失败不记录）

**性能优化**
- 配额缓存机制（默认60秒TTL，减少数据库查询）
- 自动缓存失效（记录使用后立即使缓存失效）

**错误处理**
- `QuotaExceededError` - 完整的异常信息（包含限制、已用、剩余、升级链接）
- 详细的错误消息（中文，包含使用量和升级引导）

**FastAPI 集成**
- `require_quota` 装饰器 - 自动检查配额并记录使用量
- 支持自定义指标类型和使用量参数

#### 3. API 使用示例

**记录使用量**
```python
from ModuleFolders.Service.Billing import UsageTracker

tracker = UsageTracker()

# 记录翻译字符数
result = tracker.record_usage(
    user_id="user-123",
    metric_type="characters",
    quantity=1500,
    metadata={"task_id": "task-456", "source_lang": "en", "target_lang": "zh"},
)
```

**查询使用历史**
```python
# 获取最近30天的使用历史
history = tracker.get_usage_history(
    user_id="user-123",
    metric_type="characters",
    days=30,
    page=1,
    per_page=50,
)

# 返回格式：
# {
#     "records": [...],
#     "pagination": {
#         "page": 1,
#         "per_page": 50,
#         "total_count": 150,
#         "total_pages": 3,
#         "has_next": true,
#         "has_prev": false,
#     }
# }
```

**获取每日统计（趋势图）**
```python
# 获取最近30天的每日使用统计
daily_stats = tracker.get_daily_usage_stats(
    user_id="user-123",
    metric_type="characters",
    days=30,
)

# 返回格式：
# [
#     {"date": "2026-02-01", "quantity": 5000},
#     {"date": "2026-02-02", "quantity": 3200},
#     ...
# ]
```

**配额检查**
```python
from ModuleFolders.Service.Billing import QuotaEnforcer

enforcer = QuotaEnforcer()

# 检查配额
result = enforcer.check_before_operation(
    user_id="user-123",
    estimated_quantity=1000,
    metric_type="characters",
    raise_on_exceeded=True,  # 超额时抛出异常
)

# 返回格式：
# {
#     "allowed": true,
#     "remaining": 49000,
#     "limit": 50000,
#     "used": 1000,
#     "requested": 1000,
#     "exceeded": false,
# }
```

**使用装饰器（FastAPI 集成）**
```python
from ModuleFolders.Service.Billing import require_quota

@require_quota(metric_type="characters", quantity_param="char_count")
async def translate_text(user_id: str, char_count: int, text: str):
    # 配额检查通过后才会执行此函数
    # 执行完成后自动记录使用量
    result = await do_translation(text)
    return result
```

**处理配额超限**
```python
from ModuleFolders.Service.Billing import QuotaEnforcer, QuotaExceededError

enforcer = QuotaEnforcer()

try:
    enforcer.check_before_operation(
        user_id="user-123",
        estimated_quantity=10000,
        raise_on_exceeded=True,
    )
    # 执行操作...
except QuotaExceededError as e:
    # 返回友好的错误信息
    return {
        "error": e.to_dict(),
        # e.to_dict() 返回：
        # {
        #     "error": "quota_exceeded",
        #     "message": "您的翻译字符配额已用完...",
        #     "limit": 50000,
        #     "used": 50000,
        #     "remaining": 0,
        #     "upgrade_url": "/pricing",
        # }
    }
```

#### 4. 数据库要求

需要 `usage_records` 表来存储使用记录：

```sql
CREATE TABLE usage_records (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    quantity INTEGER NOT NULL,
    recorded_at TIMESTAMP NOT NULL,
    metadata TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_usage_records_user ON usage_records(user_id);
CREATE INDEX idx_usage_records_metric ON usage_records(metric_type);
CREATE INDEX idx_usage_records_date ON usage_records(date(recorded_at));
```

#### 5. 集成说明

用量追踪和配额执行系统依赖以下模块：
- SubscriptionManager (ModuleFolders/Service/Billing/SubscriptionManager.py)
- Database (ModuleFolders/Infrastructure/Database/pgsql.py)
- User/Tenant 模型 (ModuleFolders/Service/Auth/models.py)

### 实现内容：用户资料管理服务

创建了完整的 User 服务模块 `ModuleFolders/Service/User/`:

#### 1. UserManager (`user_manager.py`)

用户管理器提供以下功能：

**用户资料管理**
- `get_profile(user_id)` - 获取用户资料
- `update_profile(user_id, ...)` - 更新用户资料（用户名、全名、简介、头像）
- `update_email(user_id, new_email, password)` - 更新邮箱（需密码验证）
- `update_password(user_id, current_password, new_password)` - 更新密码
- `delete_account(user_id, password)` - 删除账户

**管理员功能**
- `list_users(page, per_page, search, role, status)` - 用户列表（支持搜索、过滤、分页）
- `update_user_role(admin_id, user_id, new_role)` - 更新用户角色
- `update_user_status(admin_id, user_id, new_status, reason)` - 更新用户状态

**其他功能**
- `get_login_history(user_id, page, per_page)` - 登录历史查询
- `update_preferences(user_id, preferences)` - 更新用户偏好
- `get_preferences(user_id)` - 获取用户偏好

**验证器**
- `validate_username()` - 用户名验证（3-20字符，字母数字下划线）
- `validate_full_name()` - 全名验证
- `validate_bio()` - 简介验证（最多500字符）
- `validate_avatar_url()` - 头像URL验证

#### 2. UserRepository (`user_repository.py`)

数据访问层提供：
- `find_by_id()` - 按ID查找
- `find_by_email()` - 按邮箱查找
- `find_by_username()` - 按用户名查找
- `find_many()` - 批量查询（支持过滤和分页）
- `count()` - 统计用户数量
- `create()` - 创建用户
- `update()` - 更新用户
- `delete()` - 删除用户

#### 3. 邮件通知扩展 (`ModuleFolders/Service/Email/`)

新增邮件模板和发送方法：
- `send_email_change_notification()` - 邮箱更改通知
- `send_password_change_notification()` - 密码更改通知
- `send_account_deletion_notification()` - 账户删除通知
- `send_role_change_notification()` - 角色更改通知
- `send_account_suspended_notification()` - 账户暂停通知
- `send_account_reactivated_notification()` - 账户重新激活通知

### 集成说明

User 服务依赖以下模块：
- Auth models (ModuleFolders/Service/Auth/models.py)
- Password Manager (ModuleFolders/Service/Auth/password_manager.py)
- Email Service (ModuleFolders/Service/Email/email_service.py)

---

## 本次更新 (2026-02-27) - 邮箱验证流程

### 实现内容：邮箱验证流程

在 `ModuleFolders/Service/Auth/auth_manager.py` 中添加了以下方法：

1. **`send_verification_email(user, verification_url_base)`**
   - 生成验证令牌（24小时有效）
   - 存储令牌到 EmailVerification 表
   - 发送验证邮件

2. **`verify_email(token)`**
   - 验证令牌有效性
   - 标记邮箱为已验证
   - 发送欢迎邮件

3. **`resend_verification_email(email, verification_url_base)`**
   - 重发验证邮件
   - 防止邮件枚举攻击
   - 检查是否已验证或已发送

4. **`verify_verification_token(token)`**
   - 仅验证令牌有效性，不执行验证操作

5. **更新 `register()` 方法**
   - 添加 `send_verification` 参数
   - 注册时自动发送验证邮件

### 集成说明

邮箱验证流程依赖以下服务：
- EmailService (ModuleFolders/Service/Email/)
- EmailVerification 模型 (ModuleFolders/Service/Auth/models.py)

---

## 本次更新 (2026-02-27) - Stripe 支付集成

### 实现内容：完整的 Stripe 支付集成

实现了完整的 Stripe 支付处理系统，包括 Webhook 处理、支付方式管理、订阅生命周期管理和邮件通知。

#### 1. StripeWebhookHandler (`ModuleFolders/Service/Billing/stripe_webhook.py`)

完整的 Stripe Webhook 事件处理器，支持：

**Webhook 签名验证**
- `verify_signature()` - 验证 Stripe 签名，防止伪造请求

**支付事件处理**
- `handle_payment_succeeded()` - 处理支付成功，记录到数据库，发送通知邮件
- `handle_payment_failed()` - 处理支付失败，记录错误信息，发送失败通知
- `handle_checkout_completed()` - 处理结账会话完成，关联用户和客户

**订阅事件处理**
- `handle_subscription_updated()` - 处理订阅更新（升降级），更新租户计划
- `handle_subscription_deleted()` - 处理订阅取消，降级为免费计划

**发票事件处理**
- `handle_invoice_paid()` - 处理发票支付成功，更新发票状态
- `handle_invoice_payment_failed()` - 处理发票支付失败，记录重试次数

**辅助方法**
- `_find_user_by_customer_id()` - 根据 Stripe 客户 ID 查找用户
- `_map_price_to_plan()` - 将 Stripe Price ID 映射到订阅计划

#### 2. PaymentProcessor 增强 (`ModuleFolders/Service/Billing/PaymentProcessor.py`)

新增完整的 Stripe API 集成方法：

**支付方式管理**
- `get_payment_methods(customer_id)` - 获取客户的所有支付方式
- `attach_payment_method()` - 将支付方式附加到客户
- `detach_payment_method()` - 分离支付方式
- `set_default_payment_method()` - 设置默认支付方式

**订阅管理**
- `create_subscription()` - 创建订阅（支持试用）
- `cancel_subscription()` - 取消订阅（立即或周期结束）
- `update_subscription()` - 更新订阅计划（升降级）
- `get_subscription()` - 获取订阅详情

**发票管理**
- `get_invoice()` - 获取发票详情（含 PDF 下载链接）
- `list_invoices()` - 获取客户的发票列表

#### 3. 邮件通知扩展 (`ModuleFolders/Service/Email/`)

**新增邮件模板** (`templates.py`)
- `get_payment_notification_template()` - 支付成功/失败通知模板
- `get_subscription_notification_template()` - 订阅更新/取消通知模板
- `get_invoice_notification_template()` - 发票支付/失败通知模板

**新增发送方法** (`email_service.py`)
- `send_payment_notification()` - 发送支付通知
- `send_subscription_notification()` - 发送订阅通知
- `send_invoice_notification()` - 发送发票通知

### 支持的 Stripe 事件

| 事件类型 | 处理方法 | 功能 |
|----------|----------|------|
| `payment_intent.succeeded` | `_handle_payment_succeeded` | 支付成功处理 |
| `payment_intent.payment_failed` | `_handle_payment_failed` | 支付失败处理 |
| `customer.subscription.updated` | `_handle_subscription_updated` | 订阅更新处理 |
| `customer.subscription.deleted` | `_handle_subscription_deleted` | 订阅取消处理 |
| `invoice.payment_failed` | `_handle_invoice_payment_failed` | 发票支付失败处理 |
| `invoice.paid` | `_handle_invoice_paid` | 发票已支付处理 |
| `checkout.session.completed` | `_handle_checkout_completed` | 结账完成处理 |

### 需要的数据库表

为支持 Stripe 集成，需要创建以下数据库表：

```sql
-- 支付记录表
CREATE TABLE payments (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    stripe_payment_id VARCHAR(255) NOT NULL,
    amount DECIMAL(10, 2),
    currency VARCHAR(3),
    status VARCHAR(50),
    error_message TEXT,
    created_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 订阅事件记录表
CREATE TABLE subscription_events (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    subscription_id VARCHAR(255) NOT NULL,
    event_type VARCHAR(50),
    plan VARCHAR(50),
    status VARCHAR(50),
    created_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 结账会话记录表
CREATE TABLE checkout_sessions (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    stripe_session_id VARCHAR(255) NOT NULL,
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    status VARCHAR(50),
    created_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 环境变量配置

需要在 `.env` 文件中配置以下变量：

```bash
# Stripe API 配置
STRIPE_API_KEY=sk_test_...              # Stripe API 密钥
STRIPE_WEBHOOK_SECRET=whsec_...         # Webhook 签名密钥

# Stripe Price IDs
STRIPE_PRICE_STARTER=price_...          # 入门计划 Price ID
STRIPE_PRICE_PRO=price_...              # 专业计划 Price ID
STRIPE_PRICE_ENTERPRISE=price_...       # 企业计划 Price ID
```

### 依赖安装

```bash
pip install stripe
```

### API 使用示例

#### 创建结账会话

```python
from ModuleFolders.Service.Billing import PaymentProcessor

processor = PaymentProcessor()

# 创建结账会话
session = processor.create_checkout_session(
    user_id="user-123",
    plan=SubscriptionPlan.PRO,
    success_url="https://example.com/success",
    cancel_url="https://example.com/cancel",
)

# 重定向用户到 session['url'] 进行支付
```

#### 处理 Webhook

```python
from ModuleFolders.Service.Billing import StripeWebhookHandler

handler = StripeWebhookHandler()

# 验证签名
if handler.verify_signature(payload, signature):
    # 解析事件
    event_data = json.loads(payload)
    # 处理事件
    result = handler.handle_event(event_data)
```

### 集成说明

Stripe 集成依赖以下模块：
- Stripe Python SDK (`stripe` 包)
- EmailService (ModuleFolders/Service/Email/)
- User/Tenant 模型 (ModuleFolders/Service/Auth/models.py)
- 数据库 (PostgreSQL/SQLite)

---

## 本次更新 (2026-02-27) - 用户管理 API 路由

### 实现内容：完整的用户管理 API 路由系统

在 `Tools/WebServer/web_server.py` 中实现了 12 个用户管理 API 路由，包括当前用户操作和管理员功能。

#### 1. 当前用户 API (8个路由)

**用户资料管理**
- `GET /api/v1/users/me` - 获取当前用户资料
  - 返回完整用户信息（邮箱、用户名、角色、状态、全名、简介、头像等）
  - 包含邮箱验证状态和最后登录时间

- `PUT /api/v1/users/me` - 更新用户资料
  - 支持部分字段更新（用户名、全名、简介、头像）
  - 自动验证用户名唯一性
  - 字段长度验证（简介最多 500 字符）

- `PUT /api/v1/users/me/email` - 更新邮箱
  - 需要密码验证
  - 新邮箱必须唯一
  - 自动发送验证邮件到新邮箱
  - 发送通知到旧邮箱

- `PUT /api/v1/users/me/password` - 更新密码
  - 需要当前密码验证
  - 自动撤销所有刷新令牌（强制重新登录）
  - 发送密码更改通知邮件

- `DELETE /api/v1/users/me` - 删除账户
  - 需要密码确认（如果用户有密码）
  - 此操作不可撤销
  - 发送账户删除通知邮件

**偏好设置**
- `GET /api/v1/users/me/preferences` - 获取用户偏好
  - 返回用户的自定义设置

- `PUT /api/v1/users/me/preferences` - 更新用户偏好
  - 允许存储任意 JSON 格式的用户设置

**登录历史**
- `GET /api/v1/users/me/login-history` - 获取登录历史
  - 支持分页（page, per_page）
  - 包含 IP 地址、User Agent、成功/失败状态、时间戳

#### 2. 管理员 API (4个路由)

- `GET /api/v1/users` - 获取用户列表
  - 支持分页（page, per_page，默认 1页20条）
  - 支持搜索（在用户名和邮箱中搜索）
  - 支持按角色过滤（super_admin, tenant_admin, team_admin, translation_admin, developer, user）
  - 支持按状态过滤（active, inactive, suspended）

- `GET /api/v1/users/{user_id}` - 获取用户详情
  - 返回指定用户的完整信息

- `PUT /api/v1/users/{user_id}/role` - 更新用户角色
  - 支持 6 种角色（super_admin, tenant_admin, team_admin, translation_admin, developer, user）
  - 发送角色更改通知邮件

- `PUT /api/v1/users/{user_id}/status` - 更新用户状态
  - 支持 3 种状态（active, inactive, suspended）
  - 可选原因字段用于审计
  - 发送状态更改通知邮件

#### 3. 安全特性

**认证和授权**
- 所有路由使用 JWT 认证（`jwt_middleware.get_current_user`）
- 管理员路由使用权限中间件（`jwt_middleware.require_admin()`）
- OAuth 用户可以设置密码以支持密码登录

**密码安全**
- 敏感操作需要密码验证（邮箱更改、密码更改、账户删除）
- 密码更改后自动撤销所有刷新令牌
- OAuth 用户如果未设置密码，删除账户时不需要密码确认

**错误处理**
- 适当的 HTTP 状态码（200, 400, 404, 500）
- 友好的中文错误消息
- 参数验证失败时返回详细错误信息

#### 4. API 使用示例

**获取当前用户资料**
```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**更新用户资料**
```bash
curl -X PUT "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"full_name": "张三", "bio": "这是我的简介"}'
```

**更新密码**
```bash
curl -X PUT "http://localhost:8000/api/v1/users/me/password" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"current_password": "oldpassword", "new_password": "newpassword123"}'
```

**管理员获取用户列表**
```bash
curl -X GET "http://localhost:8000/api/v1/users?page=1&per_page=20&search=zhang&role=user&status=active" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

**管理员更新用户角色**
```bash
curl -X PUT "http://localhost:8000/api/v1/users/user-123/role" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"new_role": "developer"}'
```

#### 5. 依赖模块

用户管理 API 路由依赖以下模块：
- UserManager (`ModuleFolders/Service/User/user_manager.py`)
- UserRepository (`ModuleFolders/Service/User/user_repository.py`)
- JWT Middleware (`ModuleFolders/Service/Auth/auth_middleware.py`)
- Email Service (`ModuleFolders/Service/Email/email_service.py`)
- User Model (`ModuleFolders/Service/Auth/models.py`)

#### 6. 测试验证

- ✅ Python 语法检查通过
- ✅ FastAPI 应用加载成功
- ✅ 12 个用户管理路由注册成功
- ✅ 所有路由使用正确的 HTTP 方法
- ✅ 请求/响应模型定义完整

### 集成说明

用户管理 API 已完全集成到 WebServer，可以通过 FastAPI 自动生成的文档访问：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 下一步

用户管理 API 已完成，可以：
1. 实现订阅管理 API 路由
2. 实现用量管理 API 路由
3. 实现前端用户管理界面

---

## 下一步计划

1. ✅ ~~实现 OAuth 第三方登录~~ (已完成)
2. ✅ ~~完善用量追踪和配额验证逻辑~~ (已完成)
3. ✅ ~~实现用户管理 API 路由~~ (已完成)
4. 完善订阅管理 API 路由（FastAPI endpoints）
5. 实现用量管理 API 路由（FastAPI endpoints）
6. 实现 OAuth API 路由（FastAPI endpoints）
7. 实现发票 PDF 生成功能
5. 前端页面开发（支付界面、订阅管理、用量统计）
