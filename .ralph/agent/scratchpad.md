# Scratchpad - User Management & Monetization System

## 2026-02-27 20:35 - Initial Assessment

### Project Analysis

**Current Status:**
- ✅ Auth service exists (ModuleFolders/Service/Auth/)
- ✅ Database models: User, Tenant, ApiKey, LoginHistory, PasswordReset, EmailVerification, RefreshToken
- ✅ Auth manager: register, login, refresh, logout
- ✅ JWT handler and password manager
- ✅ Auth middleware
- ✅ Auth API endpoints in web_server.py

**Missing Components:**

#### Phase 1 - Core User System (Partial)
- ❌ OAuth manager (GitHub, Google login)
- ❌ Email service for verification/reset
- ❌ User service for profile management
- ❌ Password reset flow implementation
- ❌ Email verification flow implementation

#### Phase 2 - RBAC (Missing)
- ❌ Permission verification middleware
- ❌ Role assignment functionality
- ❌ API key management endpoints

#### Phase 3 - Billing/Subscription (Not Started)
- ❌ Billing service folder (doesn't exist)
- ❌ Usage tracker
- ❌ Subscription manager
- ❌ Stripe integration
- ❌ Payment processor
- ❌ Invoice generator
- ❌ Quota enforcer
- ❌ Stripe webhook handler

#### Phase 4 - Advanced Features (Missing)
- ❌ Tenant service
- ❌ Team management
- ❌ SSO enterprise login

### Technical Notes

**Database:**
- Uses Peewee ORM
- Falls back to SQLite if PostgreSQL unavailable
- Models reference `pgsql.database` which doesn't exist
- Need to create proper database configuration

**Web Server:**
- FastAPI based
- Auth endpoints implemented: `/api/v1/auth/*`
- Need to add billing endpoints: `/api/v1/subscriptions/*`, `/api/v1/usage/*`

**Frontend:**
- React + TypeScript + Vite
- Located in Tools/WebServer/
- No auth UI pages yet (login, register, settings)

### Implementation Plan

1. **Fix database configuration** - Create proper pgsql.py module
2. **Complete Phase 1** - OAuth, email service, password reset flows
3. **Build Phase 2** - RBAC middleware, permissions
4. **Build Phase 3** - Entire billing system
5. **Add Phase 4** - Tenant service, team management

### Next Actions

1. Create database configuration module
2. Implement email service
3. Build OAuth manager
4. Create billing service structure
