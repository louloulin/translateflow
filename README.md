# AiNiee CLI (Optimized Edition)

<div align="center">
  <img src="https://img.shields.io/badge/Interface-CLI%20%2F%20TUI-0078D4?style=for-the-badge&logo=windows-terminal&logoColor=white" alt="CLI">
  <img src="https://img.shields.io/badge/Runtime-uv-purple?style=for-the-badge&logo=python&logoColor=white" alt="uv">
  <img src="https://img.shields.io/badge/Status-Optimized-success?style=for-the-badge" alt="Status">
</div>

<br/>

[English](README_EN.md) | [简体中文](README.md)

**AiNiee CLI** 是针对 [AiNiee](https://github.com/NEKOparapa/AiNiee) 核心逻辑进行工程化重构的命令行版本。

本项目引入了现代化的 Python 包管理工具 **`uv`**，并对底层运行时进行了多项稳定性优化。通过接管底层 IO 流与异常处理，我们构建了一个适合长时间挂机、服务器部署及自动化工作流的高健壮性 TUI 环境。

> **🚧 提示**：为了降低环境配置难度，本项目深度集成 `uv`。后续版本将直接提供 `Launch.bat` 和 `Launch.sh` 一键启动脚本，敬请期待。

---

## ✨ 核心优化 (Key Optimizations)

### 🛡️ 运行时稳定性 (Runtime Stability)
*   **IO 流清洗与接管**：重构了标准输出流 (Stdout/Stderr) 的捕获逻辑，有效屏蔽了底层依赖库（如 TensorFlow/C++ Bindings）的冗余日志，防止 TUI 界面撕裂或崩溃，确保在 Headless 环境下的日志可读性。

### ⚙️ 流程与配置管理 (Workflow & Config)
*   **智能化格式输入/转换**：优化了输入处理管线，支持对非标准格式（.mobi/.azw3等）进行全自动的“识别 -> 转换 -> 翻译 -> 还原”闭环操作，大幅简化了前置处理步骤。
*   **多配置文件系统 (Profiles)**：引入 Profile 概念，支持创建、克隆、切换多套配置方案（如区分“快速翻译”与“精细润色”），所有配置隔离存储，互不干扰。
*   **实时任务指挥中心 (Live Mission Control)**： **[New]** 引入全新的 TUI 任务状态与控制中心，支持：
    *   **动态并发调整**：在任务运行时，通过键盘 `+` 和 `-` 键实时增减并发线程数。
    *   **API Key 热切换**：通过键盘 `K` 键强制触发 API Key 轮换，应对特定 API 的调用限制。
    *   **网页监控面板 [New]**：通过键盘 `M` 键立即启动后台 WebServer 并自动打开浏览器监控当前任务。此时 TUI 面板将进入托管模式，所有日志与状态将实时同步至网页端。
    *   **系统状态监控**：底部状态栏实时显示系统运行状态（正常/修复中/警告/错误）， 并联动改变面板边框颜色。
    *   **预估成本与时间**：任务启动前，自动预估本次任务的总 Token 消耗、在线 API 预估费用及预计完成时间（ETA），并在日志窗格中醒目提示（仅供参考）。
*   **可视化交互体验**：基于 `Rich` 构建的现代化 TUI，提供实时性能监控（RPM/TPM）、双屏日志对照翻译及类 BIOS 的交互式设置菜单。
*   **[New] 插件化架构 (Plugin Architecture)**：
    *   引入了全新的插件系统，允许在不修改核心代码的情况下安全地扩展功能。
    *   **内置 RAG 插件**：附带一个开箱即用的 RAG（检索增强生成）上下文插件。启用后，系统会在翻译时自动检索历史译文，为长篇内容提供关键的上下文参考，显著提升术语和风格的一致性。
    *   **集中化管理**：CLI 主菜单和 Web UI 均提供独立的"插件管理"页面，支持一键启用/禁用所有已发现的插件。
*   **[New] 智能任务队列系统 (Task Queue System)**：
    *   **多模式队列管理**：支持在 TUI 交互式菜单和 WebServer 可视化界面中创建、编辑、删除翻译任务队列。
    *   **灵活队列调度**：支持动态调整队列顺序 - WebServer 界面提供鼠标拖拽排序，TUI 界面提供键盘交互式重排功能。
    *   **任务热修改**：在队列执行过程中，支持通过 WebServer 实时修改待处理任务的参数配置，无需停止当前运行的任务。所有队列变更将在 TUI 控制台中实时显示操作日志。
    *   **批处理优化**：允许预先配置多个不同文件或不同翻译策略的任务，系统将按顺序自动执行，适合大批量翻译工作流。
*   **[New] 思考模式增强 (Thinking Mode Enhancement)**：
    *   **全平台兼容**：修复了思考模式在多个 AI 平台上的兼容性问题，现已支持所有主流在线 API 平台及第三方中转站。
    *   **智能参数配置**：思考模式设置现在在所有界面中常驻显示，不再受平台条件限制，并为在线 API 和本地模型提供不同的兼容性警告提示。
    *   **统一界面体验**：修复了思考模式参数在 CLI 菜单和 Web 控制面板中的显示不一致问题，确保用户体验的统一性。

---

本项目提供多种启动方式，推荐根据你的使用场景选择最适合的方法。

## 🚀 方式一：一键启动（推荐）

### 1. 获取代码
```bash
git clone https://github.com/ShadowLoveElysia/AiNiee-CLI.git
cd AiNiee-CLI
```

### 2. 环境准备（首次运行）

**Windows:**
```batch
双击 prepare.bat
```

**Linux / macOS:**
```bash
chmod +x prepare.sh
./prepare.sh
```

Prepare 脚本会自动：
- 检测并安装 `uv`（如果未安装）
- 创建虚拟环境
- 安装所有项目依赖

### 3. 启动应用

环境准备完成后，每次启动只需：

**Windows:**
```batch
双击 Launch.bat
```

**Linux / macOS:**
```bash
./Launch.sh
```

---

## 🛠️ 方式二：手动配置（高级用户）

如果你希望手动配置环境，可以使用以下方法：

### 1. 安装 uv

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Linux / macOS:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Android (Termux) - 方式1 (直接安装):**
```bash
# 更新软件源
pkg update && pkg upgrade
# 安装Python（如果没有的话）
pkg install python
# 通过pip安装uv
pip install uv
```

**Android (Termux) - 方式2 (Proot-Distro Ubuntu):**
```bash
# 安装 proot-distro
pkg install proot-distro
# 安装 Ubuntu 环境
proot-distro install ubuntu
# 登录 Ubuntu 环境
proot-distro login ubuntu
# 在 Ubuntu 中安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

> **📱 Termux 用户提示**：对于移动设备，我们建议使用 **WebServer 模式配合在线 API** 获得最佳体验。Web 界面针对触摸交互和远程监控进行了优化。

### 2. 获取代码
```bash
git clone https://github.com/ShadowLoveElysia/AiNiee-CLI.git
cd AiNiee-CLI
```

### 3. 极速启动
无需手动创建虚拟环境或安装 pip 依赖，直接使用 `uv run` 即可自动处理环境并启动工具：

```bash
# 自动同步依赖并启动 CLI (交互式菜单)
uv run ainiee_cli.py
```

### 4. 控制台参数启动 (Non-Interactive CLI)
**[New]** 本项目支持通过命令行参数直接启动翻译或导出任务，适用于脚本集成与自动化。

**翻译任务示例：**
```bash
uv run ainiee_cli.py translate H:\小说\我的书.txt -o H:\小说\我的书_Output -p MyProfile -s Japanese -t Chinese --resume --yes
```

**队列任务示例：**
```bash
uv run ainiee_cli.py queue --queue-file H:\小说\my_queue.json --yes
```
**参数说明：**
*   `translate` / `polish` / `export` / `queue`: 指定任务类型。
*   `H:\小说\我的书.txt`: (位置参数) 输入文件或文件夹路径。
*   `-o, --output`: 指定输出路径。
*   `-p, --profile`: 指定配置 Profile 名称。
*   `-s, --source`: 指定源语言。
*   `-t, --target`: 指定目标语言。
*   `--type`: 指定项目类型 (如 `Txt`, `Epub`, `MTool`, `RenPy` 等)。
*   `--resume`: 如果检测到缓存，自动恢复任务。
*   `--yes`: 非交互模式，对所有确认提示自动回答 `yes`。
*   **[New] 高级参数覆盖：**
    *   `--threads`: 并发线程数。
    *   `--rounds`: 最大任务轮次。
    *   `--retry`: 单请求最大重试次数。
    *   `--timeout`: API 超时时间。
    *   `--platform`: 覆盖目标平台。
    *   `--model`: 覆盖模型名称。
    *   `--api-url`: 覆盖 API 地址。
    *   `--api-key`: 覆盖 API 密钥。
    *   `--lines` / `--tokens`: 覆盖单批处理量。
    *   `--pre-lines`: 上下文包含行数。
    *   `--failover`: `on/off` 切换故障转移。
    *   `--think-depth`: 思考模式深度级别（0-10000，0为禁用）。
    *   `--thinking-budget`: 思考模式 Token 预算限制。
    *   `--queue-file`: 指定任务队列 JSON 文件路径（仅适用于 `queue` 任务类型）。

---

## 📖 菜单功能概览

启动后，您将通过交互式菜单操作以下功能：

*   **Start Translation / Polishing**: 核心翻译与润色任务（支持自动断点续传）。
*   **Export Only**: 针对已有缓存的快速导出模式。
*   **Task Queue**: **[New]** 智能任务队列管理中心，支持批量任务配置与执行。
*   **Profiles**: **[New]** 配置方案切换与管理中心。
*   **Settings / API Settings**: 经过分类整理的参数设置，支持热重载。
*   **Glossary**: 提示词模板的预览与应用。
*   **Start Web Server**: **[New]** 启动现代化 Web 控制面板。

---

## 🌐 Web 控制面板 (Web Dashboard)

**[New]** 为了提供更直观的操作体验，本项目现已集成基于 React 构建的 Web 控制面板。

### 如何启动
1.  运行 `uv run ainiee_cli.py` 进入主菜单。
2.  选择 **12. Start Web Server**。
3.  程序将自动检测您的局域网 IP 并启动服务（默认端口 `8000`），同时在默认浏览器中打开页面。

### 功能亮点
*   **可视化看板**：实时图表展示 RPM、TPM 及任务进度。
*   **网络访问**：支持通过局域网 IP 远程监控翻译进度，您也可以配合内网穿透工具（如 `frp`, `cloudflared`）进行外网映射访问。
*   **配置管理**：直接在网页端创建、重命名、删除或切换配置 Profile，实时同步至后端。
*   **[New] 队列管理中心**：提供直观的队列管理界面，支持鼠标拖拽重新排序任务、实时编辑任务参数、添加删除队列项目，所有操作均会在 TUI 控制台同步显示日志。
*   **[New] 思考模式配置**：完整的思考模式参数配置界面，提供针对不同 AI 平台的兼容性提示和优化建议。
*   **[New] 插件中心**：在 Web UI 中提供独立的插件管理页面，允许用户通过卡片式界面直观地启用或禁用 RAG 等高级功能。
*   **状态恢复**：支持页面刷新后自动同步后端任务状态、日志及图表历史。

> **⚠️ 重要提示**：
> **Web 控制面板目前处于 Beta 测试阶段，部分设备（如手机端浏览器）可能兼容性不佳。若您需要绝佳的运行稳定性（如超大规模任务挂机），请务必继续使用原生 TUI 模式执行任务。**

---

## 🛠️ 架构说明

本项目采用了 **Wrapper / Adapter** 模式：

*   **Core**: 保持原版 AiNiee 的核心业务逻辑不变。
*   **Adapter Layer**: `ainiee_cli.py` 作为防腐层，负责环境隔离、异常拦截与资源调度。
*   **Runtime**: 由 `uv` 托管，确保依赖环境的一致性与启动速度。

---

## ⚠️ 免责声明

*   本项目是 AiNiee 的非官方 CLI 优化分支，侧重于运行体验与工程稳定性。
*   核心翻译算法与原版保持一致，请遵守原版的使用协议。
*   本工具仅供个人学习与合法用途使用。

---

<div align="center">
  Made with 💻 and ☕ by ShadowLoveElysia
  <br>
  Based on the original work by NEKOparapa
</div>
```
