## 页面设计规范（Desktop First）

### 0. 全局样式与设计令牌（适用于所有页面）
- Layout：整体采用 **CSS Grid + Flex 混合**。外层 `grid`（侧栏/主内容），内层 `flex` 做纵向分区（header/body/panels）。
- Breakpoints（建议）：
  - Desktop：>= 1024px（双栏/多列优先）
  - Tablet：768–1023px（缩小间距，部分区域改单列）
  - Mobile：< 768px（侧栏抽屉 + 单列）
- Global Tokens（建议）：
  - 字号：12/14/16/20；正文行高 1.5；等宽信息（路径/日志）行高 1.45。
  - 间距：8/12/16/24；卡片 padding 默认 16。
  - 可读性：长文本最大行宽建议 80–110 字符；超出采用换行/断行而非横向滚动（除表格）。
- 交互状态：按钮 hover 增强对比；禁用态降低饱和度；错误态使用红色并带图标。

### 1. 仪表盘（首页）
- Meta：title=“AiNiee 控制台”；description=“任务与配置的统一控制台”。
- Page Structure：
  - 顶部：页面标题 + 简要说明（可省略）
  - 内容区：卡片网格（2–4 列，随宽度变化）
- 关键布局优化（解决“过窄”）：
  - 提供内容宽度模式：
    - **Fluid（默认）**：主内容容器 `max-width` 放宽或取消，利用大屏空间。
    - **Contained**：保留 `max-width` 以获得稳定阅读宽度。
  - 在设置页可切换，并全站生效。

### 2. 任务控制台（开始翻译）
- Meta：title=“任务控制台”；description=“启动任务并实时查看日志与统计”。
- Page Structure（纵向分区，解决“高度不足”）：
  1) Header Controls（输入路径/任务类型/启动停止/上传）
  2) CLI 预览条（可折叠）
  3) Panel Area（可占满剩余高度）
     - StatsPanel（上）
     - Terminal 或 Comparison（下）
- 高度策略（关键）：
  - 采用“父容器 `height: 100%` + 子区 `min-h-0` + `overflow:auto`”的滚动模型。
  - Panel Area 使用可调分隔（拖拽）或可配置比例：`Stats : Terminal = splitRatio`。
  - Terminal 设保底高度 `minTerminalPx`，避免窗口过矮导致不可用。
- 信息密度与可读性：
  - 提供“紧凑模式”：缩小 card padding、缩短控件高度、日志行间距略减。
  - 日志：时间列固定宽；消息列自动换行+断行；error/warn 使用图标+高对比色；支持点击复制单行。
- 响应式：
  - 宽屏：Comparison 双栏；每栏内部独立滚动；标题条吸顶。
  - 窄屏：Comparison 自动堆叠（上原文/下译文），保持独立滚动并可快速切换锚点。

### 3. 监控面板
- Meta：title=“监控面板”；description=“只读监控任务进度与关键状态”。
- Page Structure：
  - Sticky Top Bar：状态/进度/错误摘要（吸顶，可开关）
  - Content：图表/列表/表格分区滚动（避免整页滚动导致信息丢失）
- 可读性：
  - 关键指标优先显示；非关键明细折叠进“展开详情”。
  - 表格在小屏自动降级为卡片摘要（主字段 + 次字段）。

### 4. 设置页（显示与布局设置）
- 新增分组：**显示与布局**
  - 内容宽度：Fluid / Contained
  - 信息密度：Comfortable / Compact
  - 任务控制台：Stats/Terminal 默认比例（splitRatio）、日志最小高度（minTerminalPx）
  - 监控面板：吸顶工具条开关
  - 恢复默认：一键回滚 UI 偏好
- 持久化：
  - 保存按钮可选；推荐“即时生效 + 自动保存”（localStorage）以减少交互成本。