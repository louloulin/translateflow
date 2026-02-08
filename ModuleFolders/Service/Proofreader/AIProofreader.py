"""
AI校对器 - 调用LLM进行翻译校对
"""

import json
import os
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class AICheckIssue:
    """AI检查发现的问题"""
    type: str  # terminology|omission|hallucination|logic_error
    severity: str  # high|medium|low
    location: str
    description: str
    suggestion: str = ""
    confidence: float = 0.0


@dataclass
class AICheckResult:
    """AI检查结果"""
    has_issues: bool
    issues: List[AICheckIssue] = field(default_factory=list)
    corrected_translation: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0


class AIProofreader:
    """AI校对器"""

    def __init__(self, config: dict):
        self.config = config
        self.prompt_template = self._load_prompt()
        self.confidence_threshold = config.get("proofread_confidence_threshold", 0.7)

    def _load_prompt(self) -> str:
        """加载校对提示词，根据用户配置自动选择语言"""
        lang_map = {
            "zh": "zh", "zh_CN": "zh", "zh_TW": "zh", "chinese": "zh",
            "en": "en", "english": "en",
            "ja": "ja", "jp": "ja", "japanese": "ja",
        }

        target_lang = self.config.get("target_language", "")
        interface_lang = self.config.get("interface_language", "zh")
        lang_key = target_lang.lower() if target_lang else interface_lang.lower()
        prompt_lang = lang_map.get(lang_key, "zh")

        prompt_file = f"proofread_{prompt_lang}.txt"
        prompt_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "..",
            "Resource", "Prompt", "System",
            prompt_file
        )

        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()

        default_path = prompt_path.replace(prompt_file, "proofread_zh.txt")
        if os.path.exists(default_path):
            with open(default_path, "r", encoding="utf-8") as f:
                return f.read()

        return ""

    def _build_user_message(
        self,
        source: str,
        translation: str,
        glossary: List[dict] = None,
        context: str = ""
    ) -> str:
        """构建用户消息"""
        message_parts = []

        if context:
            message_parts.append(f"## 上下文\n{context}")

        message_parts.append(f"## 原文\n{source}")
        message_parts.append(f"## 译文\n{translation}")

        if glossary:
            glossary_str = "\n".join([
                f"- {item.get('src', '')} → {item.get('dst', '')}"
                for item in glossary
            ])
            message_parts.append(f"## 术语表\n{glossary_str}")

        return "\n\n".join(message_parts)

    def _parse_response(self, response: str) -> AICheckResult:
        """解析AI响应"""
        try:
            json_match = response
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_match = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                json_match = response[start:end].strip()

            data = json.loads(json_match)

            issues = []
            for issue_data in data.get("issues", []):
                issue = AICheckIssue(
                    type=issue_data.get("type", "unknown"),
                    severity=issue_data.get("severity", "low"),
                    location=issue_data.get("location", ""),
                    description=issue_data.get("description", ""),
                    suggestion=issue_data.get("suggestion", ""),
                    confidence=issue_data.get("confidence", 0.0)
                )
                if issue.confidence >= self.confidence_threshold:
                    issues.append(issue)

            return AICheckResult(
                has_issues=len(issues) > 0,
                issues=issues,
                corrected_translation=data.get("corrected_translation", "")
            )

        except (json.JSONDecodeError, KeyError, TypeError):
            return AICheckResult(has_issues=False, issues=[])

    def proofread_single(
        self,
        source: str,
        translation: str,
        glossary: List[dict] = None,
        context: str = ""
    ) -> AICheckResult:
        """校对单条翻译（同步方法）"""
        from ModuleFolders.Infrastructure.LLMRequester.LLMRequester import LLMRequester
        from ModuleFolders.Infrastructure.TaskConfig.TaskConfig import TaskConfig

        user_message = self._build_user_message(
            source, translation, glossary, context
        )

        messages = [{"role": "user", "content": user_message}]

        try:
            # 使用 TaskConfig 获取平台配置（和翻译一样的逻辑）
            from ModuleFolders.Infrastructure.TaskConfig.TaskType import TaskType
            task_config = TaskConfig()
            task_config.load_config_from_dict(self.config)
            task_config.prepare_for_translation(TaskType.TRANSLATION)
            platform_config = task_config.get_platform_configuration("translationReq")

            requester = LLMRequester()
            skip, response_think, response_content, prompt_tokens, completion_tokens = requester.sent_request(
                messages=messages,
                system_prompt=self.prompt_template,
                platform_config=platform_config
            )

            if skip:
                return AICheckResult(has_issues=False, issues=[])

            result = self._parse_response(response_content)
            result.prompt_tokens = prompt_tokens
            result.completion_tokens = completion_tokens
            return result

        except Exception as e:
            print(f"[AI校对错误] {e}")
            return AICheckResult(has_issues=False, issues=[])

    def proofread_batch(
        self,
        items: List[Dict[str, Any]],
        glossary: List[dict] = None,
        context_lines: int = 5,
        progress_callback=None
    ) -> Dict[int, AICheckResult]:
        """批量校对"""
        results = {}
        total_prompt_tokens = 0
        total_completion_tokens = 0

        for i, item in enumerate(items):
            # 构建上下文
            context_parts = []
            start = max(0, i - context_lines)
            end = min(len(items), i + context_lines + 1)

            for j in range(start, end):
                if j != i:
                    ctx_item = items[j]
                    context_parts.append(
                        f"[{j}] {ctx_item.get('source', '')[:50]}"
                    )

            context = "\n".join(context_parts)

            result = self.proofread_single(
                source=item.get("source", ""),
                translation=item.get("translation", ""),
                glossary=glossary,
                context=context
            )

            total_prompt_tokens += result.prompt_tokens
            total_completion_tokens += result.completion_tokens

            if result.has_issues:
                results[item.get("index", i)] = result

            if progress_callback:
                progress_callback(i + 1, len(items), total_prompt_tokens, total_completion_tokens)

        return results
