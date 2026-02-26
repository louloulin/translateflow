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
- [ ] TUI 添加搜索对话框
- [ ] Web 添加在线编辑器 (Monaco Editor)
- [ ] Web 添加断点续传检测

### P2 (中优先级)
- [ ] TUI 添加定时任务 UI
- [ ] Web 添加定时任务 UI
- [ ] Qt 添加双语对照显示

## 当前迭代计划

首先修复最关键的配置问题，让双语对照功能正常工作。
