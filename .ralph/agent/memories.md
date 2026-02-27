# Memories

## Patterns

### mem-1772181035-4ed5
> 用户注册和登录API已实现: 包含注册、登录、登出、token刷新和获取当前用户功能。使用JWT(HS256)进行认证，bcrypt进行密码哈希。访问令牌15分钟有效，刷新令牌7天有效。账户5次登录失败后锁定15分钟。
<!-- tags: auth, api, implementation | created: 2026-02-27 -->

### mem-1772180703-5791
> Peewee 3.18.3 版本不支持 JSONField，需要自定义 JSONField 类使用 TextField 实现
<!-- tags: database, peewee, orm | created: 2026-02-27 -->

### mem-1772179886-ba52
> BilingualPlugin 需要在 plugin_enables 中手动启用，default_enable=False。双语功能需要两部分：1)BilingualPlugin修改translated_text为'译文+原文' 2)enable_bilingual_output配置生成分离双语文件
<!-- tags: bilingual, plugin, configuration | created: 2026-02-27 -->

## Decisions

## Fixes

## Context

### mem-1772180341-b07d
> AiNiee项目: 当前无用户管理和认证系统，需要全新开发。推荐使用Supabase或自建FastAPI后端实现认证和用户管理
<!-- tags: user-management, authentication, architecture | created: 2026-02-27 -->
