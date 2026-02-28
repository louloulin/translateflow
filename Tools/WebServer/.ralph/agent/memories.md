# Memories

## Patterns

### mem-1772200648-08bd
> 用户管理 API 路由实现完成：在 web_server.py 中添加了12个用户管理 API 路由。当前用户API包括：GET/PUT /api/v1/users/me（获取/更新资料）、PUT /api/v1/users/me/email/password（更新邮箱/密码）、DELETE /api/v1/users/me（删除账户）、GET/PUT /api/v1/users/me/preferences（偏好管理）、GET /api/v1/users/me/login-history（登录历史）。管理员API包括：GET /api/v1/users（用户列表，支持搜索过滤分页）、GET /api/v1/users/{id}（用户详情）、PUT /api/v1/users/{id}/role（更新角色）、PUT /api/v1/users/{id}/status（更新状态）。所有路由使用JWT认证，管理员路由使用require_admin()中间件，包含完整的中文文档和错误处理。
<!-- tags: api, user-management, implementation | created: 2026-02-27 -->

## Decisions

## Fixes

## Context
