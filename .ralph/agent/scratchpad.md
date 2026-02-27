# Ralph Loop Scratchpad

## Current Iteration: User Registration and Login API Implementation

### Objective
全面分析整个代码，搜索相关的资料，实现用户管理功能和登陆功能

### Analysis Completed
1. Found existing Auth module with models at `ModuleFolders/Service/Auth/models.py`
2. Database models already defined: User, Tenant, ApiKey, LoginHistory, RefreshToken, PasswordReset, EmailVerification
3. FastAPI app is in `Tools/WebServer/web_server.py`

### Implementation Done (Task 1: 用户注册和登录API实现)

Created the following new files:
1. `ModuleFolders/Service/Auth/jwt_handler.py` - JWT token creation and verification
2. `ModuleFolders/Service/Auth/password_manager.py` - Password hashing with bcrypt
3. `ModuleFolders/Service/Auth/auth_manager.py` - Registration, login, logout, token refresh logic

Modified files:
1. `Tools/WebServer/web_server.py` - Added auth API endpoints:
   - POST /api/v1/auth/register
   - POST /api/v1/auth/login
   - POST /api/v1/auth/refresh
   - POST /api/v1/auth/logout
   - GET /api/v1/auth/me
2. `ModuleFolders/Service/Auth/__init__.py` - Added exports for new modules
3. `pyproject.toml` - Added bcrypt and pyjwt dependencies

### Next Tasks
- Task 2: JWT认证中间件实现 - Need to add middleware for protected routes (IN PROGRESS)

### Implementation Done (Task 2: JWT认证中间件实现)

Created the following:
1. `ModuleFolders/Service/Auth/auth_middleware.py` - JWT authentication middleware with:
   - `JWTAuthMiddleware` class for token verification
   - `get_current_user` dependency for protected routes
   - `get_current_user_optional` dependency for optional authentication
   - `require_role()` factory for role-based access control
   - `require_admin()` shortcut for admin-only routes

Modified files:
1. `Tools/WebServer/web_server.py` - Updated `/api/v1/auth/me` to use new middleware
   - Added protected route examples:
     - GET /api/v1/auth/protected - Requires authentication
     - GET /api/v1/auth/optional - Optional authentication
     - GET /api/v1/auth/admin - Admin only
2. `ModuleFolders/Service/Auth/__init__.py` - Added exports for new middleware

### Usage Examples

```python
# Required authentication
@app.get("/protected")
async def protected(user: User = Depends(jwt_middleware.get_current_user)):
    return {"user": user.id}

# Optional authentication
@app.get("/optional")
async def optional(user: Optional[User] = Depends(jwt_middleware.get_current_user_optional)):
    if user:
        return {"user": user.id}
    return {"message": "anonymous"}

# Role-based access
@app.get("/admin")
async def admin(user: User = Depends(jwt_middleware.require_admin())):
    return {"message": "admin only"}
```

### Notes
- The auth endpoints return access_token and refresh_token
- Uses bcrypt for password hashing
- JWT tokens: 15 min access, 7 days refresh
- Account locking after 5 failed login attempts
