# Python + Web 桌面应用构建方案

## 项目背景

TranslateFlow (原 AiNiee-Next) 当前架构:
- **桌面 UI**: PyQt (source/AiNiee/UserInterface)
- **后端 API**: FastAPI (Python 3.12)
- **前端**: React + Vite
- **部署**: Docker 多平台构建

本方案研究如何将现有的 Python+Web 技术栈转换为桌面应用。

---

## 方案对比

### 1. Tauri + Python (推荐)

**架构**: Rust 主进程 + System WebView + Python 子进程

| 指标 | 数值 |
|------|------|
| 安装包大小 | 4-12 MB |
| 内存占用 | 35-100 MB |
| 启动时间 | 0.3-1 秒 |
| 安全等级 | 最高 |

**优点**:
- 体积最小，比 Electron 小 90%
- 性能最佳，启动速度最快
- 内存安全 (Rust)
- 默认沙箱隔离
- Tauri 2.0 支持 iOS/Android

**缺点**:
- 需要学习 Rust 基础
- 插件生态较小 (500+ vs Electron 100K+)
- 首次编译时间长

**Python 集成方式**:
```python
# 使用 pytauri 或直接通过子进程
import subprocess
import sys

def start_python_backend():
    # 启动 Python FastAPI 后端
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "Tools.WebServer.web_server:app"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return proc
```

**前端通过 Tauri IPC 调用**:
```typescript
// React 前端调用 Python 后端
import { invoke } from '@tauri-apps/api/core';

// 调用 Python 服务
const result = await invoke('proxy-request', {
    method: 'POST',
    path: '/api/v1/tasks/start',
    body: taskConfig
});
```

---

### 2. Electron + Python

**架构**: Chromium + Node.js + Python 子进程

| 指标 | 数值 |
|------|------|
| 安装包大小 | 100-300 MB |
| 内存占用 | 200-500 MB |
| 启动时间 | 2-5 秒 |
| 安全等级 | 中等 |

**优点**:
- 生态最成熟 (100K+ npm 包)
- 无需学习新语言
- 一致性最好 (独立 Chromium)
- 调试工具完善

**缺点**:
- 体积最大
- 内存占用高
- 安全配置复杂

---

### 3. PyWebView

**架构**: 系统 WebView + Python

| 指标 | 数值 |
|------|------|
| 安装包大小 | 1-3 MB |
| 内存占用 | 50-150 MB |
| 启动时间 | 0.5-2 秒 |

**优点**:
- 纯 Python，最简单
- 体积最小
- 适合内部工具

**缺点**:
- 功能有限
- 不适合复杂应用

---

### 4. Flet

**架构**: Flutter 引擎 + Python

| 指标 | 数值 |
|------|------|
| 安装包大小 | 40-60 MB |
| 内存占用 | 120-250 MB |
| 启动时间 | 1-2 秒 |

**优点**:
- Python 原生支持
- 支持移动端
- Flutter UI 组件丰富

**缺点**:
- 体积较大
- 不适合保留现有 React 前端

---

## 推荐方案: Tauri + Python

### 架构设计

```
┌─────────────────────────────────────────┐
│           Tauri (Rust)                  │
│  ┌───────────────────────────────────┐  │
│  │  - 窗口管理                       │  │
│  │  - 系统集成 (托盘/通知/文件)       │  │
│  │  - IPC 路由                      │  │
│  │  - Python 子进程管理              │  │
│  └───────────────────────────────────┘  │
├─────────────────────────────────────────┤
│         React Frontend (Vite)           │
│  - 现有前端代码复用                     │
│  - 通过 Tauri API 调用后端              │
├─────────────────────────────────────────┤
│       Python FastAPI Backend             │
│  - 现有 API 复用                       │
│  - 独立进程运行                        │
│  - 通过 HTTP 与前端通信                 │
└─────────────────────────────────────────┘
```

### 实现步骤

1. **创建 Tauri 项目**
   ```bash
   npm create tauri-app@latest translateflow
   ```

2. **配置 Python 后端**
   - 修改 web_server.py 支持外部连接
   - 配置 CORS
   - 添加健康检查端点

3. **前端集成**
   - 安装 @tauri-apps/api
   - 创建 API 代理层
   - 处理后端启动/停止

4. **系统集成**
   - 托盘图标
   - 系统通知
   - 文件关联
   - 自动更新

5. **构建发布**
   - 配置签名
   - 多平台构建

### 关键代码

**Tauri 命令 (Rust)**:
```rust
#[tauri::command]
async fn start_backend(port: u16) -> Result<(), String> {
    // 启动 Python 后端进程
    let mut child = Command::new("python")
        .args(["-m", "uvicorn", "Tools.WebServer.web_server:app",
               "--port", &port.to_string()])
        .spawn()
        .map_err(|e| e.to_string())?;
    Ok(())
}
```

**前端 API 代理**:
```typescript
// src/lib/api.ts
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function createTask(config: TaskConfig) {
    const response = await fetch(`${API_BASE}/api/v1/tasks/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
    });
    return response.json();
}
```

---

## 其他方案备选

### 备选 1: Electron + Python

如果团队:
- 已有 Electron 经验
- 需要复杂桌面功能
- 不在意体积

### 备选 2: PyWebView + Flask

如果:
- 内部工具
- 追求最小体积
- 不需要复杂功能

### 备选 3: 保持 PyQt

当前 PyQt 方案:
- 成熟稳定
- 功能完整
- 可用 PyInstaller 打包

缺点:
- 非 Web 技术栈
- 维护成本高

---

## 参考资料

- [Tauri 官方文档](https://tauri.app/)
- [Tauri 中文网](https://www.tauri.net.cn/)
- [Tauri 最佳实践：企业级应用开发指南](https://m.blog.csdn.net/gitblog_00754/article/details/150616671)
- [2025 Angular桌面应用终极抉择：Electron与Tauri深度测评](https://m.blog.csdn.net/gitblog_00652/article/details/153610283)
- [WebView 桌面应用全景对比](https://juejin.cn/post/7605128056485953551)
- [跨平台框架全景对比 2026](https://juejin.cn/post/7602133286643220530)
- [Tauri vs Electron 2026 对比](https://m.toutiao.com/article/7609322393777013275/)
- [Python+Tauri 桌面开发实战](https://www.toutiao.com/article/7550873875156861491/)
- [Flet vs Tauri vs Electron 对比](https://m.blog.csdn.net/qq_21460781/article/details/156801997)
- [FastAPI+Tauri封神！轻量框架逆袭](https://m.toutiao.com/a7609333298275369499/)
- [PyTauri: Python 官方绑定](https://github.com/pytauri/pytauri)

---

## 2025-2026 技术更新

### Tauri 2.0 新特性

| 特性 | 说明 |
|------|------|
| 平台支持 | Windows 7+, macOS 10.15+, Linux (webkit2gtk 4.1+), iOS, Android |
| 内置功能 | App bundler, 自更新, 托盘图标, 原生通知 |
| 安全架构 | CSP 配置, 权限系统, 隔离架构 |
| 无需 HTTP 服务器 | 使用原生 WebView 协议 |

### Tauri vs Electron 2025 对比

| 指标 | Electron | Tauri 2.0 | 胜者 |
|------|----------|-----------|------|
| 基础包大小 | ~150MB | ~5MB | Tauri |
| 启动速度 | 2-5秒 | 0.5-2秒 | Tauri |
| 内存占用 | 高 (完整 Chromium) | 低 (系统 WebView) | Tauri |
| API 丰富度 | ★★★★★ | ★★★☆☆ | Electron |
| 安全性 | 中等 | 高 (隔离架构) | Tauri |
| 生态成熟度 | ★★★★★ | ★★★★☆ | Electron |

### PyTauri 新方案

**PyTauri** 提供 Python 原生绑定 (通过 Pyo3):

```python
from pydantic import BaseModel
from pytauri import AppHandle, Commands

commands = Commands()

class Person(BaseModel):
    name: str

@commands.command()
async def greet(body: Person, app_handle: AppHandle) -> dict:
    return {"message": f"Hello, {body.name}!"}
```

**优势**:
- 无 IPC 开销 - 直接 Python 集成
- 自动生成 TypeScript 类型
- 支持异步 Python (asyncio, trio, anyio)
- 可用 Cython 保护源代码

**适用场景**: 如果不需要独立的 FastAPI 服务，PyTauri 是更好的选择

### FastAPI + Tauri 集成方案

如需保留现有 FastAPI 后端:

1. **配置后端地址**: 在 `src-tauri/tauri.conf.json` 中设置
2. **API 调用**: 使用 fetch 从 Tauri 前端调用 FastAPI 端点
3. **CORS 配置**: 在 FastAPI 中正确配置 CORS 中间件

```python
# FastAPI CORS 配置
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["tauri://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 企业级安全最佳实践

```json
// tauri.conf.json 安全配置
{
  "security": {
    "csp": "default-src 'self'; script-src 'self' 'unsafe-inline'"
  }
}
```

**安全原则**:
- 使用命令作用域限制访问
- 实现基于能力的访问控制
- 遵循最小权限原则
- 防止 XSS 和远程代码执行
