# Memories

## Patterns

### mem-1772171488-df69
> Theme implementation verified: Uses CSS variables with :root (light) and .dark classes, localStorage persistence via uiPreferences.ts, supports light/dark/system modes. Follows shadcn UI patterns without using next-themes library. Theme application logic in GlobalContext.tsx:259-283 correctly handles all modes.
<!-- tags: theme, ui, shadcn | created: 2026-02-27 -->

### mem-1772170996-88e9
> Theme default changed from 'dark' to 'light' in uiPreferences.ts. The normalizeUiPreferences() function now uses defaults.themeMode instead of hardcoded 'system' for consistency.
<!-- tags: theme, ui, defaults | created: 2026-02-27 -->

### mem-1772148314-302c
> Web断点续传检测实现：后端已有/api/task/breakpoint-status接口，前端Dashboard页面通过DataService.getBreakpointStatus()调用，页面加载时自动检测并显示恢复翻译横幅
<!-- tags: web, breakpoint, translation | created: 2026-02-26 -->

## Decisions

## Fixes

### mem-1772147864-1f3d
> Bilingual output feature was disabled by default in code despite preset.json having enable_bilingual_output=true. Fixed by changing defaults in default_config.py:56 and TaskConfig.py:107 from False to True.
<!-- tags: config, bilingual, translation | created: 2026-02-26 -->

## Context

### mem-1772178212-fa0f
> Analysis complete: PROMPT.md contains comprehensive AI translation platform analysis including market research (Smartcat, DeepL), gap analysis, future architecture design, and implementation roadmap. Ready tasks verification: TUI SearchDialog already implemented (SearchDialog.py), Web Monaco Editor already integrated (MonacoEditor.tsx in CacheEditor.tsx), Qt BilingualCard already exists (BilingualCard.py in MonitoringPage). All P1/P2 tasks from the analysis are already implemented.
<!-- tags: analysis, translation-platform | created: 2026-02-27 -->
