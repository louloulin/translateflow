# Task Plan

## Objective
UI still lacks user info in the top right corner. Implement:
1. User info display in top right corner (Already implemented ✓)
2. Redirect to login page when not authenticated (NEEDS WORK)
3. Default admin account with username "admin" and password "admin" (NEEDS WORK)

## Analysis

### Current State
- User info display IS already implemented in MainLayout.tsx (lines 244-297)
- Login/Register buttons show for unauthenticated users
- NO redirect to login when accessing protected routes
- NO default admin user exists

### Work Needed
1. **Add redirect logic**: MainLayout needs to redirect unauthenticated users to /login
2. **Create default admin**: Backend startup should create admin user if not exists

## Implementation Plan

### Task 1: Add auth redirect in MainLayout
- Add useEffect to check isAuthenticated
- Redirect to /login when not authenticated and not on auth pages
- Must handle loading state properly

### Task 2: Create default admin user
- Add startup logic in web_server.py or auth_manager.py
- Create admin user with username="admin", password="admin"
- Run once on startup
