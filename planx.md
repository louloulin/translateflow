# TranslateFlow 部署计划总览 (Deployment Plan)

> **项目**: TranslateFlow (formerly AiNiee-Next)
> **版本**: v1.0.0
> **最后更新**: 2026-02-28
> **状态**: ✅ 生产就绪

---

## 📋 目录 (Table of Contents)

1. [项目概述](#项目概述)
2. [架构设计](#架构设计)
3. [部署方案对比](#部署方案对比)
4. [快速开始指南](#快速开始指南)
5. [平台部署详解](#平台部署详解)
6. [自动化脚本](#自动化脚本)
7. [安全检查清单](#安全检查清单)
8. [监控与运维](#监控与运维)
9. [故障排查](#故障排查)
10. [CI/CD集成](#cicd集成)
11. [成本估算](#成本估算)
12. [最佳实践](#最佳实践)

---

## 项目概述

TranslateFlow 是一个AI驱动的翻译平台，支持多语言翻译、OCR识别、项目管理等功能。

### 核心组件

| 组件 | 技术栈 | 端口 | 说明 |
|------|--------|------|------|
| **后端API** | FastAPI (Python 3.12) | 8000 | RESTful API，异步处理 |
| **前端UI** | React 19 + Vite 6.4 | 4200 (dev) | SPA，客户端路由 |
| **数据库** | PostgreSQL 15 / SQLite | 5432 | 主数据存储 |
| **文件存储** | 本地 / 对象存储 | - | 上传文件、输出结果 |

### 环境需求

**最低配置**:
- CPU: 2核
- RAM: 2GB (推荐 4GB)
- 磁盘: 10GB (推荐 20GB)
- Python: 3.12
- Node.js: 20.x

**生产环境推荐**:
- CPU: 4核
- RAM: 4GB
- 磁盘: 50GB SSD
- PostgreSQL: 15+
- CDN: 可选

---

## 架构设计

### 系统架构图

```
┌──────────────────────────────────────────────────────────────┐
│                         负载均衡 / CDN                         │
│                    (Nginx / Vercel Edge)                      │
└───────────────────────────┬──────────────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
┌───────▼────────┐                    ┌────────▼────────┐
│  React Frontend│                    │ FastAPI Backend │
│  (Vite Build)  │◄─── HTTPS ────────►│   (Uvicorn)     │
│  Static Assets │    API Calls       │   Port 8000     │
└────────────────┘                    └────────┬────────┘
                                               │
                    ┌──────────────────────────┼───────────────────┐
                    │                          │                   │
            ┌───────▼────────┐      ┌────────▼────────┐  ┌───────▼────────┐
            │  PostgreSQL    │      │   File Storage  │  │ External APIs  │
            │  (Primary DB)  │      │  (output/temp)  │  │ (Stripe/Email) │
            └────────────────┘      └─────────────────┘  └────────────────┘
```

### 数据流

1. **用户访问**: 用户通过浏览器访问前端
2. **API请求**: 前端调用后端REST API
3. **业务处理**: 后端处理翻译、OCR、认证等逻辑
4. **数据持久化**: 数据存储到PostgreSQL
5. **文件存储**: 输出文件保存到文件系统

### 部署架构选项

| 选项 | 前端 | 后端 | 数据库 | 复杂度 | 成本 | 适用场景 |
|------|------|------|--------|--------|------|----------|
| **A: Docker Compose** | 容器内 | 容器内 | 容器内 | 低 | $5-30/mo | 自托管、小型团队 |
| **B: Dokploy** | 容器 | 容器 | 托管 | 低 | $10-50/mo | PaaS平台、快速部署 |
| **C: Vercel + Railway** | Vercel | Railway | Railway | 中 | $5-30/mo | 全球分发、生产环境 |
| **D: Kubernetes** | 容器 | 容器 | 托管 | 高 | $50-200/mo | 大规模、高可用 |

---

## 部署方案对比

### 方案A: Docker Compose (推荐用于自托管)

**优势**:
- ✅ 完全控制
- ✅ 一键部署
- ✅ 适合内网环境
- ✅ 成本低

**劣势**:
- ❌ 需要运维
- ❌ 需要手动扩展
- ❌ 需要手动备份

**适用场景**:
- 内网部署
- 开发/测试环境
- 小型团队（<50用户）

**详细指南**: [DEPLOYMENT_DOCKER.md](./DEPLOYMENT_DOCKER.md)

---

### 方案B: Dokploy PaaS (推荐用于快速部署)

**优势**:
- ✅ 简单易用
- ✅ 自动扩展
- ✅ 内置监控
- ✅ SSL自动配置

**劣势**:
- ❌ 需要Dokploy服务器
- ❌ 平台锁定
- ❌ 成本较高

**适用场景**:
- 快速上线
- 中小型团队
- 不想管理服务器

**详细指南**: [DEPLOYMENT_DOKPLOY.md](./DEPLOYMENT_DOKPLOY.md)

---

### 方案C: Vercel + Railway (推荐用于生产环境)

**优势**:
- ✅ 全球CDN
- ✅ 自动扩展
- ✅ 高可用性
- ✅ 免费额度

**劣势**:
- ❌ 前后端分离
- ❌ 配置较复杂
- ❌ 需要自定义域名

**适用场景**:
- 全球用户
- 生产环境
- 高流量网站

**详细指南**: [DEPLOYMENT_VERCEL.md](./DEPLOYMENT_VERCEL.md)

---

### 方案D: Kubernetes (企业级)

**优势**:
- ✅ 高可用性
- ✅ 自动扩展
- ✅ 滚动更新
- ✅ 多集群管理

**劣势**:
- ❌ 复杂度高
- ❌ 运维成本高
- ❌ 学习曲线陡

**适用场景**:
- 大型企业
- 高并发需求
- 多环境部署

**注意**: Kubernetes部署配置需要单独开发，当前版本未包含。

---

## 快速开始指南

### 选择部署方案

根据您的需求选择合适的部署方案：

```
┌─────────────────────────────────────────────────────────────┐
│                    部署方案决策树                             │
└─────────────────────────────────────────────────────────────┘

是否有服务器？
│
├─ 是 → 是否需要完全控制？
│       │
│       ├─ 是 → [方案A: Docker Compose]
│       │
│       └─ 否 → 是否有Dokploy？
│               │
│               ├─ 是 → [方案B: Dokploy]
│               │
│               └─ 否 → [方案A: Docker Compose]
│
└─ 否 → 是否需要全球CDN？
        │
        ├─ 是 → [方案C: Vercel + Railway]
        │
        └─ 否 → 预算是否充足？
                │
                ├─ 是 → [方案C: Vercel + Railway]
                │
                └─ 否 → 考虑云服务器 + [方案A]
```

### 5分钟快速部署 (Docker Compose)

```bash
# 1. 克隆仓库
git clone https://github.com/ShadowLoveElysia/TranslateFlow.git
cd TranslateFlow

# 2. 配置环境变量
cp .env.example .env
nano .env  # 编辑配置，设置DB_PASSWORD和SECRET_KEY

# 3. 一键启动
chmod +x scripts/deploy.sh
./scripts/deploy.sh setup
./scripts/deploy.sh start

# 4. 检查状态
./scripts/health-check.sh

# 5. 访问应用
# 浏览器打开: http://localhost:8000
# 默认账号: admin / admin (⚠️ 首次登录后请修改密码)
```

---

## 平台部署详解

### 1. Docker Compose 部署

**文件清单**:
- `Dockerfile.production` - 生产环境镜像
- `docker-compose.yml` - 编排配置
- `docker-compose.override.yml` - 开发环境覆盖
- `.env.example` - 环境变量模板
- `scripts/deploy.sh` - 部署脚本
- `scripts/health-check.sh` - 健康检查脚本
- `scripts/db-migrate.sh` - 数据库迁移脚本

**核心命令**:
```bash
./scripts/deploy.sh setup    # 初始化配置
./scripts/deploy.sh build    # 构建镜像
./scripts/deploy.sh start    # 启动服务
./scripts/deploy.sh stop     # 停止服务
./scripts/deploy.sh logs     # 查看日志
./scripts/deploy.sh status   # 查看状态
./scripts/deploy.sh backup   # 备份数据
./scripts/deploy.sh update   # 更新部署
```

**详细指南**: [DEPLOYMENT_DOCKER.md](./DEPLOYMENT_DOCKER.md)

---

### 2. Dokploy 部署

**文件清单**:
- `docker-compose.dokploy.yml` - Dokploy专用配置
- `.env.dokploy.example` - 环境变量模板
- `scripts/deploy-dokploy.sh` - 部署自动化脚本

**部署步骤**:
1. 准备Dokploy服务器
2. 创建PostgreSQL服务（推荐使用托管数据库）
3. 创建应用并上传`docker-compose.dokploy.yml`
4. 配置环境变量
5. 配置自定义域名和SSL

**详细指南**: [DEPLOYMENT_DOKPLOY.md](./DEPLOYMENT_DOKPLOY.md)

---

### 3. Vercel + Railway 部署

**文件清单**:
- `Tools/WebServer/vercel.json` - Vercel配置
- `.env.vercel.example` - 前端环境变量
- `.env.backend.example` - 后端环境变量
- `scripts/deploy-vercel-frontend.sh` - 前端部署脚本

**部署步骤**:
1. 后端部署到Railway
2. 前端部署到Vercel
3. 配置API连接
4. 配置自定义域名

**详细指南**: [DEPLOYMENT_VERCEL.md](./DEPLOYMENT_VERCEL.md)

---

### 4. 多平台构建

**脚本**: `scripts/build-docker-multiplatform.sh`

**支持平台**:
- `linux/amd64` (标准x86_64)
- `linux/arm64` (ARM 64位，如Apple Silicon)

**构建命令**:
```bash
# 构建所有平台
./scripts/build-docker-multiplatform.sh

# 构建特定平台
./scripts/build-docker-multiplatform.sh -p linux/amd64
./scripts/build-docker-multiplatform.sh -p linux/arm64

# 推送到镜像仓库
./scripts/build-docker-multiplatform.sh --push
```

---

## 自动化脚本

### 部署脚本 (scripts/deploy.sh)

**功能**: Docker部署的主控制脚本

**命令**:
```bash
./scripts/deploy.sh setup      # 初始化配置（生成.env、密钥等）
./scripts/deploy.sh build      # 构建Docker镜像
./scripts/deploy.sh start      # 启动所有服务
./scripts/deploy.sh stop       # 停止服务
./scripts/deploy.sh restart    # 重启服务
./scripts/deploy.sh logs       # 查看日志
./scripts/deploy.sh status     # 查看服务状态
./scripts/deploy.sh clean      # 清理停止的容器和未使用的镜像
./scripts/deploy.sh backup     # 备份数据库和卷
./scripts/deploy.sh restore    # 从备份恢复
./scripts/deploy.sh update     # 拉取最新代码并重新部署
./scripts/deploy.sh help       # 显示帮助信息
```

**示例**:
```bash
# 初始化并启动
./scripts/deploy.sh setup && ./scripts/deploy.sh start

# 查看状态
./scripts/deploy.sh status

# 备份
./scripts/deploy.sh backup

# 更新
./scripts/deploy.sh update
```

---

### 健康检查脚本 (scripts/health-check.sh)

**功能**: 监控应用健康状态

**检查项**:
1. Docker守护进程状态
2. 后端API健康检查
3. 数据库连接状态
4. 容器运行状态
5. 磁盘空间使用
6. 内存使用情况

**命令**:
```bash
# 基础健康检查
./scripts/health-check.sh

# 详细报告
./scripts/health-check.sh --verbose

# JSON输出（用于CI/CD）
./scripts/health-check.sh --json

# 快速模式（仅检查关键项）
./scripts/health-check.sh --quick

# 持续监控（每30秒检查一次）
./scripts/health-check.sh --watch

# 自定义超时
./scripts/health-check.sh --timeout 10
```

**退出码**:
- `0` - 健康
- `1` - 不健康

**示例**:
```bash
# 基础检查
./scripts/health-check.sh

# CI/CD集成
if ./scripts/health-check.sh --quick; then
    echo "健康检查通过"
    ./scripts/deploy.sh update
else
    echo "健康检查失败"
    exit 1
fi

# 持续监控
./scripts/health-check.sh --watch
```

---

### 数据库迁移脚本 (scripts/db-migrate.sh)

**功能**: 数据库迁移和管理

**命令**:
```bash
# 查看迁移状态
./scripts/db-migrate.sh status

# 列出所有迁移
./scripts/db-migrate.sh list

# 创建新迁移
./scripts/db-migrate.sh create add_user_preferences_table

# 执行迁移
./scripts/db-migrate.sh migrate

# 回滚最后一个迁移
./scripts/db-migrate.sh rollback

# 填充种子数据
./scripts/db-migrate.sh seed

# 重置数据库（⚠️ 危险操作，仅开发环境）
./scripts/db-migrate.sh reset

# 备份数据库
./scripts/db-migrate.sh backup

# 测试模式（不实际执行）
./scripts/db-migrate.sh migrate --dry-run
```

**迁移文件**:
- 位置: `migrations/`
- 命名格式: `YYYYMMDDHHMMSS_description.sql`
- 版本跟踪: `schema_migrations` 表

**示例**:
```bash
# 开发环境：创建并执行迁移
./scripts/db-migrate.sh create add_index_on_users_email
./scripts/db-migrate.sh migrate

# 生产环境：备份并迁移
./scripts/db-migrate.sh backup
./scripts/db-migrate.sh migrate

# 回滚
./scripts/db-migrate.sh rollback
```

---

### 平台特定脚本

#### Dokploy部署脚本 (scripts/deploy-dokploy.sh)

```bash
# 验证配置
./scripts/deploy-dokploy.sh validate

# 生成密钥
./scripts/deploy-dokploy.sh generate-secrets

# 构建并导出
./scripts/deploy-dokploy.sh build

# 完整部署流程
./scripts/deploy-dokploy.sh deploy

# 部署前检查清单
./scripts/deploy-dokploy.sh checklist
```

#### Vercel前端部署脚本 (scripts/deploy-vercel-frontend.sh)

```bash
# 验证环境
./scripts/deploy-vercel-frontend.sh validate

# 安装依赖
./scripts/deploy-vercel-frontend.sh install

# 本地构建测试
./scripts/deploy-vercel-frontend.sh build

# 部署到预览环境
./scripts/deploy-vercel-frontend.sh preview

# 部署到生产环境
./scripts/deploy-vercel-frontend.sh production

# 查看部署日志
./scripts/deploy-vercel-frontend.sh logs

# 配置自定义域名
./scripts/deploy-vercel-frontend.sh domains
```

---

## 安全检查清单

### 生产环境部署前必查项

#### 🔴 关键安全项（必须完成）

- [ ] **修改默认密码**
  - 修改admin账户默认密码
  - 设置强密码策略（最少12位，包含大小写字母、数字、特殊字符）

- [ ] **生成安全密钥**
  - `SECRET_KEY`: 使用 `openssl rand -hex 32` 生成
  - `DB_PASSWORD`: 使用强密码生成器
  - `JWT_SECRET_KEY`: 与SECRET_KEY不同

- [ ] **配置HTTPS/SSL**
  - 使用Let's Encrypt获取免费SSL证书
  - 配置自动续期
  - 强制HTTPS重定向

- [ ] **数据库安全**
  - PostgreSQL不暴露到公网
  - 使用强密码
  - 限制远程访问
  - 定期备份

- [ ] **环境变量保护**
  - `.env`文件不提交到版本控制
  - 使用`.env.example`作为模板
  - 生产环境密钥与开发环境分离

#### 🟡 重要安全项（强烈推荐）

- [ ] **CORS配置**
  - 限制允许的源域名
  - 不使用 `*` 通配符

- [ ] **API限流**
  - 配置速率限制
  - 防止DDoS攻击

- [ ] **文件上传限制**
  - 限制文件大小
  - 限制文件类型
  - 扫描恶意文件

- [ ] **日志安全**
  - 不记录敏感信息（密码、token）
  - 定期清理日志
  - 设置日志轮转

#### 🟢 增强安全项（可选）

- [ ] **监控告警**
  - 配置异常登录告警
  - 配置资源使用告警

- [ ] **备份策略**
  - 自动定期备份
  - 异地备份存储
  - 备份恢复测试

- [ ] **访问控制**
  - 配置防火墙规则
  - 限制管理端口访问
  - 使用VPN/堡垒机

### 安全配置示例

#### .env文件安全配置

```bash
# ===========================================
# 安全配置（生产环境）
# ===========================================

# 密钥（使用 openssl rand -hex 32 生成）
SECRET_KEY=your-generated-secret-key-here
DB_PASSWORD=your-strong-db-password-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# CORS（替换为实际域名）
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# 数据库（不暴露到公网）
DB_HOST=postgres  # Docker内部网络
DB_PORT=5432

# 限流
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60

# 文件上传
MAX_UPLOAD_SIZE=10485760  # 10MB
ALLOWED_FILE_TYPES=txt,pdf,docx,doc,xlsx,png,jpg,jpeg

# 日志
LOG_LEVEL=INFO
LOG_SENSITIVE_DATA=false
```

#### Nginx SSL配置示例

```nginx
server {
    listen 80;
    server_name translateflow.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name translateflow.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/translateflow.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/translateflow.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 监控与运维

### 健康检查端点

TranslateFlow提供以下健康检查端点：

| 端点 | 用途 | 响应 |
|------|------|------|
| `GET /api/system/status` | 系统状态 | JSON: `{status: "healthy", version: "..."}` |
| `GET /api/health` | 基础健康检查 | 200 OK |
| `GET /api/translate/status` | 翻译服务状态 | JSON: 服务可用性 |
| `GET /api/proofread/status` | 校对服务状态 | JSON: 服务可用性 |

### 监控指标

#### 系统指标

```bash
# 使用健康检查脚本
./scripts/health-check.sh --json

# 输出示例
{
  "overall_status": "healthy",
  "checks": {
    "docker": "healthy",
    "api": "healthy",
    "database": "healthy",
    "containers": "healthy",
    "disk_usage": "warning",
    "memory": "healthy"
  },
  "metrics": {
    "disk_usage_percent": 85,
    "memory_usage_percent": 62,
    "api_response_time_ms": 145
  },
  "warnings": [
    "Disk usage at 85%, consider cleaning up"
  ]
}
```

#### 应用指标

关键指标：
- API响应时间
- 数据库连接数
- 翻译任务队列长度
- 内存使用率
- CPU使用率

### 日志管理

#### 查看日志

```bash
# Docker Compose
docker-compose logs -f app

# 查看最近100行
docker-compose logs --tail=100 app

# 查看特定时间段
docker-compose logs --since="2024-01-01T00:00:00" app
```

#### 日志配置

```bash
# .env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=json  # json 或 text
LOG_FILE=/var/log/translateflow/app.log
```

### 备份策略

#### 自动备份（推荐）

```bash
# 添加到crontab
# 每天凌晨2点备份
0 2 * * * /path/to/TranslateFlow/scripts/deploy.sh backup

# 每周日凌晨3点完整备份
0 3 * * 0 /path/to/TranslateFlow/scripts/deploy.sh backup --full
```

#### 手动备份

```bash
# 备份数据库
./scripts/deploy.sh backup

# 备份到指定位置
./scripts/deploy.sh backup --output /backups/translateflow

# 数据库迁移备份
./scripts/db-migrate.sh backup
```

#### 恢复备份

```bash
# 列出可用备份
ls -lh /backups/translateflow/

# 恢复
./scripts/deploy.sh restore --input /backups/translateflow/backup-20240128.tar.gz
```

---

## 故障排查

### 常见问题

#### 1. 容器启动失败

**症状**: `docker-compose up` 失败

**排查步骤**:
```bash
# 查看详细日志
docker-compose logs app

# 检查配置
docker-compose config

# 检查端口占用
netstat -tlnp | grep 8000

# 检查磁盘空间
df -h
```

**常见原因**:
- 端口被占用 → 修改`.env`中的`PORT`
- 磁盘空间不足 → 清理旧镜像和容器
- 内存不足 → 增加系统内存或减少服务

---

#### 2. 数据库连接失败

**症状**: 应用无法连接到数据库

**排查步骤**:
```bash
# 检查数据库容器
docker-compose ps postgres

# 查看数据库日志
docker-compose logs postgres

# 测试连接
docker-compose exec postgres psql -U translateflow -d translateflow

# 检查环境变量
docker-compose exec app env | grep DB_
```

**常见原因**:
- 数据库未启动 → `docker-compose up -d postgres`
- 密码错误 → 检查`.env`中的`DB_PASSWORD`
- 数据库未就绪 → 等待几秒后重试

---

#### 3. 前端无法访问后端API

**症状**: 前端报网络错误

**排查步骤**:
```bash
# 检查后端是否运行
curl http://localhost:8000/api/system/status

# 检查CORS配置
docker-compose exec app env | grep CORS

# 检查网络连接
docker-compose network inspect translateflow-network
```

**常见原因**:
- CORS配置错误 → 更新`CORS_ORIGINS`
- 后端未启动 → `docker-compose up -d app`
- 防火墙阻止 → 检查防火墙规则

---

#### 4. 内存不足

**症状**: 应用被OOM Killer杀死

**排查步骤**:
```bash
# 查看内存使用
free -h

# 查看容器内存限制
docker stats

# 查看系统日志
dmesg | grep -i oom
```

**解决方案**:
```yaml
# docker-compose.yml
services:
  app:
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G
```

---

#### 5. 健康检查失败

**症状**: 容器被标记为unhealthy

**排查步骤**:
```bash
# 手动测试健康检查
curl http://localhost:8000/api/system/status

# 查看健康检查日志
docker inspect --format='{{json .State.Health}}' translateflow-app | jq

# 检查健康检查配置
docker inspect --format='{{json .Config.Healthcheck}}' translateflow-app | jq
```

---

### 故障排查工具箱

```bash
# 一键诊断
./scripts/health-check.sh --verbose

# 查看所有容器状态
docker-compose ps

# 查看资源使用
docker stats

# 查看日志
docker-compose logs --tail=100 -f

# 进入容器调试
docker-compose exec app bash

# 重启服务
docker-compose restart app

# 完全重建
docker-compose down && docker-compose up -d --build
```

---

## CI/CD集成

### GitHub Actions示例

创建`.github/workflows/deploy.yml`:

```yaml
name: Deploy TranslateFlow

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: |
          docker build -f Dockerfile.production -t translateflow:${{ github.sha }} .
          docker tag translateflow:${{ github.sha }} translateflow:latest

      - name: Run tests
        run: |
          docker run --rm translateflow:${{ github.sha }} pytest

      - name: Health check
        run: |
          docker run -d -p 8000:8000 --name test-app translateflow:${{ github.sha }}
          sleep 30
          curl -f http://localhost:8000/api/system/status || exit 1
          docker stop test-app

      - name: Deploy to production
        if: success()
        env:
          SSH_KEY: ${{ secrets.SSH_PRIVATE_KEY }}
          DEPLOY_HOST: ${{ secrets.DEPLOY_HOST }}
        run: |
          # 使用健康检查脚本验证
          ssh -i $SSH_KEY user@$DEPLOY_HOST "cd /opt/translateflow && ./scripts/health-check.sh --quick"
          # 部署
          ssh -i $SSH_KEY user@$DEPLOY_HOST "cd /opt/translateflow && ./scripts/deploy.sh update"
          # 验证部署
          ssh -i $SSH_KEY user@$DEPLOY_HOST "cd /opt/translateflow && ./scripts/health-check.sh"
```

### GitLab CI示例

创建`.gitlab-ci.yml`:

```yaml
stages:
  - build
  - test
  - deploy

build:
  stage: build
  script:
    - docker build -f Dockerfile.production -t translateflow:$CI_COMMIT_SHA .
    - docker tag translateflow:$CI_COMMIT_SHA translateflow:latest

test:
  stage: test
  script:
    - docker run --rm translateflow:$CI_COMMIT_SHA pytest

deploy:
  stage: deploy
  only:
    - main
  script:
    - ./scripts/deploy.sh update
    - ./scripts/health-check.sh --json
  artifacts:
    reports:
      health: health-report.json
```

---

## 成本估算

### Docker Compose自托管

**服务器成本**:
- 云服务器（2C4G）: ¥100-300/月
- 带宽（5Mbps）: ¥50-150/月
- 备份存储（50GB）: ¥10-50/月
- **总计**: ¥160-500/月

**优势**: 完全控制、数据安全
**劣势**: 需要运维

---

### Dokploy PaaS

**平台成本**:
- 应用容器: ¥50-150/月
- 托管PostgreSQL: ¥50-100/月
- 域名+SSL: ¥10-50/月
- **总计**: ¥110-300/月

**优势**: 简单易用、自动扩展
**劣势**: 平台锁定

---

### Vercel + Railway

**前端成本**:
- Vercel Pro: ¥150/月
- 或 Vercel免费额度: ¥0/月（有限制）

**后端成本**:
- Railway: $5-20/月 (¥35-140/月)
- PostgreSQL: $5-10/月 (¥35-70/月)

**总计**:
- 免费方案: ¥35-70/月
- Pro方案: ¥185-360/月

**优势**: 全球CDN、高可用
**劣势**: 前后端分离配置复杂

---

### 成本对比表

| 方案 | 月成本（¥） | 年成本（¥） | 启动成本 | 运维难度 |
|------|------------|------------|----------|----------|
| Docker Compose | 160-500 | 1,920-6,000 | 低 | 中 |
| Dokploy | 110-300 | 1,320-3,600 | 低 | 低 |
| Vercel + Railway | 35-360 | 420-4,320 | 低 | 低 |
| Kubernetes | 200-1,000 | 2,400-12,000 | 高 | 高 |

**建议**:
- 小型团队（<10人）: Docker Compose或Vercel免费方案
- 中型团队（10-50人）: Dokploy或Vercel Pro
- 大型团队（50+人）: Kubernetes或混合云

---

## 最佳实践

### 开发环境

1. **使用docker-compose.override.yml**
   - 覆盖生产配置
   - 暴露调试端口
   - 启用DEBUG模式

2. **本地开发工作流**
   ```bash
   # 启动开发环境
   docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d

   # 查看日志
   docker-compose logs -f app

   # 重新构建
   docker-compose up -d --build app
   ```

3. **数据管理**
   - 使用seed数据填充测试数据
   - 定期清理测试数据
   - 使用SQLite进行快速测试

---

### 生产环境

1. **环境隔离**
   - 开发、测试、生产环境分离
   - 使用不同的数据库
   - 不同的密钥和配置

2. **配置管理**
   - 使用环境变量管理配置
   - 不将敏感信息提交到版本控制
   - 使用密钥管理服务（如AWS Secrets Manager）

3. **高可用性**
   - 使用托管数据库
   - 配置自动备份
   - 配置监控和告警
   - 准备灾难恢复计划

4. **性能优化**
   - 使用CDN加速前端
   - 启用gzip压缩
   - 配置缓存策略
   - 优化数据库查询

---

### 安全实践

1. **定期更新**
   - 定期更新依赖包
   - 更新Docker基础镜像
   - 监控安全漏洞

2. **访问控制**
   - 最小权限原则
   - 定期审计用户权限
   - 记录操作日志

3. **数据保护**
   - 加密敏感数据
   - 定期备份
   - 测试恢复流程

---

### 监控和告警

1. **监控指标**
   - 服务可用性
   - 响应时间
   - 错误率
   - 资源使用率

2. **告警配置**
   - 服务宕机告警
   - 高负载告警
   - 磁盘空间告警
   - 异常登录告警

3. **日志分析**
   - 集中式日志收集
   - 日志分析工具（如ELK）
   - 定期审计日志

---

## 附录

### 相关文档

- [DEPLOYMENT_DOCKER.md](./DEPLOYMENT_DOCKER.md) - Docker Compose部署详解
- [DEPLOYMENT_DOKPLOY.md](./DEPLOYMENT_DOKPLOY.md) - Dokploy部署详解
- [DEPLOYMENT_VERCEL.md](./DEPLOYMENT_VERCEL.md) - Vercel部署详解
- [README.md](./README.md) - 项目说明
- [PROJECT_SUMMARY.md](./.ralph/agent/PROJECT_SUMMARY.md) - 项目总结

### 脚本清单

| 脚本 | 功能 | 用途 |
|------|------|------|
| `scripts/deploy.sh` | 主部署脚本 | Docker环境部署 |
| `scripts/health-check.sh` | 健康检查 | 监控和诊断 |
| `scripts/db-migrate.sh` | 数据库迁移 | 数据库版本管理 |
| `scripts/deploy-dokploy.sh` | Dokploy部署 | PaaS平台部署 |
| `scripts/deploy-vercel-frontend.sh` | Vercel部署 | 前端部署 |
| `scripts/build-docker-multiplatform.sh` | 多平台构建 | 构建多架构镜像 |

### 环境变量清单

完整的环境变量列表请参考`.env.example`文件。

**必需变量**:
- `SECRET_KEY` - 应用密钥
- `DATABASE_URL` 或数据库配置
- `JWT_SECRET_KEY` - JWT密钥

**可选变量**:
- Stripe支付配置
- OAuth提供商配置
- 邮件服务配置

### 技术支持

**问题反馈**:
- GitHub Issues: https://github.com/ShadowLoveElysia/TranslateFlow/issues

**文档更新**:
- 如发现文档错误或不完善之处，欢迎提交PR

---

## 更新日志

### v1.0.0 (2026-02-28)

**新增**:
- ✅ Docker Compose部署配置
- ✅ Dokploy PaaS部署配置
- ✅ Vercel + Railway部署配置
- ✅ 部署自动化脚本（deploy.sh, health-check.sh, db-migrate.sh）
- ✅ 多平台Docker构建支持
- ✅ 生产优化Dockerfile
- ✅ 全面的部署文档

**文件统计**:
- 配置文件: 10+
- 脚本文件: 6个（共2,511行）
- 文档文件: 4个（共2,500+行）

---

**文档版本**: v1.0.0
**最后更新**: 2026-02-28
**维护者**: TranslateFlow Team
**许可**: MIT License
