# AiNiee-Next 代码分析与改造计划

## 一、项目概述

### 1.1 项目背景
AiNiee-Next 是 AiNiee 项目的一个硬分支，进行了工程化重构。主要特点包括：
- 原始项目：PyQt5 GUI 版本（位于 `source/AiNiee/`）
- 重构版本：CLI/TUI 版本（位于 `ModuleFolders/` 和 `ainiee_cli.py`）
- Web 版本：React + FastAPI 实现（位于 `Tools/WebServer/`）

### 1.2 技术栈
- **后端**: Python 3.12, FastAPI, uvicorn, uv 包管理器
- **前端**: React, TypeScript, Vite, Elysia UI 框架
- **TUI**: Rich 库
- **LLM 支持**: 18+ 平台（OpenAI, Anthropic, Google, Cohere 等）
- **文件格式**: 25+ 种格式支持

---

## 二、双语对照功能分析

### 2.1 双语对照实现机制

#### 核心代码位置
1. **BilingualPlugin**: `/PluginScripts/BilingualPlugin/BilingualPlugin.py`
2. **FileOutputer**: `/ModuleFolders/Domain/FileOutputer/`
3. **配置**: `enable_bilingual_output` 和 `bilingual_text_order`

#### 工作流程
```
翻译完成 → postprocess_text 事件 → BilingualPlugin 处理 → 文件输出
```

#### 代码分析
```python
# BilingualPlugin.py 关键逻辑
def process_dictionary_list(self, event_data: CacheProject):
    native_bilingual_types = {
        ProjectType.TXT,
        ProjectType.EPUB,
        ProjectType.SRT,
        ProjectType.BABELDOC_PDF,
    }

    for file in event_data.files.values():
        # 跳过原生支持双语的文件类型
        if file.file_project_type in native_bilingual_types:
            continue

        for entry in file.items:
            if translation_status == TranslationStatus.TRANSLATED:
                entry.translated_text = translated_text + "\n" + source_text
```

### 2.2 双语对照未生效的根本原因分析（深度调查结果）

#### 🔴 核心问题：配置默认值
- **最关键原因**: `enable_bilingual_output` 在 `Resource/platforms/preset.json` 中默认为 `false`
- 当前配置值: `false`, `bilingual_text_order`: `"translation_first"`

#### 原因 1: 插件未启用
- `BilingualPlugin.default_enable = False`
- 需要用户手动启用插件

#### 原因 2: 代码实现差异（关键发现）

**当前版本 BilingualPlugin (PluginScripts/BilingualPlugin/BilingualPlugin.py):**
```python
def process_dictionary_list(self, event_data: CacheProject):
    native_bilingual_types = {
        ProjectType.TXT, ProjectType.EPUB, ProjectType.SRT, ProjectType.BABELDOC_PDF
    }
    for file in event_data.files.values():
        if file.file_project_type in native_bilingual_types:
            continue  # 跳过原生双语类型
```

**Source版本 BilingualPlugin (source/AiNiee/PluginScripts/BilingualPlugin/BilingualPlugin.py):**
```python
def process_dictionary_list(self, event_data: CacheProject):
    for entry in event_data.items_iter():  # 直接处理所有条目
        if translation_status == TranslationStatus.TRANSLATED:
            entry.translated_text = translated_text + "\n" + source_text
```

#### 原因 3: FileOutputer 实现差异（关键发现）

**当前版本 (ModuleFolders/Domain/FileOutputer/FileOutputer.py:145):**
```python
enable_bilingual = config.get("enable_bilingual_output", False)  # 从配置读取，默认 False
bilingual_config=TranslationOutputConfig(enable_bilingual, ...)  # 使用变量
```

**Source版本 (source/AiNiee/ModuleFolders/Domain/FileOutputer/FileOutputer.py:134):**
```python
bilingual_config=TranslationOutputConfig(True, ...)  # 硬编码为 True！
```

#### 原因 4: TaskExecutor 配置差异

**当前版本输出配置 (ModuleFolders/Service/TaskExecutor/TaskExecutor.py:673-679):**
```python
output_config = {
    "translated_suffix": self.config.output_filename_suffix,
    "bilingual_suffix": "_bilingual",
    "bilingual_order": self.config.bilingual_text_order,
    "enable_bilingual_output": self.config.enable_bilingual_output  # 新增配置项
}
```

**Source版本输出配置 (source/AiNiee/ModuleFolders/Service/TaskExecutor/TaskExecutor.py:337-341):**
```python
output_config = {
    "translated_suffix": self.config.output_filename_suffix,
    "bilingual_suffix": "_bilingual",
    "bilingual_order": self.config.bilingual_text_order
    # 注意：没有 enable_bilingual_output 配置项
}
```

### 2.3 双语对照配置路径

#### 文件层配置 (FileOutputer)
```python
# FileOutputer.py:145
enable_bilingual = config.get("enable_bilingual_output", False)

# FileOutputer.py:158
bilingual_config=TranslationOutputConfig(enable_bilingual, bilingual_suffix, output_path / "bilingual_srt")
```

#### Writer 层实现
- **TxtWriter**: `_item_to_bilingual_line` 方法处理双语行格式
- **SrtWriter**: `_yield_bilingual_block` 生成双语字幕块
- **EpubWriter**: `_rebuild_bilingual_tag` 重建双语 HTML 标签
- **AssWriter**: `_yield_bilingual_lines` 生成双语 ASS 字幕

---

## 三、source/AiNiee vs ModuleFolders 功能对比

### 3.1 共同功能（两者都实现）

| 功能 | source/AiNiee | ModuleFolders | 状态 |
|------|---------------|---------------|------|
| 核心 ModuleFolders 架构 | ✓ | ✓ | 完全相同 |
| 双语对照支持 | ✓ | ✓ | 实现相同 |
| 插件系统 | ✓ | ✓ | 完全相同 |
| 25+ 文件格式读写 | ✓ | ✓ | 完全相同 |
| 18+ LLM 平台支持 | ✓ | ✓ | 完全相同 |
| 任务执行器 | ✓ | ✓ | 核心逻辑相同 |
| 缓存系统 | ✓ | ✓ | 完全相同 |
| 限流控制 | ✓ | ✓ | 完全相同 |

### 3.2 source/AiNiee 独有功能（GUI 版本）

| 功能模块 | 描述 | 文件位置 |
|----------|------|----------|
| **PyQt5 GUI** | 完整图形用户界面 | `source/AiNiee/UserInterface/` |
| **qfluentwidgets** | 现代化 UI 组件库 | `source/AiNiee/UserInterface/Widgets/` |
| **EditView 页面** | 翻译编辑器主界面 | `source/AiNiee/UserInterface/EditView/` |
| **设置页面** | 20+ 设置页面 | `source/AiNiee/UserInterface/Settings/` |
| **StevExtraction 工具** | RPG Maker 游戏提取 | `source/AiNiee/StevExtraction/` |
| **平台管理 UI** | API 管理图形界面 | `source/AiNiee/UserInterface/APIManagement/` |
| **模型浏览器** | 模型选择对话框 | `source/AiNiee/UserInterface/APIManagement/ModelBrowserDialog.py` |
| **版本管理器** | 自动更新 UI | `source/AiNiee/UserInterface/VersionManager/` |
| **计时器对话框** | 定时任务设置 | `source/AiNiee/UserInterface/EditView/Timer/` |
| **搜索功能** | 全文搜索 UI | `source/AiNiee/UserInterface/EditView/Search/` |

### 3.3 ModuleFolders 独有功能（CLI/TUI 版本）

| 功能模块 | 描述 | 文件位置 |
|----------|------|----------|
| **Rich TUI** | 终端用户界面 | `ModuleFolders/UserInterface/` |
| **TUIEditor** | 交互式终端编辑器 | `ModuleFolders/UserInterface/Editor/TUIEditor.py` |
| **ProofreadTUI** | 校对界面 | `ModuleFolders/UserInterface/Proofreader/ProofreadTUI.py` |
| **TaskUI** | 任务进度显示 | `ModuleFolders/UserInterface/TaskUI.py` |
| **TermSelector** | 术语选择 TUI | `ModuleFolders/UserInterface/TermSelector/TermSelector.py` |
| **FileSelector** | 文件选择 TUI | `ModuleFolders/UserInterface/FileSelector.py` |
| **诊断系统** | SmartDiagnostic | `ModuleFolders/Diagnostic/` |
| **自动化功能** | WatchManager, SchedulerManager | `ModuleFolders/Infrastructure/Automation/` |
| **GlossaryAnalysis** | 术语分析服务 | `ModuleFolders/Service/GlossaryAnalysis/` |
| **AIProofreader** | AI 校对服务 | `ModuleFolders/Service/Proofreader/` |
| **OperationLogger** | 操作日志 | `ModuleFolders/CLI/OperationLogger.py` |

### 3.4 Tools/WebServer 独有功能（Web 版本）

| 功能模块 | 描述 | 文件位置 |
|----------|------|----------|
| **FastAPI 后端** | Web 服务 | `Tools/WebServer/web_server.py` |
| **React 前端** | 现代化 Web UI | `Tools/WebServer/App.tsx` |
| **TaskManager** | 任务状态管理 | `Tools/WebServer/web_server.py:35` |
| **实时对照** | 双语对照显示 | `Tools/WebServer/pages/Monitor.tsx` |
| **缓存编辑器** | 缓存数据编辑 | `Tools/WebServer/pages/CacheEditor.tsx` |
| **主题系统** | 15+ UI 主题 | `Tools/WebServer/components/Themes/` |
| **规则配置** | 规则文件管理 | `Tools/WebServer/pages/Rules.tsx` |
| **插件管理** | 插件启用/禁用 | `Tools/WebServer/pages/Plugins.tsx` |
| **提示词管理** | Prompt 配置 | `Tools/WebServer/pages/Prompts.tsx` |
| **任务队列** | 队列管理界面 | `Tools/WebServer/pages/TaskQueue.tsx` |

---

## 四、功能缺失分析

### 4.1 CLI/TUI 版本缺失的功能

| 功能 | 优先级 | 原因 | 实现难度 |
|------|--------|------|----------|
| **StevExtraction 工具** | 低 | RPG Maker 专用，小众需求 | 中 |
| **模型浏览器** | 中 | 需要调用各平台 API 获取模型列表 | 高 |
| **版本更新 UI** | 中 | CLI 可以用 UpdateManager | 低 |
| **搜索功能** | 低 | 可以用 grep 替代 | 低 |
| **定时任务 UI** | 中 | 已有 SchedulerManager，缺 UI | 中 |

### 4.2 Web 版本缺失的功能

| 功能 | 优先级 | 原因 | 实现难度 |
|------|--------|------|----------|
| **StevExtraction** | 低 | 同上 | 中 |
| **文件选择器** | 中 | Web 文件上传支持有限 | 中 |
| **TUI 风格交互** | 低 | Web 有自己的交互模式 | - |

### 4.3 GUI 版本缺失的功能

| 功能 | 优先级 | 原因 | 实现难度 |
|------|--------|------|----------|
| **诊断系统** | 中 | 新增功能，GUI 没有实现 | 中 |
| **自动化功能** | 中 | 新增功能 | 中 |
| **GlossaryAnalysis** | 中 | 新增功能 | 中 |
| **AIProofreader** | 中 | 新增功能 | 中 |

---

## 五、双语对照修复方案

### 5.1 短期修复（立即可行）

#### 方案 1: 检查配置
```bash
# 检查当前配置
cat Resource/platforms/preset.json | grep bilingual

# 确保 enable_bilingual_output 为 true
# 确保 bilingual_text_order 设置正确
```

#### 方案 2: 启用插件
```python
# 在启动时启用 BilingualPlugin
plugin_manager.update_plugins_enable({
    "BilingualPlugin": True
})
```

#### 方案 3: 验证事件触发
在 `TaskExecutor.py:656` 确认 `postprocess_text` 事件被触发：
```python
self.plugin_manager.broadcast_event("postprocess_text", self.config, self.cache_manager.project)
```

### 5.2 中期改进（需要代码修改）

#### 改进 1: 统一双语配置
- 将 `enable_bilingual_output` 和插件启用状态解耦
- 配置文件中明确双语输出选项

#### 改进 2: 增强 Web 界面双语支持
- 在 Web 界面添加双语对照显示
- 实时更新双语对照数据

#### 改进 3: 添加双语输出验证
- 添加单元测试验证双语输出
- 添加双语文件生成后的验证逻辑

### 5.3 长期优化（架构层面）

#### 优化 1: 统一双语处理机制
- 将双语处理逻辑集中在 `FileOutputer` 层
- 减少 `BilingualPlugin` 的职责

#### 优化 2: 支持更多格式双语
- 扩展 `native_bilingual_types` 列表
- 为更多格式添加双语支持

---

## 六、后续改造计划

### 6.1 第一阶段：双语对照修复（优先级：高）

#### 任务清单
- [ ] 调查双语对照未生效的具体原因
- [ ] 修复配置问题
- [ ] 验证事件触发机制
- [ ] 添加双语输出测试
- [ ] 更新文档说明双语配置

#### 预计工作量
- 调查分析：4 小时
- 修复实现：6 小时
- 测试验证：4 小时
- 文档更新：2 小时
- **总计：16 小时**

### 6.2 第二阶段：TUI 功能增强（优先级：中）

#### 任务清单
- [ ] 添加模型浏览器 UI
- [ ] 添加定时任务配置 UI
- [ ] 改进术语选择器
- [ ] 添加搜索功能 UI
- [ ] 添加版本更新提示 UI

#### 预计工作量
- 模型浏览器：8 小时
- 定时任务 UI：6 小时
- 术语选择器改进：4 小时
- 搜索功能：4 小时
- 版本更新 UI：4 小时
- **总计：26 小时**

### 6.3 第三阶段：Web 功能完善（优先级：中）

#### 任务清单
- [ ] 改进双语对照实时显示
- [ ] 添加文件上传支持
- [ ] 改进缓存编辑器
- [ ] 添加更多配置项
- [ ] 添加双语文件预览

#### 预计工作量
- 双语对照显示：6 小时
- 文件上传：8 小时
- 缓存编辑器：6 小时
- 配置项：4 小时
- 文件预览：6 小时
- **总计：30 小时**

### 6.4 第四阶段：功能整合与优化（优先级：低）

#### 任务清单
- [ ] 整合 StevExtraction 到 CLI/TUI
- [ ] 添加诊断系统到 GUI
- [ ] 添加自动化功能到 GUI
- [ ] 添加 GlossaryAnalysis 到 GUI
- [ ] 添加 AIProofreader 到 GUI

#### 预计工作量
- StevExtraction 整合：8 小时
- 诊断系统 GUI：6 小时
- 自动化功能 GUI：6 小时
- GlossaryAnalysis GUI：4 小时
- AIProofreader GUI：6 小时
- **总计：30 小时**

---

## 七、技术债务与建议

### 7.1 代码重复问题
- `source/AiNiee` 和 `ModuleFolders` 存在大量重复代码
- 建议提取公共逻辑到共享库

### 7.2 配置管理
- 多处配置文件（preset.json, default_config.py）
- 建议统一配置管理

### 7.3 测试覆盖
- 缺少单元测试
- 建议添加测试覆盖，特别是双语输出

### 7.4 文档完整性
- 部分功能缺少文档
- 建议完善 API 文档和用户手册

### 7.5 性能优化
- 异步请求已实现，但可以进一步优化
- 建议添加性能监控和优化

---

## 八、结论

### 8.1 核心发现
1. **双语对照功能已实现**，但可能因配置问题未生效
2. **三个版本功能基本完整**，各有特色
3. **CLI/TUI 版本功能更丰富**，包含诊断、自动化等新功能
4. **Web 版本架构现代化**，使用 React + FastAPI

### 8.2 建议优先级
1. **修复双语对照配置问题**（高优先级）
2. **完善 Web 界面功能**（中优先级）
3. **增强 TUI 功能**（中优先级）
4. **功能整合**（低优先级）

### 8.3 下一步行动
1. 立即调查双语对照未生效的具体原因
2. 创建修复方案并实施
3. 添加测试验证修复
4. 更新文档

---

## 九、详细功能对比矩阵（补充）

### 9.1 双语对照功能对比

| 特性 | Source GUI | ModuleFolders CLI/TUI | Web 版本 |
|------|------------|----------------------|----------|
| **BilingualPlugin** | 简单实现（无native_bilingual检查） | 完整实现（有类型检查） | 无插件 |
| **enable_bilingual_output** | 无配置项，硬编码True | 从配置读取，默认False | 从配置读取 |
| **FileOutputer双语配置** | 硬编码 `TranslationOutputConfig(True, ...)` | 从配置读取 `enable_bilingual` | 从配置读取 |
| **原生双语格式** | TXT, EPUB, SRT, PDF | TXT, EPUB, SRT, PDF | TXT, EPUB, SRT, PDF |
| **双语排序** | `bilingual_order` 配置 | `bilingual_order` 配置 | `bilingual_order` 配置 |
| **双语文件输出** | 自动生成双语版本 | 需要配置启用 | 需要配置启用 |
| **插件启用机制** | 需手动启用 | 需手动启用 | 需手动启用 |

### 9.2 核心架构对比

| 层级 | Source GUI | ModuleFolders CLI/TUI | Web 版本 |
|------|------------|----------------------|----------|
| **UI 框架** | PyQt5 + qfluentwidgets | Rich TUI | React + Elysia UI |
| **后端** | Python (单进程) | Python (支持异步) | FastAPI + uvicorn |
| **插件系统** | ✓ 完全相同 | ✓ 完全相同 | ✓ 完全相同 |
| **文件格式支持** | ✓ 25+ 格式 | ✓ 25+ 格式 | ✓ 25+ 格式 |
| **LLM 平台支持** | ✓ 18+ 平台 | ✓ 18+ 平台 | ✓ 18+ 平台 |
| **诊断系统** | ✗ 未实现 | ✓ SmartDiagnostic | ✗ 未实现 |
| **自动化功能** | ✗ 未实现 | ✓ Watch/Scheduler | ✗ 未实现 |
| **术语分析** | 基础支持 | ✓ GlossaryAnalysis | 基础支持 |
| **AI 校对** | 基础支持 | ✓ AIProofreader | 基础支持 |

### 9.3 代码实现差异总结

#### BilingualPlugin 差异
```python
# Source 版本（简单）
for entry in event_data.items_iter():
    entry.translated_text = translated_text + "\n" + source_text

# 当前版本（复杂）
native_bilingual_types = {TXT, EPUB, SRT, PDF}
for file in event_data.files.values():
    if file.file_project_type in native_bilingual_types:
        continue  # 跳过
    for entry in file.items:
        entry.translated_text = translated_text + "\n" + source_text
```

#### FileOutputer 差异
```python
# Source 版本（硬编码启用）
bilingual_config=TranslationOutputConfig(True, bilingual_suffix, output_path / "bilingual_srt")

# 当前版本（配置驱动）
enable_bilingual = config.get("enable_bilingual_output", False)
bilingual_config=TranslationOutputConfig(enable_bilingual, bilingual_suffix, ...)
```

### 9.4 配置文件对比

| 配置项 | Source GUI | ModuleFolders CLI/TUI | Web 版本 | 默认值 |
|--------|------------|----------------------|----------|--------|
| enable_bilingual_output | 无配置项 | preset.json 中存在 | preset.json 中存在 | **false** |
| bilingual_text_order | ✓ | ✓ | ✓ | translation_first |
| bilingual_suffix | ✓ | ✓ | ✓ | _bilingual |
| bilingual_order | ✓ | ✓ | ✓ | source_first |

---

**文档版本**: 1.1
**创建日期**: 2026-02-26
**最后更新**: 2026-02-26 (补充深度代码对比)

---

## 十、核心翻译功能深度分析（2026-02-26 新增）

### 10.1 Qt (source/AiNiee) 核心翻译功能解析

#### 10.1.1 EditViewPage 核心功能
**文件位置**: `source/AiNiee/UserInterface/EditView/EditViewPage.py`

**核心特性**:
1. **BottomCommandBar (底部命令栏)**
   - 开始翻译/开始润色按钮（可切换模式）
   - 继续按钮（断点续传）
   - 停止按钮
   - 定时任务按钮
   - 导出结果按钮
   - 项目名称显示
   - 进度条和状态显示
   - 实时更新定时器（每秒刷新）

2. **事件驱动更新机制**
   ```python
   # 订阅事件
   self.subscribe(Base.EVENT.TASK_UPDATE, self.data_update)
   self.subscribe(Base.EVENT.TASK_STOP_DONE, self.task_stop_done)
   self.subscribe(Base.EVENT.APP_SHUT_DOWN, self.app_shut_down)

   # UI更新定时器
   self.ui_update_timer.timeout.connect(lambda: self.emit(Base.EVENT.TASK_UPDATE, {}))
   ```

3. **进度显示**
   - 进度条百分比
   - 当前进度/总行数（例如 "15/100"）

#### 10.1.2 MonitoringPage 监控页面
**文件位置**: `source/AiNiee/UserInterface/EditView/Monitoring/MonitoringPage.py`

**核心组件**:
1. **DashboardCard** - 数据卡片
   - 累计时间（Time）
   - 剩余时间（Time）
   - 平均速度（T/S）
   - 累计消耗（Token）
   - 实时任务数
   - 任务稳定性（%）

2. **CombinedLineCard** - 行数统计卡片
   - 已完成行数
   - 剩余行数
   - 双列显示

3. **ProgressRingCard** - 进度环
   - 圆形进度显示
   - 任务进度百分比

4. **WaveformCard** - 波形图
   - 实时速度波形
   - 可配置网格线

5. **实时数据更新**
   ```python
   # 监听任务更新事件
   self.subscribe(Base.EVENT.TASK_UPDATE, self.data_update)
   self.subscribe(Base.EVENT.TASK_COMPLETED, self.data_update)
   ```

#### 10.1.3 StartupPage 启动页面
**文件位置**: `source/AiNiee/UserInterface/EditView/Startup/StartupPage.py`

**核心功能**:
1. **项目类型选择** - ComboBoxCard
2. **文件夹拖放** - FolderDropCard
3. **继续项目** - ActionCard（显示上次项目）
4. **异步加载** - 子线程加载项目，信号通知主线程
   ```python
   folderSelected = pyqtSignal(str, str)  # 文件夹已选好
   loadSuccess = pyqtSignal(str, str)     # 加载成功
   loadFailed = pyqtSignal(str)           # 加载失败
   ```

---

### 10.2 TUI (ModuleFolders) 核心翻译功能解析

#### 10.2.1 TUIEditor 交互式编辑器
**文件位置**: `ModuleFolders/UserInterface/Editor/TUIEditor.py`

**核心特性**:
1. **双栏对照布局**
   ```python
   self.layout["body"].split_row(
       Layout(name="source_pane"),
       Layout(name="target_pane")
   )
   ```

2. **模式切换**
   - VIEW: 查看模式（只读）
   - EDIT: 编辑模式（可修改译文）

3. **动态终端适配**
   ```python
   # 根据终端大小动态调整页面大小
   terminal_width, terminal_height = self._get_terminal_size()
   available_lines = max(terminal_height - reserved_lines, 10)
   ```

4. **数据加载**
   - 支持 AI 校对版本 cache
   - 自动过滤未翻译内容
   - 保留原始 cache_item 引用

5. **编辑功能**
   - 修改译文
   - 撤销功能（original_translation）
   - 修改追踪（modified_items）

#### 10.2.2 TaskUI 任务界面
**文件位置**: `ModuleFolders/UserInterface/TaskUI.py`

**核心特性**:
1. **双模式显示**
   - **详细模式** (show_detailed=True): 三段式布局
     - Header (3行)
     - Body: 双栏对照（source_pane + target_pane）
     - Footer (15行): 小日志窗格 + 统计信息
   - **经典模式** (show_detailed=False): 上下两段式
     - Upper: 日志显示
     - Lower: 进度条 + 统计

2. **实时对照内容**
   ```python
   self.current_source = Text("Waiting...", style="dim")
   self.current_translation = Text("Waiting...", style="dim")
   ```

3. **进度条组件**
   ```python
   self.progress = Progress(
       SpinnerColumn(),
       TextColumn("[bold blue]{task.fields[action]}"),
       BarColumn(),
       TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
       TimeElapsedColumn(),
       TextColumn("/"),
       TimeRemainingColumn()
   )
   ```

4. **状态颜色映射**
   ```python
   color_map = {
       "normal": "green",
       "fixing": "yellow",
       "warning": "yellow",
       "error": "red",
       "paused": "yellow",
       "critical_error": "red"
   }
   ```

---

### 10.3 Web (Tools/WebServer) 核心翻译功能解析

#### 10.3.1 Monitor 页面
**文件位置**: `Tools/WebServer/pages/Monitor.tsx`

**核心特性**:
1. **轮询机制**
   ```typescript
   const startPolling = () => {
       intervalRef.current = setInterval(async () => {
           const data = await DataService.getTaskStatus();
           setTaskState(prev => ({
               stats: data.stats,
               logs: mappedLogs,
               chartData: data.chart_data,
               comparison: data.comparison
           }));
       }, 1000);  // 每秒更新
   };
   ```

2. **标签页切换**
   - Console Tab: 指标和控制台日志
   - Comparison Tab: 双语对照视图

3. **双语对照视图**
   ```tsx
   {/* Source Pane */}
   <div className="flex flex-col bg-slate-900/40 border border-magenta/20">
       <div className="px-4 py-2 bg-magenta/10 border-b border-magenta/20">
           <span className="text-[10px] font-bold text-magenta">Original Source</span>
       </div>
       <div className="flex-1 p-4 overflow-y-auto font-mono text-sm text-slate-300">
           {taskState.comparison?.source || "Waiting for text..."}
       </div>
   </div>

   {/* Translation Pane */}
   <div className="flex flex-col bg-slate-900/40 border border-primary/20">
       <div className="px-4 py-2 bg-primary/10 border-b border-primary/20">
           <span className="text-[10px] font-bold text-primary">Translation Output</span>
       </div>
       <div className="flex-1 p-4 overflow-y-auto font-mono text-sm text-primary-light">
           {taskState.comparison?.translation || "Processing batch..."}
       </div>
   </div>
   ```

4. **状态显示**
   - SYSTEM ACTIVE: 绿色脉冲动画
   - SYSTEM IDLE: 灰色静态

5. **统计信息**
   ```tsx
   <span>S-Rate: {taskState.stats?.successRate.toFixed(1)}%</span>
   <span>E-Rate: {taskState.stats?.errorRate.toFixed(1)}%</span>
   <span>RPM: {taskState.stats?.rpm.toFixed(2)}</span>
   <span>TPM: {taskState.stats?.tpm.toFixed(2)}k</span>
   ```

---

### 10.4 功能对比总结表

#### 10.4.1 核心翻译功能对比

| 功能特性 | Qt (source/AiNiee) | TUI (ModuleFolders) | Web (Tools/WebServer) |
|---------|-------------------|---------------------|----------------------|
| **双栏对照显示** | ✗ 无（独立表格） | ✓ 实时对照 | ✓ 实时对照 |
| **实时进度条** | ✓ ProgressBar | ✓ Rich Progress | ✓ 统计面板 |
| **波形图** | ✓ WaveformCard | ✗ 无 | ✗ 无 |
| **进度环** | ✓ ProgressRingCard | ✗ 无 | ✗ 无 |
| **累计/剩余时间** | ✓ DashboardCard | ✓ Rich显示 | ✓ 轮询更新 |
| **行数统计** | ✓ CombinedLineCard | ✓ Rich显示 | ✓ 轮询更新 |
| **任务稳定性** | ✓ DashboardCard (%) | ✓ Rich显示 | ✓ 轮询更新 |
| **Token统计** | ✓ DashboardCard | ✓ Rich显示 | ✓ 轮询更新 |
| **速度显示** | ✓ T/S | ✓ Rich显示 | ✓ RPM/TPM |
| **日志显示** | ✗ 无专用界面 | ✓ 双模式 | ✓ Terminal组件 |
| **编辑器** | ✓ TableWidget | ✓ TUIEditor | ✗ 无独立编辑器 |
| **搜索功能** | ✓ SearchDialog | ✗ 无 | ✗ 无 |
| **定时任务** | ✓ ScheduledDialogPage | ✓ SchedulerManager | ✗ 无 |
| **断点续传** | ✓ 继续按钮 | ✓ 启动时检测 | ✗ 无 |
| **AI校对支持** | ✓ 基础支持 | ✓ ProofreadTUI | ✗ 无 |
| **双语对照** | ✓ 硬编码启用 | ✗ 配置默认禁用 | ✗ 配置默认禁用 |
| **动态终端适配** | N/A | ✓ 动态布局 | N/A |
| **主题系统** | ✓ qfluentwidgets | ✓ Rich主题 | ✓ Tailwind主题 |

#### 10.4.2 预览/对照功能对比

| 特性 | Qt | TUI | Web |
|------|----|----|-----|
| **双语对照显示** | ❌ 缺失 | ✅ 有（详细模式） | ✅ 有（标签页） |
| **对照模式切换** | N/A | ⚠️ show_detailed配置 | ✅ Tab切换 |
| **实时对照更新** | ❌ 无 | ✅ 每秒更新 | ✅ 轮询1秒 |
| **对照内容滚动** | N/A | ✅ Rich自动滚动 | ✅ CSS overflow |
| **对照行数统计** | ❌ 无 | ✅ 显示行数 | ✅ 显示行数 |
| **对照样式** | N/A | ✅ magenta/green | ✅ magenta/primary |
| **对照等待提示** | N/A | ✅ "Waiting..." | ✅ "Waiting..." |

---

### 10.5 核心缺失功能分析

#### 10.5.1 TUI 缺失的 Qt 功能

| 功能 | 优先级 | 实现难度 | 说明 |
|------|--------|----------|------|
| **波形图** | 低 | 高 | Rich库不支持动态波形，需自定义 |
| **进度环** | 低 | 中 | 可用 Rich Progress 模拟 |
| **搜索功能** | 中 | 中 | 可添加搜索对话框 |
| **双语对照UI开关** | 高 | 低 | show_detailed 已实现 |
| **实时编辑** | ✅ 已实现 | - | TUIEditor 已支持 |
| **定时任务对话框** | 中 | 中 | 已有 SchedulerManager，缺UI |

#### 10.5.2 Web 缺失的 Qt 功能

| 功能 | 优先级 | 实现难度 | 说明 |
|------|--------|----------|------|
| **波形图** | 中 | 中 | 可用 Chart.js/Recharts |
| **进度环** | 低 | 低 | 可用 React 组件库 |
| **编辑器** | 高 | 中 | 需添加在线编辑器 |
| **搜索功能** | 中 | 低 | 可添加搜索框 |
| **定时任务** | 中 | 中 | 需添加定时任务UI |
| **断点续传** | 高 | 低 | 启动时检测 cache |
| **文件选择器** | 中 | 中 | 文件上传组件 |

#### 10.5.3 TUI/Web 缺失的 Qt 对照功能

| 功能 | Qt | TUI | Web | 建议 |
|------|----|----|-----|------|
| **双语对照** | ❌ 缺失 | ✅ 有 | ✅ 有 | TUI/Web 已超越 Qt |
| **对照实时更新** | ❌ | ✅ | ✅ | TUI/Web 已超越 Qt |
| **对照样式切换** | ❌ | ⚠️ 配置 | ✅ Tab | 保持现状 |
| **对照内容滚动** | ❌ | ✅ | ✅ | 保持现状 |

---

### 10.6 架构优势对比

#### 10.6.1 Qt 优势
1. **成熟的桌面应用框架**
2. **丰富的组件库** (qfluentwidgets)
3. **拖放交互** (FolderDropCard)
4. **对话框系统** (SearchDialog, ScheduledDialog)
5. **信号槽机制** (事件驱动)

#### 10.6.2 TUI 优势
1. **终端适配** (动态布局)
2. **异步支持** (AsyncLLMRequester)
3. **诊断系统** (SmartDiagnostic)
4. **自动化功能** (WatchManager, SchedulerManager)
5. **AI校对** (AIProofreader, ProofreadTUI)

#### 10.6.3 Web 优势
1. **现代化架构** (React + FastAPI)
2. **跨平台访问** (浏览器)
3. **实时轮询** (1秒更新)
4. **响应式设计** (Tailwind CSS)
5. **主题系统** (15+主题)

---

### 10.7 改造建议

#### 10.7.1 短期改进（1-2周）

**TUI 改进**:
1. ✅ 双语对照已实现（show_detailed 模式）
2. ✅ 实时编辑已实现（TUIEditor）
3. ⚠️ 需修复配置默认值（enable_bilingual_output: true）
4. 🔨 添加搜索对话框
5. 🔨 添加定时任务配置 UI

**Web 改进**:
1. ✅ 双语对照已实现（Monitor.tsx Comparison Tab）
2. ✅ 实时轮询已实现（1秒间隔）
3. ⚠️ 需修复配置默认值
4. 🔨 添加在线编辑器（基于 Monaco Editor）
5. 🔨 添加断点续传检测

#### 10.7.2 中期改进（3-4周）

**TUI 改进**:
1. 添加波形图（使用 ASCII art 或 canvas）
2. 添加进度环（Rich Progress）
3. 改进搜索功能（支持正则表达式）

**Web 改进**:
1. 添加波形图（Chart.js 或 Recharts）
2. 添加进度环（React 组件库）
3. 添加文件上传进度显示

#### 10.7.3 长期优化（1-2月）

1. **统一双语对照机制**
   - Qt 添加双语对照显示
   - TUI/Web 保持现有优势

2. **统一编辑器体验**
   - TUI: 保持 TUIEditor
   - Web: 添加 Monaco Editor
   - Qt: 保持 TableWidget

3. **统一配置管理**
   - 统一 preset.json 配置
   - 统一默认值

---

## 十一、总结与行动计划（2026-02-26 更新）

### 11.1 核心发现

1. **双语对照功能分析**
   - ✅ 功能已完整实现（BilingualPlugin + FileOutputer）
   - ❌ 配置默认值导致不生效（`enable_bilingual_output: false`）
   - 📊 TUI/Web 已超越 Qt（有实时对照，Qt 无）

2. **核心翻译功能对比**
   - Qt: 成熟的桌面应用，丰富的组件（波形图、进度环）
   - TUI: 终端适配，异步支持，诊断系统（超出 Qt）
   - Web: 现代化架构，跨平台访问（超出 Qt）

3. **预览/对照功能对比**
   - Qt: ❌ 无双语对照显示
   - TUI: ✅ 详细模式双栏对照
   - Web: ✅ Tab切换双栏对照

### 11.2 立即行动项

| 优先级 | 任务 | 预计时间 | 负责模块 |
|--------|------|----------|----------|
| 🔴 P0 | 修复双语配置默认值 | 1小时 | preset.json |
| 🟡 P1 | TUI 添加搜索对话框 | 6小时 | TUIEditor |
| 🟡 P1 | Web 添加在线编辑器 | 12小时 | CacheEditor |
| 🟡 P1 | Web 添加断点续传检测 | 4小时 | Startup |
| 🟢 P2 | TUI 添加定时任务UI | 8小时 | AutomationMenu |
| 🟢 P2 | Web 添加定时任务UI | 8小时 | TaskQueue |
| 🟢 P2 | Qt 添加双语对照显示 | 12小时 | MonitoringPage |

### 11.3 配置修复方案

**立即执行**:
```bash
# 修改 Resource/platforms/preset.json
# "enable_bilingual_output": false → true
```

**验证步骤**:
1. 翻译测试文件
2. 检查是否生成 `_bilingual` 文件
3. 验证双语文件内容格式

### 11.4 后续改造路线图

**第1阶段（1周）**: 配置修复 + 基础功能补齐
- 修复双语配置
- 添加 TUI 搜索
- 添加 Web 编辑器基础

**第2阶段（2周）**: 功能增强
- TUI 定时任务 UI
- Web 断点续传
- Web 定时任务 UI

**第3阶段（3-4周）**: Qt 追赶
- Qt 添加双语对照显示
- Qt 添加诊断系统
- Qt 添加自动化功能

**第4阶段（持续）**: 优化整合
- 统一配置管理
- 统一双语机制
- 性能优化

---

**文档版本**: 2.0
**最后更新**: 2026-02-26 23:40
**分析深度**: ⭐⭐⭐⭐⭐ (源码级深度分析)
**覆盖范围**: Qt + TUI + Web 全面对比

---

## 十二、AI翻译平台市场分析与未来规划（2026-02-27 新增）

### 12.1 专业AI翻译平台功能对比

#### 12.1.1 Smartcat 平台核心功能

| 功能模块 | 功能描述 | AiNiee现状 | 差距分析 |
|----------|----------|------------|----------|
| **翻译工作流** | 端到端项目管理 | 基础任务队列 | 需要增强 |
| **术语库管理** | 企业级术语管理 | 基础规则 | 需要专业系统 |
| **翻译记忆库** | TM集成与复用 | 缓存系统 | 需要API集成 |
| **质量评估** | AI驱动的质量评分 | 基础检查 | 需要机器学习 |
| **多用户协作** | 团队工作流 | 单用户 | 需要权限系统 |
| **CAT工具集成** | SDL, MemoQ等连接器 | 无 | 需要开发 |

#### 12.1.2 DeepL API 能力

| 能力 | 描述 | 对应AiNiee功能 |
|------|------|---------------|
| 文本翻译 | 基础翻译能力 | ✅ 已实现 |
| 文档翻译 | PDF/DOCX等 | ✅ 已实现 |
| 术语表 | 自定义术语 | ⚠️ 基础规则 |
| 正式/口语风格 | 风格控制 | ⚠️ Prompt调整 |
| Formality参数 | 礼貌级别 | ❌ 未实现 |

#### 12.1.3 专业平台共性功能矩阵

| 功能 | Smartcat | DeepL | Google | Azure | AiNiee |
|------|----------|-------|--------|-------|--------|
| 基础翻译 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 术语管理 | ✅ | ✅ | ⚠️ | ⚠️ | ⚠️ |
| 翻译记忆 | ✅ | ⚠️ | ❌ | ⚠️ | ⚠️ |
| 质量评估 | ✅ | ⚠️ | ⚠️ | ⚠️ | ❌ |
| 工作流 | ✅ | ❌ | ❌ | ⚠️ | ⚠️ |
| 团队协作 | ✅ | ❌ | ❌ | ⚠️ | ❌ |
| API集成 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 自定义模型 | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅ |

---

### 12.2 AiNiee-Next 功能差距分析

#### 12.2.1 高级翻译功能缺失

| 功能 | 优先级 | 实现难度 | 说明 |
|------|--------|----------|------|
| **专业术语库系统** | P1 | 高 | 支持TBX格式导入导出 |
| **翻译记忆API** | P2 | 中 | 与外部TM系统对接 |
| **AI质量评分** | P2 | 高 | 机器学习模型评估 |
| **风格控制参数** | P2 | 低 | formal/informal控制 |
| **翻译一致性检查** | P1 | 中 | 术语一致性验证 |
| **上下文记忆** | P1 | 中 | 段落级上下文 |

#### 12.2.2 企业级功能缺失

| 功能 | 优先级 | 实现难度 | 说明 |
|------|--------|----------|------|
| **用户权限管理** | P2 | 高 | 多用户系统 |
| **项目共享** | P2 | 中 | 团队协作 |
| **审计日志** | P3 | 中 | 操作记录 |
| **成本分析** | P3 | 中 | 费用统计 |
| **Webhooks** | P2 | 中 | 事件通知 |
| **API开放平台** | P3 | 高 | 第三方集成 |

#### 12.2.3 翻译流程优化

| 功能 | 优先级 | 实现难度 | 说明 |
|------|--------|----------|------|
| **预翻译** | P1 | 中 | 批量翻译记忆 |
| **译后编辑** | P1 | 中 | 校对工作流 |
| **多语言项目** | P2 | 高 | 多目标语言 |
| **版本控制** | P3 | 中 | 翻译版本管理 |
| **审校流程** | P2 | 高 | 多级审核 |

---

### 12.3 未来AI翻译平台架构设计

#### 12.3.1 扩展架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AiNiee Future Architecture                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐               │
│  │   Qt GUI    │    │  TUI/CLI    │    │  Web UI     │               │
│  │  (Desktop)  │    │ (Terminal)  │    │  (Browser)  │               │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘               │
│         │                   │                   │                        │
│         └───────────────────┼───────────────────┘                        │
│                             │                                            │
│                      ┌──────▼──────┐                                    │
│                      │  API Gateway │                                    │
│                      │   (FastAPI)  │                                    │
│                      └──────┬──────┘                                    │
│                             │                                            │
│         ┌───────────────────┼───────────────────┐                        │
│         │                   │                   │                        │
│  ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐               │
│  │ Translation │    │   Project    │    │    User     │               │
│  │   Service   │    │   Service    │    │   Service   │               │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘               │
│         │                   │                   │                        │
│  ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐               │
│  │  LLM Pool   │    │    Cache     │    │  Database   │               │
│  │ (18+ APIs)  │    │   Manager    │    │  (SQLite)   │               │
│  └─────────────┘    └─────────────┘    └─────────────┘               │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Extended Services Layer                        │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐   │   │
│  │  │ Terminology│ │    Translation│ │   Quality   │ │  Workflow │   │   │
│  │  │  Service   │ │    Memory    │ │  Estimator  │ │  Engine   │   │   │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 12.3.2 核心服务设计

**TranslationService (翻译服务)**
```python
class TranslationService:
    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        options: TranslationOptions
    ) -> TranslationResult:
        """核心翻译方法"""
        # 1. 获取术语
        terminology = await self.terminology_service.get_terms(source_lang, target_lang)
        # 2. 检查翻译记忆
        tm_match = await self.tm_service.lookup(text)
        if tm_match.confidence > 0.9:
            return tm_match.result
        # 3. 调用LLM翻译
        result = await self.llm_pool.translate(text, terminology, options)
        # 4. 质量评估
        quality = await self.quality_estimator.score(result)
        # 5. 保存到翻译记忆
        await self.tm_service.store(text, result, quality)
        return result
```

**TerminologyService (术语服务)**
```python
class TerminologyService:
    async def get_terms(self, source_lang: str, target_lang: str) -> Terminology:
        """获取项目术语库"""
        # 支持TBX格式导入导出
        # 术语一致性检查
        # 自动术语识别
```

**TranslationMemoryService (翻译记忆服务)**
```python
class TranslationMemoryService:
    async def lookup(self, text: str) -> TMDMatch:
        """查询翻译记忆"""
        # 模糊匹配
        # 上下文匹配
        # 质量分数计算

    async def store(self, source: str, target: str, quality: float):
        """存储到翻译记忆"""
        # 自动学习
        # 重复检测
```

**QualityEstimatorService (质量评估服务)**
```python
class QualityEstimatorService:
    async def score(self, translation: str, source: str) -> QualityScore:
        """AI质量评分"""
        # 语法检查
        # 术语一致性
        # 风格评估
        # 流畅度评分
```

---

### 12.4 UI设计分析与改进

#### 12.4.1 当前UI架构

| 界面 | 技术栈 | 特点 | 不足 |
|------|--------|------|------|
| Qt GUI | PyQt5 + qfluentwidgets | 丰富组件 | 依赖重 |
| TUI | Rich | 终端友好 | 交互有限 |
| Web | React + Tailwind | 跨平台 | 功能较少 |

#### 12.4.2 UI改进建议

**Dashboard 改进**
```
当前: 基础统计信息
建议:
- 项目进度可视化
- 成本消耗图表
- 团队活动 Timeline
- AI质量趋势
```

**编辑器改进**
```
当前: 基础双语对照
建议:
- 实时术语高亮
- 翻译记忆建议
- 质量评分显示
- 快捷术语插入
```

**项目管理改进**
```
当前: 单一项目
建议:
- 项目模板
- 批量操作
- 版本历史
- 团队分配
```

---

### 12.5 后续开发功能优先级规划

#### 12.5.1 第一优先级（P0-P1）- 核心翻译增强

| 功能 | 描述 | 预计工作量 | 优先级 |
|------|------|-----------|--------|
| **术语库系统** | 专业术语管理，支持TBX导入导出 | 16小时 | P0 |
| **翻译一致性检查** | 自动检测术语不一致 | 8小时 | P0 |
| **风格控制** | 正式/口语/礼貌级别参数 | 4小时 | P1 |
| **上下文记忆** | 段落级上下文保持 | 12小时 | P1 |

#### 12.5.2 第二优先级（P1-P2）- 企业功能

| 功能 | 描述 | 预计工作量 | 优先级 |
|------|------|-----------|--------|
| **Webhooks** | 任务完成事件通知 | 8小时 | P1 |
| **翻译记忆API** | 外部TM系统集成 | 16小时 | P2 |
| **成本分析** | 翻译费用统计 | 8小时 | P2 |
| **项目模板** | 预设配置模板 | 6小时 | P2 |

#### 12.5.3 第三优先级（P2-P3）- 高级功能

| 功能 | 描述 | 预计工作量 | 优先级 |
|------|------|-----------|--------|
| **AI质量评分** | 机器学习质量评估 | 24小时 | P2 |
| **多语言项目** | 单一项目多语言 | 24小时 | P2 |
| **版本控制** | 翻译版本管理 | 16小时 | P3 |
| **用户权限** | 多用户系统 | 32小时 | P3 |

#### 12.5.4 第四优先级（P3）- 探索功能

| 功能 | 描述 | 预计工作量 | 优先级 |
|------|------|-----------|--------|
| **CAT集成** | SDL/MemoQ连接器 | 40小时 | P3 |
| **API开放平台** | 第三方开发者API | 80小时 | P3 |
| **协作编辑** | 实时多人编辑 | 48小时 | P3 |

---

### 12.6 实施路线图

#### 阶段1：核心增强（1-2个月）
- [ ] 术语库系统设计与实现
- [ ] 翻译一致性检查
- [ ] 风格控制参数
- [ ] 上下文记忆增强

#### 阶段2：企业基础（2-3个月）
- [ ] Webhooks通知系统
- [ ] 翻译记忆API
- [ ] 成本分析面板
- [ ] 项目模板系统

#### 阶段3：高级功能（3-6个月）
- [ ] AI质量评估模型
- [ ] 多语言项目支持
- [ ] 版本控制系统
- [ ] 用户权限管理

#### 阶段4：生态建设（6个月+）
- [ ] CAT工具集成
- [ ] 开放API平台
- [ ] 社区插件市场
- [ ] 企业级部署方案

---

### 12.7 技术选型建议

#### 术语库系统
- **存储**: SQLite + JSON术语文件
- **格式**: 支持TBX (TermBase eXchange) 导入导出
- **API**: RESTful接口

#### 翻译记忆
- **存储**: SQLite + 可选外部MySQL/PostgreSQL
- **匹配**: 模糊匹配算法 (Levenshtein距离)
- **API**: 标准TMX格式支持

#### 质量评估
- **方案1**: 基于规则的评估 (快速实现)
- **方案2**: ML模型评估 (需要训练)
- **建议**: 先实现规则评估，再逐步引入ML

#### 工作流引擎
- **轻量**: 状态机实现
- **企业**: Camunda/BPMN集成
- **建议**: 先状态机，后续扩展

---

### 12.8 总结与建议

#### 核心优势
1. **多LLM支持**: 18+平台，灵活切换
2. **本地部署**: 数据安全可控
3. **开源免费**: 成本优势明显
4. **多UI支持**: 桌面/终端/网页

#### 改进方向
1. **专业化**: 术语库、质量评估
2. **企业化**: 权限、协作、工作流
3. **智能化**: AI质量评估、上下文理解
4. **生态化**: 插件市场、API平台

#### 实施建议
1. **短期**: 完成术语库和一致性检查
2. **中期**: 企业基础功能
3. **长期**: 智能化和生态建设

---

**文档版本**: 3.0
**最后更新**: 2026-02-27
**新增内容**: AI翻译平台市场分析、未来架构设计、功能优先级规划
**分析范围**: Smartcat、DeepL等专业平台对比，功能差距分析，实施路线图