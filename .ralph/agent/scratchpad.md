# 分析：为什么翻译只生成中文而不是中英对照

## 问题分析

### 日志分析
- 项目类型: AutoType (PDF文件)
- 原文语言: en (英语)
- 译文语言: zh_CN (中文)
- 输出文件: 只有一个PDF文件，没有bilingual_pdf文件夹

### 根本原因

根据代码分析，存在两个双语输出机制：

1. **BilingualPlugin** (`PluginScripts/BilingualPlugin/BilingualPlugin.py`):
   - `default_enable = False` - 默认禁用
   - 作用：将 `translated_text` 修改为 `译文 + "\n" + 原文` 的形式
   - 适用于非原生支持双语的格式（如AutoType）

2. **FileOutputer** 原生支持:
   - 原生支持格式: TXT, EPUB, SRT, BABELDOC_PDF
   - 通过 `enable_bilingual_output` 配置控制
   - 会创建单独的 bilingual_txt, bilingual_epub, bilingual_srt, bilingual_pdf 文件夹

### AutoType 不在原生支持列表

日志显示项目类型是 `AutoType`，这不在原生支持双语的格式列表中。因此需要启用 BilingualPlugin 才能实现双语输出。

## 解决方案

需要在配置中启用 BilingualPlugin：

1. **Web界面**: 在插件设置中启用 BilingualPlugin
2. **配置文件**: 在 `plugin_enables` 中添加 `"BilingualPlugin": true`

或者直接在代码中修改默认值为 True:
- 文件: `PluginScripts/BilingualPlugin/BilingualPlugin.py`
- 修改: `self.default_enable = True`
