
Task starting with parameters from web UI...
[DEBUG] UV Path: /Users/louloulin/.local/bin/uv
[DEBUG] Command: uv run /Users/louloulin/Documents/linchong/ai/AiNiee-Next/ainiee_cli.py translate /Users/louloulin/Documents/linchong/ai/AiNiee-Next/updatetemp/ORI___SAM’S CLUB_PO 37672_CRL 1604750_6-25-2024 REVISED.pdf -y --web-mode
Uninstalled 1 package in 11ms
Installed 1 package in 4ms
[BabeldocPatch] 补丁已应用
保护的缓存目录: /Users/louloulin/Documents/linchong/ai/AiNiee-Next/Resource/Models/tiktoken
Traceback (most recent call last):
File "/Users/louloulin/Documents/linchong/ai/AiNiee-Next/ainiee_cli.py", line 108, in <module>
i18n = I18NLoader(current_lang)
^^^^^^^^^^^^^^^^^^^^^^^^
File "/Users/louloulin/Documents/linchong/ai/AiNiee-Next/ainiee_cli.py", line 87, in __init__
self.load_language(lang)
File "/Users/louloulin/Documents/linchong/ai/AiNiee-Next/ainiee_cli.py", line 91, in load_language
with open(path, 'r', encoding='utf-8') as f: self.data = json.load(f)
^^^^^^^^^^^^
rapidjson.JSONDecodeError: Parse error at offset 55108: The document root must not be followed by other values.
