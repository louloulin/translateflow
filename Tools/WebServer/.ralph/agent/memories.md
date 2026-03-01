# Memories

## Patterns

### mem-1772335066-5aec
> Playwright MCP bilingual output test completed: Frontend loads on port 4200, Backend API on port 8000, Login works with admin/admin, Bilingual viewer UI loads correctly showing loading state then error (expected - no project cache). The bilingual viewer component renders without JS crashes, error handling works properly.
<!-- tags: testing, playwright, bilingual | created: 2026-03-01 -->

### mem-1772332019-24ff
> File comparison dashboard implemented: Created FileComparisonDashboard component with 3 view modes (grid, list, compare), statistics cards (total/completed/in-progress/avg progress/diffs), filtering by status, multi-select with batch JSON export, pagination (12 items/page), file status badges (Original/Translated/Bilingual), progress bars, file size formatting. Route: /comparison/:projectId. Crowdin/Transifex-inspired design with three-column comparison. Files: Tools/WebServer/components/FileComparisonDashboard.tsx (592 lines), pages/FileComparisonView.tsx (10 lines). Committed: 6bdce4fa
<!-- tags: file-management, dashboard, comparison, ui, translation | created: 2026-03-01 -->

### mem-1772200648-08bd
> 用户管理 API 路由实现完成：在 web_server.py 中添加了12个用户管理 API 路由。当前用户API包括：GET/PUT /api/v1/users/me（获取/更新资料）、PUT /api/v1/users/me/email/password（更新邮箱/密码）、DELETE /api/v1/users/me（删除账户）、GET/PUT /api/v1/users/me/preferences（偏好管理）、GET /api/v1/users/me/login-history（登录历史）。管理员API包括：GET /api/v1/users（用户列表，支持搜索过滤分页）、GET /api/v1/users/{id}（用户详情）、PUT /api/v1/users/{id}/role（更新角色）、PUT /api/v1/users/{id}/status（更新状态）。所有路由使用JWT认证，管理员路由使用require_admin()中间件，包含完整的中文文档和错误处理。
<!-- tags: api, user-management, implementation | created: 2026-02-27 -->

## Decisions

## Fixes

## Context
