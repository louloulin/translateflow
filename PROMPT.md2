# AiNiee 用户管理与商业化功能计划

## 一、项目现状分析

### 1.1 代码库结构
- **主项目**: AiNiee-Next (AI翻译工具)
- **技术栈**:
  - 后端: Python 3.12, FastAPI
  - 前端: React + TypeScript + Vite
  - 支持: 18+ LLM平台, 25+ 文件格式
- **现有模块**:
  - ModuleFolders (核心业务逻辑)
  - Tools/WebServer (Web服务)
  - 无现有用户管理/认证系统

### 1.2 关键发现
- ❌ 无用户认证系统
- ❌ 无订阅/计费系统
- ❌ 无多租户支持
- ❌ 无API密钥管理（仅有LLM API配置）
- ✅ 有完善的LLM请求和任务执行系统

---

## 二、用户管理系统设计

### 2.1 核心功能模块

#### 2.1.1 认证系统 (Authentication)
```
功能需求:
├── 邮箱/密码注册登录
├── 第三方OAuth登录 (GitHub, Google)
├── JWT Token 认证
├── 刷新Token机制
├── 密码重置流程
└── 邮箱验证
```

#### 2.1.2 用户管理 (User Management)
```
功能需求:
├── 用户CRUD操作
├── 用户资料管理
├── 头像上传
├── 登录历史记录
├── 账户状态管理 (启用/禁用)
└── 用户搜索和列表
```

#### 2.1.3 角色权限系统 (RBAC)
```
角色层级:
├── 超级管理员 (Super Admin)
│   └── 平台全部管理权限
├── 租户管理员 (Tenant Admin)
│   └── 本租户全部管理权限
├── 团队管理员 (Team Admin)
│   └── 团队管理, 成员管理
├── 翻译管理员 (Translation Admin)
│   └── 翻译任务, 术语表, 规则
├── 开发者 (Developer)
│   └── API密钥, Webhook配置
└── 普通用户 (User)
    └── 基本翻译功能
```

### 2.2 数据模型设计

#### 2.2.1 核心表结构
```sql
-- 用户表
users (
  id: UUID PRIMARY KEY
  email: VARCHAR(255) UNIQUE NOT NULL
  username: VARCHAR(100) UNIQUE NOT NULL
  password_hash: VARCHAR(255)
  avatar_url: VARCHAR(500)
  role: ENUM('super_admin', 'tenant_admin', 'team_admin', 'translation_admin', 'developer', 'user')
  tenant_id: UUID (多租户支持)
  status: ENUM('active', 'inactive', 'suspended')
  email_verified: BOOLEAN DEFAULT FALSE
  created_at: TIMESTAMP
  updated_at: TIMESTAMP
  last_login_at: TIMESTAMP
)

-- 租户表 (多租户支持)
tenants (
  id: UUID PRIMARY KEY
  name: VARCHAR(255) NOT NULL
  plan: ENUM('free', 'starter', 'pro', 'enterprise')
  status: ENUM('active', 'suspended')
  settings: JSONB
  created_at: TIMESTAMP
)

-- API密钥表
api_keys (
  id: UUID PRIMARY KEY
  user_id: UUID FOREIGN KEY
  key_hash: VARCHAR(255) NOT NULL
  name: VARCHAR(100)
  permissions: JSONB
  rate_limit: INTEGER (每分钟请求数)
  last_used_at: TIMESTAMP
  expires_at: TIMESTAMP
  created_at: TIMESTAMP
)

-- 登录历史
login_history (
  id: UUID PRIMARY KEY
  user_id: UUID FOREIGN KEY
  ip_address: VARCHAR(45)
  user_agent: VARCHAR(500)
  success: BOOLEAN
  created_at: TIMESTAMP
)
```

---

## 三、商业化订阅系统设计

### 3.1 订阅计划设计

| 计划 | 价格 | 功能限制 |
|------|------|----------|
| **Free** | ¥0/月 | 1000字/天, 基础格式, 无API |
| **Starter** | ¥29/月 | 5万字/天, 全部格式, 1用户 |
| **Pro** | ¥99/月 | 50万字/天, 高级功能, 5用户 |
| **Enterprise** | 定制 | 无限量, 专属客服, SSO |

### 3.2 计费模式

#### 3.2.1 混合计费模型
```
计费组成:
├── 订阅费 (固定月费)
├── 超额用量费 (超出配额按量计费)
└── 增值服务费 (额外功能单独计费)
```

#### 3.2.2 用量追踪
```python
# 计量维度
usage_metrics = {
    "daily_characters": 0,      # 每日字符数
    "monthly_characters": 0,    # 月度字符数
    "api_calls": 0,             # API调用次数
    "storage_mb": 0,            # 存储使用(MB)
    "team_members": 0,          # 团队成员数
    "concurrent_tasks": 0       # 并发任务数
}
```

### 3.3 支付集成

#### 3.3.1 Stripe 集成方案
```python
# 核心支付功能
payment_features = {
    "subscription_management": [
        "订阅创建/更新/取消",
        "订阅计划升降级",
        "自动续费",
        "计费周期管理"
    ],
    "invoicing": [
        "自动生成发票",
        "PDF发票下载",
        "账单邮件发送",
        "历史账单查询"
    ],
    "payment_methods": [
        "信用卡/借记卡",
        "支付宝",
        "微信支付",
        "企业银行转账"
    ],
    "webhooks": [
        "payment_succeeded",
        "payment_failed",
        "subscription_updated",
        "invoice_payment_failed"
    ]
}
```

---

## 四、技术架构设计

### 4.1 系统架构
```
┌─────────────────────────────────────────────────────────┐
│                    前端 (React + TS)                     │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐  │
│  │ 登录页  │ │ 控制台  │ │ 用户管理 │ │ 订阅管理   │  │
│  └────┬────┘ └────┬────┘ └────┬────┘ └──────┬──────┘  │
└───────┼────────────┼───────────┼─────────────┼──────────┘
        │            │           │             │
        ▼            ▼           ▼             ▼
┌─────────────────────────────────────────────────────────┐
│                 API Gateway (FastAPI)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │
│  │ Auth API │ │ User API │ │Billing API│ │Task API  │  │
│  └─────┬────┘ └────┬─────┘ └─────┬────┘ └─────┬─────┘  │
└────────┼───────────┼─────────────┼────────────┼────────┘
         │           │             │            │
         ▼           ▼             ▼            ▼
┌──────────────────────────────────────────────────────────┐
│                   服务层 (Microservices)                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │
│  │Auth Service│ │User Service│ │Billing Service│ │Translation│  │
│  └─────┬────┘ └────┬─────┘ └─────┬────┘ └─────┬─────┘  │
└────────┼───────────┼─────────────┼──────────────┼────────┘
         │           │             │              │
         ▼           ▼             ▼              ▼
┌──────────────────────────────────────────────────────────┐
│                      数据层                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │
│  │PostgreSQL│ │  Redis   │ │ S3/MinIO │ │  Stripe  │  │
│  │(用户/订阅)│ │(缓存/会话)│ │ (文件存储)│ │ (支付)   │  │
│  └──────────┘ └──────────┘ └──────────┘ └───────────┘  │
└──────────────────────────────────────────────────────────┘
```

### 4.2 核心模块划分

#### 4.2.1 认证服务 (Auth Service)
```
模块: ModuleFolders/Service/Auth/
├── AuthManager.py          # 认证管理器
├── JWTHandler.py           # JWT处理
├── OAuthManager.py         # 第三方登录
├── PasswordManager.py      # 密码管理
├── TokenRefresh.py        # Token刷新
└── LoginHistory.py        # 登录历史
```

#### 4.2.2 用户服务 (User Service)
```
模块: ModuleFolders/Service/User/
├── UserManager.py          # 用户管理
├── UserProfile.py          # 用户资料
├── UserRepository.py      # 数据访问
└── UserValidator.py       # 数据验证
```

#### 4.2.3 租户服务 (Tenant Service)
```
模块: ModuleFolders/Service/Tenant/
├── TenantManager.py       # 租户管理
├── TenantContext.py       # 租户上下文
├── TenantRepository.py    # 数据访问
└── TenantSettings.py     # 租户设置
```

#### 4.2.4 计费服务 (Billing Service)
```
模块: ModuleFolders/Service/Billing/
├── SubscriptionManager.py # 订阅管理
├── UsageTracker.py        # 用量追踪
├── PaymentProcessor.py    # 支付处理
├── InvoiceGenerator.py    # 发票生成
├── StripeWebhook.py       # Stripe Webhook
└── QuotaEnforcer.py      # 配额执行
```

---

## 五、实施计划

### 阶段一：基础用户系统 (第1-2周)

| 任务 | 描述 | 预计工时 |
|------|------|----------|
| T1.1 | 数据库设计和迁移 | 8h |
| T1.2 | 用户注册/登录API | 16h |
| T1.3 | JWT认证中间件 | 8h |
| T1.4 | 密码重置流程 | 8h |
| T1.5 | 用户资料管理API | 8h |
| T1.6 | 前端登录/注册页面 | 16h |
| T1.7 | 前端用户设置页面 | 12h |
| **小计** | | **76h** |

### 阶段二：RBAC权限系统 (第3周)

| 任务 | 描述 | 预计工时 |
|------|------|----------|
| T2.1 | 角色和权限数据模型 | 8h |
| T2.2 | 权限验证中间件 | 12h |
| T2.3 | 管理员用户管理界面 | 16h |
| T2.4 | 角色分配功能 | 8h |
| T2.5 | API密钥管理 | 12h |
| **小计** | | **56h** |

### 阶段三：订阅计费系统 (第4-5周)

| 任务 | 描述 | 预计工时 |
|------|------|----------|
| T3.1 | Stripe集成 | 16h |
| T3.2 | 订阅计划管理 | 12h |
| T3.3 | 用量追踪系统 | 16h |
| T3.4 | 配额执行器 | 12h |
| T3.5 | 发票生成 | 8h |
| T3.6 | 前端订阅管理页面 | 16h |
| T3.7 | 支付页面集成 | 12h |
| **小计** | | **92h** |

### 阶段四：高级功能 (第6周)

| 任务 | 描述 | 预计工时 |
|------|------|----------|
| T4.1 | OAuth第三方登录 | 12h |
| T4.2 | 多租户支持 | 16h |
| T4.3 | 团队管理功能 | 12h |
| T4.4 | SSO企业登录 (SAML/OIDC) | 16h |
| T4.5 | Webhook通知 | 8h |
| **小计** | | **64h** |

---

## 六、API 设计

### 6.1 认证 API
```
POST   /api/v1/auth/register          # 用户注册
POST   /api/v1/auth/login            # 用户登录
POST   /api/v1/auth/logout           # 用户登出
POST   /api/v1/auth/refresh          # 刷新Token
POST   /api/v1/auth/forgot-password  # 忘记密码
POST   /api/v1/auth/reset-password   # 重置密码
GET    /api/v1/auth/verify-email    # 验证邮箱
POST   /api/v1/auth/oauth/{provider} # OAuth登录
```

### 6.2 用户 API
```
GET    /api/v1/users/me               # 获取当前用户
PUT    /api/v1/users/me               # 更新当前用户
DELETE /api/v1/users/me               # 删除账户
GET    /api/v1/users                  # 用户列表 (管理员)
GET    /api/v1/users/{id}             # 获取用户详情
PUT    /api/v1/users/{id}             # 更新用户
DELETE /api/v1/users/{id}            # 删除用户
```

### 6.3 订阅 API
```
GET    /api/v1/subscriptions/plans    # 获取订阅计划
POST   /api/v1/subscriptions          # 创建订阅
GET    /api/v1/subscriptions/current  # 当前订阅
PUT    /api/v1/subscriptions/current  # 更新订阅
DELETE /api/v1/subscriptions/current  # 取消订阅
GET    /api/v1/subscriptions/invoices # 发票列表
GET    /api/v1/subscriptions/invoices/{id}/pdf # 下载发票
```

### 6.4 用量 API
```
GET    /api/v1/usage/current         # 当前用量
GET    /api/v1/usage/history        # 用量历史
GET    /api/v1/usage/daily          # 每日用量
```

---

## 七、安全考虑

### 7.1 认证安全
- 密码使用 bcrypt 加密存储
- JWT Token 短期有效 (15分钟), 刷新Token长期有效 (7天)
- 登录失败锁定 (5次失败后锁定15分钟)
- 敏感操作需要二次验证

### 7.2 数据安全
- HTTPS 全站加密
- API 密钥仅显示一次
- 敏感日志脱敏
- 数据库加密存储

### 7.3 审计日志
- 记录所有管理操作
- 记录登录历史
- 记录API调用
- 保留180天日志

---

## 八、第三方服务推荐

| 服务 | 用途 | 成本 |
|------|------|------|
| **Stripe** | 支付处理 | 1.4%+¥0 |
| **Supabase** | 认证+数据库 | $0-25/月 |
| **Resend** | 邮件发送 | $0-49/月 |
| **Sentry** | 错误追踪 | $0-199/月 |

---

## 九、总结

本计划为 AiNiee 翻译工具设计了完整的用户管理和商业化系统，包括:

1. **用户认证**: 邮箱登录、OAuth、 JWT
2. **权限管理**: 6级角色体系、细粒度权限
3. **订阅计费**: 4档订阅计划、混合计费模式
4. **支付集成**: Stripe全栈集成
5. **实施周期**: 约6周 (288小时)

---

## 参考资料

- [Azure AI Translator 安全准则](https://learn.microsoft.com/zh-cn/azure/ai-services/translator/secure-deployment)
- [Stripe Billing 文档](https://docs.stripe.com/billing)
- [SaaS 订阅计费模型设计](https://blog.csdn.net/sinat_28461591/article/details/148176807)
- [13.7亿级用户订阅系统架构](https://blog.csdn.net/yonggeit/article/details/148540794)
- [企业级SaaS权限设计](https://m.sohu.com/a/201677293_99913305/)
