# Memories

## Patterns

### mem-1772187283-a3c5
> Worktree merge strategy: 当合并多个worktree分支时，按照复杂度从低到高的顺序合并(docs → UI → features)，避免代码冲突。.ralph/运行时文件冲突可以安全地使用--ours策略，不影响实际代码
<!-- tags: git, worktree, merge | created: 2026-02-27 -->

### mem-1772185964-32ef
> BilingualPlugin 需要在 plugin_enables 中手动启用，default_enable=False。双语功能需要两部分：1)BilingualPlugin修改translated_text为'译文+原文' 2)enable_bilingual_output配置生成分离双语文件
<!-- tags: bilingual, plugin, configuration | created: 2026-02-27 -->

### mem-1772179886-ba52
> BilingualPlugin 需要在 plugin_enables 中手动启用，default_enable=False。双语功能需要两部分：1)BilingualPlugin修改translated_text为'译文+原文' 2)enable_bilingual_output配置生成分离双语文件
<!-- tags: bilingual, plugin, configuration | created: 2026-02-27 -->

## Decisions

## Fixes

### mem-1772187293-f520
> Git worktree冲突解决: 对于.ralph/和Resource/Prompt运行时文件，使用git checkout --ours保留当前状态。对于代码文件(PROMPT.md, *.tsx, *.py)，检查冲突内容后选择合适的版本
<!-- tags: git, conflict-resolution, worktree | created: 2026-02-27 -->

## Context
