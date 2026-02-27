# OAuth 第三方登录实现文档

## 概述

TranslateFlow 支持 GitHub 和 Google OAuth 第三方登录，用户可以使用现有的 GitHub 或 Google 账户快速登录系统。

## 功能特性

- ✅ 支持 GitHub OAuth 登录
- ✅ 支持 Google OAuth 登录
- ✅ 自动邮箱验证（OAuth 用户邮箱预验证）
- ✅ 账户关联功能（可关联多个 OAuth 提供商）
- ✅ 账户解绑功能
- ✅ 查询已关联账户
- ✅ 安全的令牌管理
- ✅ 完整的登录历史记录

## 快速开始

### 1. 环境配置

在 `.env` 文件中添加以下配置：

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

### 2. GitHub OAuth 应用设置

1. 访问 [GitHub Developer Settings](https://github.com/settings/developers)
2. 点击 "New OAuth App"
3. 填写应用信息：
   - **Application name**: TranslateFlow
   - **Homepage URL**: `http://localhost:8000`
   - **Authorization callback URL**: `http://localhost:8000/api/v1/auth/oauth/callback`
4. 点击 "Register application"
5. 复制 **Client ID** 和 **Client Secret** 到 `.env` 文件

### 3. Google OAuth 应用设置

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目或选择现有项目
3. 在左侧菜单选择 "APIs & Services" → "Library"
4. 搜索并启用 "Google+ API"
5. 配置 OAuth 同意屏幕：
   - 选择 "External" 用户类型
   - 填写应用名称、Logo 等信息
   - 添加授权范围（email, profile）
6. 创建 OAuth 2.0 凭据：
   - 选择 "Web application"
   - 名称：TranslateFlow
   - 授权重定向 URI：`http://localhost:8000/api/v1/auth/oauth/callback`
7. 复制 **Client ID** 和 **Client Secret** 到 `.env` 文件

## 使用方法

### 基本登录流程

#### 步骤 1: 生成授权 URL

```python
from ModuleFolders.Service.Auth import get_oauth_manager

oauth_manager = get_oauth_manager()

# 生成 GitHub 授权 URL
auth_url, state = oauth_manager.get_authorization_url("github")

# 保存 state 到 session（用于 CSRF 保护）
session["oauth_state"] = state
session["oauth_provider"] = "github"

# 重定向用户到 auth_url
return Redirect(auth_url)
```

#### 步骤 2: 处理 OAuth 回调

```python
from ModuleFolders.Service.Auth import get_oauth_manager
from fastapi import Request

oauth_manager = get_oauth_manager()

@router.get("/api/v1/auth/oauth/callback")
async def oauth_callback(
    request: Request,
    code: str,
    state: str
):
    # 验证 state 防止 CSRF 攻击
    if state != session.get("oauth_state"):
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    provider = session.get("oauth_provider")

    try:
        # 完成 OAuth 登录
        result = await oauth_manager.oauth_login(
            provider=provider,
            code=code,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
        )

        # 清除 session
        del session["oauth_state"]
        del session["oauth_provider"]

        # 返回 JWT 令牌
        return {
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "token_type": result["token_type"],
            "user": result["user"]
        }

    except OAuthError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### 账户关联功能

已登录用户可以关联额外的 OAuth 账户：

```python
from ModuleFolders.Service.Auth import get_oauth_manager

oauth_manager = get_oauth_manager()

@router.post("/api/v1/users/me/oauth/link")
async def link_oauth_account(
    provider: str,
    code: str,
    current_user: User = Depends(get_current_user)
):
    try:
        # 交换授权码获取令牌
        token_data = await oauth_manager.exchange_code_for_token(provider, code)

        # 获取用户信息
        user_info = await oauth_manager.get_user_info(
            provider,
            token_data["access_token"]
        )

        # 关联账户
        result = oauth_manager.link_oauth_account(
            user_id=str(current_user.id),
            provider=provider,
            oauth_id=user_info["oauth_id"],
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            account_data=user_info,
        )

        return result

    except OAuthError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### 查询已关联账户

```python
from ModuleFolders.Service.Auth import get_oauth_manager

oauth_manager = get_oauth_manager()

@router.get("/api/v1/users/me/oauth/accounts")
async def get_linked_accounts(
    current_user: User = Depends(get_current_user)
):
    accounts = oauth_manager.get_linked_accounts(str(current_user.id))
    return {"accounts": accounts}
```

### 解除账户关联

```python
from ModuleFolders.Service.Auth import get_oauth_manager

oauth_manager = get_oauth_manager()

@router.delete("/api/v1/users/me/oauth/{provider}")
async def unlink_oauth_account(
    provider: str,
    current_user: User = Depends(get_current_user)
):
    try:
        result = oauth_manager.unlink_oauth_account(
            user_id=str(current_user.id),
            provider=provider,
        )
        return result

    except OAuthError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

## 数据模型

### OAuthAccount 模型

```python
class OAuthAccount(Model):
    """OAuth 账户关联模型"""

    id: UUID              # 主键
    user: User            # 关联用户（外键）
    provider: str         # 提供商（github/google）
    oauth_id: str         # 提供商用户 ID
    access_token: str     # OAuth 访问令牌
    refresh_token: str    # OAuth 刷新令牌（可选）
    token_expires_at: datetime  # 令牌过期时间
    account_email: str    # OAuth 账户邮箱
    account_username: str # OAuth 账户用户名
    account_data: str     # 完整账户数据（JSON）
    linked_at: datetime   # 关联时间
    last_login_at: datetime  # 最后登录时间
```

### 数据库表结构

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

## API 参考

### OAuthManager

#### `get_authorization_url(provider, state=None, redirect_uri=None)`

生成 OAuth 授权 URL。

**参数**:
- `provider` (str): OAuth 提供商 ("github" 或 "google")
- `state` (str, optional): CSRF 令牌，如未提供会自动生成
- `redirect_uri` (str, optional): 自定义重定向 URI

**返回**:
- `tuple`: (authorization_url, state)

**示例**:
```python
url, state = oauth_manager.get_authorization_url("github")
```

---

#### `exchange_code_for_token(provider, code, redirect_uri=None)`

交换授权码获取访问令牌。

**参数**:
- `provider` (str): OAuth 提供商
- `code` (str): 授权码
- `redirect_uri` (str, optional): 自定义重定向 URI

**返回**:
- `dict`: 包含 access_token 和可选的 refresh_token

**示例**:
```python
tokens = await oauth_manager.exchange_code_for_token("github", code)
access_token = tokens["access_token"]
```

---

#### `get_user_info(provider, access_token)`

从 OAuth 提供商获取用户信息。

**参数**:
- `provider` (str): OAuth 提供商
- `access_token` (str): OAuth 访问令牌

**返回**:
- `dict`: 用户信息（oauth_id, email, username, name, avatar_url）

**示例**:
```python
user_info = await oauth_manager.get_user_info("github", token)
```

---

#### `oauth_login(provider, code, redirect_uri=None, ip_address=None, user_agent=None)`

完整的 OAuth 登录流程。

**参数**:
- `provider` (str): OAuth 提供商
- `code` (str): 授权码
- `redirect_uri` (str, optional): 自定义重定向 URI
- `ip_address` (str, optional): 客户端 IP 地址
- `user_agent` (str, optional): 客户端 User-Agent

**返回**:
- `dict`: 用户数据和 JWT 令牌

**示例**:
```python
result = await oauth_manager.oauth_login(
    "github",
    code,
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0..."
)
```

---

#### `link_oauth_account(user_id, provider, oauth_id, access_token, ...)`

将 OAuth 账户关联到现有用户。

**参数**:
- `user_id` (str): 用户 ID
- `provider` (str): OAuth 提供商
- `oauth_id` (str): OAuth 用户 ID
- `access_token` (str): OAuth 访问令牌
- `refresh_token` (str, optional): OAuth 刷新令牌
- `account_data` (dict, optional): 额外账户数据

**返回**:
- `dict`: 关联结果

---

#### `unlink_oauth_account(user_id, provider)`

解除 OAuth 账户关联。

**参数**:
- `user_id` (str): 用户 ID
- `provider` (str): OAuth 提供商

**返回**:
- `dict`: 解绑结果

---

#### `get_linked_accounts(user_id)`

获取用户的所有关联账户。

**参数**:
- `user_id` (str): 用户 ID

**返回**:
- `list`: 关联账户列表

## 安全考虑

### CSRF 保护

OAuth 流程使用 `state` 参数防止 CSRF 攻击：

```python
# 生成 state 并保存到 session
state = secrets.token_urlsafe(32)
session["oauth_state"] = state

# 回调时验证
if request.state != session["oauth_state"]:
    raise HTTPException(status_code=400, detail="Invalid state")
```

### 令牌安全

- OAuth 访问令牌安全存储在数据库中
- 支持令牌过期时间
- 支持刷新令牌
- 使用加密连接（HTTPS）传输敏感数据

### 账户安全

- OAuth 用户自动邮箱验证
- 防止最后一个 OAuth 账户被解绑（需先设置密码）
- 支持混合登录（OAuth + 密码）
- 完整的登录历史记录

## 错误处理

OAuth 管理器可能抛出以下错误：

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| `OAuthError: Unsupported OAuth provider` | 提供商不支持 | 使用 "github" 或 "google" |
| `OAuthError: GitHub OAuth error` | GitHub 令牌交换失败 | 检查 Client ID/Secret |
| `OAuthError: Google OAuth error` | Google 令牌交换失败 | 检查 Client ID/Secret |
| `OAuthError: OAuth account already linked` | 账户已关联 | 不要重复关联 |
| `OAuthError: Cannot unlink last OAuth account` | 最后一个账户 | 先设置密码 |

## 测试

### 测试 GitHub OAuth

1. 启动应用：`uvicorn main:app --reload`
2. 访问：`http://localhost:8000/api/v1/auth/oauth/github`
3. 授权后自动重定向回应用

### 测试 Google OAuth

1. 启动应用：`uvicorn main:app --reload`
2. 访问：`http://localhost:8000/api/v1/auth/oauth/google`
3. 授权后自动重定向回应用

## 前端集成

### React 示例

```jsx
import { useState } from 'react';

function OAuthLoginButton({ provider }) {
  const [loading, setLoading] = useState(false);

  const handleOAuthLogin = async () => {
    setLoading(true);
    try {
      // 1. 获取授权 URL
      const response = await fetch(`/api/v1/auth/oauth/${provider}`);
      const { url, state } = await response.json();

      // 2. 保存 state 到 localStorage
      localStorage.setItem('oauth_state', state);
      localStorage.setItem('oauth_provider', provider);

      // 3. 重定向到 OAuth 提供商
      window.location.href = url;
    } catch (error) {
      console.error('OAuth login failed:', error);
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleOAuthLogin}
      disabled={loading}
      className="oauth-button"
    >
      {loading ? 'Loading...' : `Login with ${provider === 'github' ? 'GitHub' : 'Google'}`}
    </button>
  );
}

export default OAuthLoginButton;
```

## 常见问题

### Q: OAuth 用户可以设置密码吗？

A: 可以。OAuth 用户可以在后续设置密码，然后同时使用 OAuth 和密码登录。

### Q: 可以关联多个相同提供商的账户吗？

A: 不可以。每个用户每个提供商只能关联一个账户（例如：一个 GitHub 账户）。

### Q: 如何取消关联 OAuth 账户？

A: 调用 `unlink_oauth_account()` 方法。如果是最后一个 OAuth 账户且未设置密码，会拒绝操作。

### Q: OAuth 令牌会过期吗？

A: 取决于提供商。GitHub 令牌不会过期（除非用户撤销），Google 令牌会过期（支持刷新令牌）。

## 下一步

- [ ] 实现 API 路由（FastAPI）
- [ ] 实现前端 OAuth 登录按钮
- [ ] 实现用户账户管理界面
- [ ] 添加更多 OAuth 提供商（Facebook, Twitter 等）
- [ ] 实现 OAuth 令牌自动刷新

## 相关文档

- [GitHub OAuth 文档](https://docs.github.com/en/developers/apps/building-oauth-apps)
- [Google OAuth 2.0 文档](https://developers.google.com/identity/protocols/oauth2)
- [OAuth 2.0 规范](https://oauth.net/2/)
