"""
规则引擎检查器 - 基于正则表达式的译文检查
不走AI，零成本，更准确
"""

import re
from dataclasses import dataclass
from typing import List
from abc import ABC, abstractmethod


@dataclass
class RuleCheckResult:
    """规则检查结果"""
    rule_name: str
    severity: str  # high/medium/low
    source_snippet: str
    target_snippet: str
    description: str
    auto_fixable: bool = False
    fix_suggestion: str = ""


class BaseRule(ABC):
    """规则基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def check(self, source: str, target: str) -> List[RuleCheckResult]:
        pass


class QuotePairRule(BaseRule):
    """引号配对检查"""

    @property
    def name(self) -> str:
        return "quote_pair"

    def _count_apostrophes(self, text: str, quote_char: str) -> int:
        """计算英文缩写中的撇号数量（字母+撇号+字母的模式）"""
        # 匹配 I'm, don't, it's 等缩写形式
        pattern = r"[a-zA-Z]" + re.escape(quote_char) + r"[a-zA-Z]"
        return len(re.findall(pattern, text))

    def check(self, source: str, target: str) -> List[RuleCheckResult]:
        results = []

        # 中文引号对 (左引号, 右引号, 名称)
        cn_quotes = [
            ('\u201c', '\u201d', '中文双引号'),  # " "
            ('\u2018', '\u2019', '中文单引号'),  # ' '
            ('\u300c', '\u300d', '日文引号'),    # 「 」
            ('\u300e', '\u300f', '日文双引号'),  # 『 』
        ]

        for item in cn_quotes:
            left = item[0]
            right = item[1]
            quote_name = item[2]
            left_count = target.count(left)
            right_count = target.count(right)

            # 检查原文中的符号情况
            src_left = source.count(left)
            src_right = source.count(right)

            # 对于中文单引号，右引号'可能被用作英文撇号（I'm, don't等）
            # 需要排除这些缩写形式
            if right == '\u2019':
                src_apostrophes = self._count_apostrophes(source, right)
                tgt_apostrophes = self._count_apostrophes(target, right)
                # 调整计数，排除撇号
                src_right = src_right - src_apostrophes
                right_count = right_count - tgt_apostrophes

            # 如果原文也不配对，说明是跨行对话，跳过检查
            if src_left != src_right:
                continue

            if left_count != right_count:
                results.append(RuleCheckResult(
                    rule_name=self.name,
                    severity="medium",
                    source_snippet=source[:50] + "..." if len(source) > 50 else source,
                    target_snippet=target[:50] + "..." if len(target) > 50 else target,
                    description=f"{quote_name}不配对: 左{left_count}个, 右{right_count}个 (原文: 左{src_left}个, 右{src_right}个)",
                    auto_fixable=False,
                    fix_suggestion=f"建议: 1) 保留原文符号 {left}...{right}  2) 或改为目标语言常用符号"
                ))

        return results


class BracketPairRule(BaseRule):
    """括号配对检查"""

    @property
    def name(self) -> str:
        return "bracket_pair"

    def check(self, source: str, target: str) -> List[RuleCheckResult]:
        results = []

        brackets = [
            ('(', ')', '英文圆括号'),
            ('\uff08', '\uff09', '中文圆括号'),  # （ ）
            ('[', ']', '英文方括号'),
            ('\u3010', '\u3011', '中文方括号'),  # 【 】
            ('{', '}', '花括号'),
            ('\u3008', '\u3009', '尖括号'),      # 〈 〉
        ]

        for item in brackets:
            left = item[0]
            right = item[1]
            bracket_name = item[2]
            left_count = target.count(left)
            right_count = target.count(right)

            # 检查原文中的符号情况
            src_left = source.count(left)
            src_right = source.count(right)

            # 如果原文也不配对，跳过检查
            if src_left != src_right:
                continue

            if left_count != right_count:
                results.append(RuleCheckResult(
                    rule_name=self.name,
                    severity="medium",
                    source_snippet=source[:50] + "..." if len(source) > 50 else source,
                    target_snippet=target[:50] + "..." if len(target) > 50 else target,
                    description=f"{bracket_name}不配对: 左{left_count}个, 右{right_count}个 (原文: 左{src_left}个, 右{src_right}个)",
                    auto_fixable=False,
                    fix_suggestion=f"建议: 1) 保留原文符号 {left}...{right}  2) 或改为目标语言常用符号"
                ))

        return results


class PlaceholderRule(BaseRule):
    """占位符保留检查"""

    @property
    def name(self) -> str:
        return "placeholder"

    def check(self, source: str, target: str) -> List[RuleCheckResult]:
        results = []

        # 严格匹配的占位符（内容必须完全相同）
        strict_patterns = [
            (r'%[sd]', '百分号占位符'),
            (r'%\d*[sd]', '带数字占位符'),
            (r'\$\{[^}]+\}', '模板占位符'),
            (r'\[\[[^\]]+\]\]', '双方括号占位符'),
        ]

        # 数量匹配的占位符（内容可以翻译，但数量要一致）
        count_patterns = [
            (r'\{[^}]+\}', '花括号占位符'),
            (r'<[^>]+/?>', 'HTML/XML标签'),
        ]

        # 严格匹配检查
        for pattern, pattern_name in strict_patterns:
            source_matches = set(re.findall(pattern, source))
            target_matches = set(re.findall(pattern, target))

            missing = source_matches - target_matches
            if missing:
                results.append(RuleCheckResult(
                    rule_name=self.name,
                    severity="high",
                    source_snippet=source[:50] + "..." if len(source) > 50 else source,
                    target_snippet=target[:50] + "..." if len(target) > 50 else target,
                    description=f"{pattern_name}丢失: {', '.join(missing)}",
                    auto_fixable=False,
                    fix_suggestion=f"请保留原文中的{pattern_name}"
                ))

        # 数量匹配检查（内容可以翻译，但数量要一致）
        for pattern, pattern_name in count_patterns:
            source_matches = re.findall(pattern, source)
            target_matches = re.findall(pattern, target)

            src_count = len(source_matches)
            tgt_count = len(target_matches)

            # 对于HTML标签，检查原文开闭标签是否配对
            # 如果原文本身不配对，跳过检查（可能是原文问题，译文补全了）
            if pattern_name == 'HTML/XML标签':
                src_open = len(re.findall(r'<([a-zA-Z][a-zA-Z0-9]*)[^>]*(?<!/)>', source))
                src_close = len(re.findall(r'</[a-zA-Z][a-zA-Z0-9]*>', source))
                if src_open != src_close:
                    continue

            if src_count != tgt_count:
                results.append(RuleCheckResult(
                    rule_name=self.name,
                    severity="medium",
                    source_snippet=source[:50] + "..." if len(source) > 50 else source,
                    target_snippet=target[:50] + "..." if len(target) > 50 else target,
                    description=f"{pattern_name}数量不一致: 原文{src_count}个, 译文{tgt_count}个",
                    auto_fixable=False,
                    fix_suggestion=f"请检查{pattern_name}是否正确保留"
                ))

        return results


class ControlCharRule(BaseRule):
    """控制符检查"""

    @property
    def name(self) -> str:
        return "control_char"

    def check(self, source: str, target: str) -> List[RuleCheckResult]:
        results = []

        control_chars = [
            (r'\n', '换行符'),
            (r'\t', '制表符'),
            (r'\r', '回车符'),
        ]

        for pattern, char_name in control_chars:
            source_count = len(re.findall(pattern, source))
            target_count = len(re.findall(pattern, target))

            if source_count > 0 and target_count == 0:
                results.append(RuleCheckResult(
                    rule_name=self.name,
                    severity="medium",
                    source_snippet=source[:50] + "..." if len(source) > 50 else source,
                    target_snippet=target[:50] + "..." if len(target) > 50 else target,
                    description=f"{char_name}丢失: 原文{source_count}个, 译文{target_count}个",
                    auto_fixable=False,
                    fix_suggestion=f"请检查是否需要保留{char_name}"
                ))

        return results


class NewlineConsistencyRule(BaseRule):
    """换行符一致性检查"""

    @property
    def name(self) -> str:
        return "newline_consistency"

    def check(self, source: str, target: str) -> List[RuleCheckResult]:
        results = []

        source_newlines = source.count('\n')
        target_newlines = target.count('\n')

        # 允许一定容差（±2）
        if abs(source_newlines - target_newlines) > 2:
            results.append(RuleCheckResult(
                rule_name=self.name,
                severity="low",
                source_snippet=source[:50] + "..." if len(source) > 50 else source,
                target_snippet=target[:50] + "..." if len(target) > 50 else target,
                description=f"换行符数量差异较大: 原文{source_newlines}个, 译文{target_newlines}个",
                auto_fixable=False,
                fix_suggestion="请检查换行符是否正确保留"
            ))

        return results


class RuleBasedChecker:
    """基于规则的译文检查器"""

    def __init__(self):
        self.rules: List[BaseRule] = [
            QuotePairRule(),
            BracketPairRule(),
            PlaceholderRule(),
            ControlCharRule(),
            NewlineConsistencyRule(),
        ]

    def check(self, source: str, target: str) -> List[RuleCheckResult]:
        """执行所有规则检查"""
        all_results = []
        for rule in self.rules:
            results = rule.check(source, target)
            all_results.extend(results)
        return all_results

    def check_batch(self, items: List[tuple]) -> dict:
        """批量检查，返回按索引分组的结果"""
        results_by_index = {}
        for index, source, target in items:
            results = self.check(source, target)
            if results:
                results_by_index[index] = results
        return results_by_index
