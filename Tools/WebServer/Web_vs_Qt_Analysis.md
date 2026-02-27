# Web 版本与 Qt 版本差异全面分析与改造计划

## 1. 现状概述

*   **Qt 版本 (AiNiee Desktop)**: 功能完备，侧重于精细化的“配置”与“工具流”。拥有完整的提示词管理（分角色、世界观、风格等）、数据表管理（术语、排除、替换）、以及 StevExtraction 工具箱（导入导出）。
*   **Web 版本 (AiNiee Control Center)**: 侧重于“运行”与“监控”。核心功能围绕 Dashboard（仪表盘）、TaskRunner（任务运行）、Monitor（监控）展开。UI 风格较为独立，拥有独特的主题系统（Elysia 等），但缺乏 Qt 版本的深度配置能力。

## 2. 功能差距分析 (Gap Analysis)

| 功能模块 | Qt 版本特性 | Web 版本现状 | 差距/缺失 |
| :--- | :--- | :--- | :--- |
| **导航/布局** | Fluent UI，多级菜单，侧边栏分类清晰（快速开始、任务配置、高级设置、提示词、数据表、工具箱）。 | 自定义 Sidebar，单层结构，混合了运行与配置。 | **结构混乱**：Web 版缺乏层级，功能堆砌。需要按 Qt 的逻辑重组菜单。 |
| **任务配置** | 任务设置、输出设置。 | 只有 Settings 页面，可能不够细化。 | **配置深度**：需要检查 Settings 是否包含 Output 相关的详细配置。 |
| **翻译设置** | 翻译设置、润色设置、插件设置。 | Plugins 页面存在，但翻译/润色设置可能混杂。 | **缺失**：独立的润色设置页面。 |
| **提示词管理** | **极度细化**：基础、角色、背景、风格、示例（翻译/润色双套）。 | 只有一个 Prompts 页面。 | **颗粒度**：Web 版需要拆分 Prompts 页面，支持多维度的提示词管理。 |
| **数据表** | 术语表、禁翻表、译前替换、译后替换。 | 只有一个 Rules 页面。 | **功能缺失**：需要确认 Rules 是否支持所有类型的表（尤其是译前/译后区分）。 |
| **工具箱** | StevExtraction (导出原文/导入译文/导出增量)。 | **完全缺失**。 | **重大缺失**：Web 版无法进行文件的前处理和后处理，只能运行任务。 |
| **监控/运行** | 基础的进度显示。 | **强项**：Dashboard, Monitor, Scheduler, Queue。 | Web 版在此处优于 Qt 版，应保留并强化。 |

## 3. UI/UX 改造目标

*   **框架迁移**: 从自定义 CSS/Tailwind 迁移至 **Shadcn UI** (基于 Radix UI + Tailwind)。
*   **布局重构**: 采用类似 Qt 的 "Sidebar + Header + Content" 布局，但更现代化。
*   **主题系统**: 保留现有的特色主题（Elysia, Mobius 等），但通过 Shadcn 的 CSS Variables 实现更平滑的切换。
*   **交互优化**: 使用 Dialog、Sheet、Popover 等组件提升配置体验，避免页面频繁跳转。

## 4. 改造实施计划

### 第一阶段：基础设施搭建 (本次执行)
1.  安装 Shadcn UI 核心依赖 (`clsx`, `tailwind-merge`, `class-variance-authority`, `lucide-react`, `@radix-ui/*`)。
2.  配置 `tailwind.config.js` 和 `globals.css` 以支持 CSS 变量主题。
3.  创建基础 UI 组件库 (`components/ui/*`)。
4.  实现全新的 Layout 组件 (`MainLayout`)，复刻 Qt 的菜单结构。

### 第二阶段：核心页面迁移
1.  **Dashboard**: 迁移现有仪表盘，使用 Card 和 Chart 组件重写。
2.  **Settings**: 将单一的 Settings 拆分为 "应用"、"任务"、"输出" 等 Tab 或子页面。
3.  **Prompts**: 重构 Prompts 页面，支持 Tab 切换（System, User, Style, etc.）。

### 第三阶段：功能补全
1.  **Data Tables**: 将 Rules 页面改造为类似 Excel 的编辑体验（使用 `@tanstack/react-table`）。
2.  **StevExtraction**: 实现文件上传/下载接口，对接后端 Python API（可能需要后端支持）。

## 5. 结论
Web 版本目前是一个优秀的“控制台”，但还不是一个完整的“工作台”。本次改造将致力于使其成为 Qt 版本的全功能 Web 替代品。
