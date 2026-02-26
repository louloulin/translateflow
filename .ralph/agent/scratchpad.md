# AiNiee-Next 代码分析与改造 - Scratchpad

## 当前理解

这是一个 AiNiee-Next 项目的代码分析和改造任务。项目有三个版本：
1. **Qt GUI 版本** (`source/AiNiee/`) - PyQt5 + qfluentwidgets
2. **CLI/TUI 版本** (`ModuleFolders/`) - Rich TUI
3. **Web 版本** (`Tools/WebServer/`) - React + FastAPI

## 核心问题发现

### 双语对照功能未生效的根本原因
1. **配置默认值问题**: `enable_bilingual_output` 在 `Resource/platforms/preset.json` 中默认为 `false`
2. **插件未默认启用**: `BilingualPlugin.default_enable = False`
3. **代码实现差异**: 当前版本比 Source 版本多了 `native_bilingual_types` 检查逻辑

### 功能对比总结
- **TUI/Web 已超越 Qt**: 有实时双语对照显示，Qt 没有
- **Qt 优势**: 波形图、进度环、搜索对话框、定时任务 UI
- **TUI 优势**: 诊断系统、自动化功能、AI 校对
- **Web 优势**: 现代化架构、跨平台、实时轮询

## 行动计划

### P0 (最高优先级)
- [x] 修复双语配置默认值 (`enable_bilingual_output: true`) - ✅ 已完成
  - 修改了 `default_config.py:56`
  - 修改了 `TaskConfig.py:107`
  - 已提交: abaf7a4

### P1 (高优先级)
- [x] TUI 添加搜索对话框 - ✅ 已完成
  - 在 TUIEditor 中添加 '/' 快捷键触发搜索
  - SearchDialog 已实现完整搜索功能
  - 更新 i18n 文件添加搜索快捷键提示
  - 已提交: 84fa1ab
- [x] Web 添加在线编辑器 (Monaco Editor) - ✅ 已存在
  - 组件已存在于 components/MonacoEditor.tsx
  - CacheEditor.tsx 已集成 MonacoInlineEditor
  - 支持 Monaco/Basic 模式切换
  - commit: 4268deb
- [x] Web 添加断点续传检测 - ✅ 已完成
  - 在 Dashboard 页面添加断点检测横幅
  - 使用后端 /api/task/breakpoint-status 接口
  - 显示项目名称、进度和继续按钮
  - 已提交: 11b8777

### P2 (中优先级)
- [x] TUI 添加定时任务 UI - ✅ 已存在
  - AutomationMenu.py 有完整的 scheduler_submenu
  - 支持 add/edit/remove scheduled tasks
  - 使用 SchedulerManager 后端
- [x] Web 添加定时任务 UI - ✅ 已完成 (2026-02-27)
  - 在 web_server.py 添加 scheduler API endpoints
  - 创建 Scheduler.tsx 页面组件
  - 添加完整的 CRUD 操作
  - 支持启动/停止调度器和查看日志
  - 已提交: 690a064
- [ ] Qt 添加双语对照显示

## 本迭代完成 (2026-02-27)

**完成任务**: Web 添加定时任务 UI

### 实现内容
1. **后端 API** (web_server.py):
   - 添加 8 个 scheduler 相关的 API endpoints
   - 集成 SchedulerManager 后端
   - 支持任务 CRUD 和调度器控制

2. **前端组件** (Scheduler.tsx):
   - 定时任务列表展示
   - 添加/编辑任务模态框
   - 启用/禁用任务切换
   - 调度器启动/停止控制
   - 执行日志查看

3. **数据服务** (DataService.ts):
   - 添加 scheduler API 调用方法
   - 错误处理和类型定义

4. **导航和翻译**:
   - App.tsx 添加路由和侧边栏导航项
   - constants.ts 添加完整的中英文翻译

### 下一步行动
- 实现 Qt 双语对照显示 (P2 剩余任务)

## 本迭代计划 (2026-02-27)

**任务**: Qt 添加双语对照显示

### 实现方案
基于 TUI/Web 的双语对照实现，为 Qt MonitoringPage 添加双语对照组件：

1. **创建 BilingualCard widget** (`source/AiNiee/UserInterface/Widget/BilingualCard.py`)
   - 双栏布局：原文栏 (magenta) + 译文栏 (green)
   - 滚动文本显示
   - 行数统计显示
   - 固定高度: 204px (与其他卡片一致)
   - 固定宽度: 833px (相当于2列卡片宽度)

2. **更新 MonitoringPage** (`source/AiNiee/UserInterface/EditView/Monitoring/MonitoringPage.py`)
   - 添加 BilingualCard 到页面布局
   - 订阅 `TUI_SOURCE_DATA` 和 `TUI_RESULT_DATA` 事件
   - 实现 `on_source_data` 和 `on_result_data` 方法

3. **数据流分析**
   - `TranslatorTask.py:376` 发射 `TUI_RESULT_DATA` 事件
   - 数据格式: `{"source": all_source, "data": all_trans}`
   - 需要在 MonitoringPage 接收并更新 BilingualCard

### 实现细节
- 使用 `QTextEdit` 或 `QPlainTextEdit` 显示双语文本
- 原文: magenta 颜色 (#FF00FF)
- 译文: green 颜色 (#00FF00)
- 标题栏显示行数统计
- 支持 "Waiting..." 默认文本
