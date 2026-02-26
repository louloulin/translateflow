"""
TUI搜索对话框
提供类似Qt版本的搜索功能，支持搜索范围选择、正则表达式、标记行过滤等
"""
import re
from typing import List, Dict, Optional, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table


class SearchScope:
    """搜索范围枚举"""
    ALL = "all"
    SOURCE = "source"
    TRANSLATION = "translation"
    POLISHED = "polished"

    @classmethod
    def get_display_name(cls, scope: str) -> str:
        """获取范围的显示名称"""
        mapping = {
            cls.ALL: "全文",
            cls.SOURCE: "原文",
            cls.TRANSLATION: "译文",
            cls.POLISHED: "润文"
        }
        return mapping.get(scope, cls.ALL)

    @classmethod
    def get_fields(cls, scope: str) -> List[str]:
        """获取要搜索的字段列表"""
        if scope == cls.ALL:
            return ['source', 'translation', 'polished']
        elif scope == cls.SOURCE:
            return ['source']
        elif scope == cls.TRANSLATION:
            return ['translation']
        elif scope == cls.POLISHED:
            return ['polished']
        return ['source', 'translation', 'polished']


class SearchDialog:
    """TUI搜索对话框"""

    def __init__(self, console: Console, cache_data: List[Dict], current_line: int):
        self.console = console
        self.cache_data = cache_data
        self.current_line = current_line

        # 搜索参数
        self.search_query = ""
        self.search_scope = SearchScope.ALL
        self.is_regex = False
        self.is_flagged_only = False

        # 搜索结果
        self.search_results: List[Tuple[int, Dict]] = []  # (index, item)
        self.current_result_index = 0

    def show(self) -> bool:
        """显示搜索对话框"""
        self.console.print()
        self.console.print(Panel.fit("🔍 搜索功能", style="bold cyan"))

        # 输入搜索内容
        self.search_query = Prompt.ask(
            "[cyan]搜索内容[/cyan]",
            default="",
            show_default=False
        ).strip()

        # 选择搜索范围
        scope_options = [
            f"[1] 全文 (搜索所有字段)",
            f"[2] 原文 (仅搜索source)",
            f"[3] 译文 (仅搜索translation)",
            f"[4] 润文 (仅搜索polished)"
        ]
        self.console.print("\n[cyan]搜索范围:[/cyan]")
        for option in scope_options:
            self.console.print(f"  {option}")

        scope_choice = Prompt.ask(
            "\n[cyan]选择范围[/cyan]",
            choices=["1", "2", "3", "4"],
            default="1"
        )

        scope_mapping = {
            "1": SearchScope.ALL,
            "2": SearchScope.SOURCE,
            "3": SearchScope.TRANSLATION,
            "4": SearchScope.POLISHED
        }
        self.search_scope = scope_mapping.get(scope_choice, SearchScope.ALL)

        # 是否使用正则表达式
        self.is_regex = Confirm.ask(
            "[cyan]使用正则表达式?[/cyan]",
            default=False
        )

        # 是否仅搜索标记行
        self.is_flagged_only = Confirm.ask(
            "[cyan]仅搜索被标记行?[/cyan]",
            default=False
        )

        # 执行搜索
        return self._perform_search()

    def _perform_search(self) -> bool:
        """执行搜索"""
        self.search_results = []

        # 验证正则表达式
        if self.is_regex:
            try:
                re.compile(self.search_query)
            except re.error as e:
                self.console.print(f"[red]正则表达式错误: {e}[/red]")
                return False

        # 确定要搜索的字段
        search_fields = SearchScope.get_fields(self.search_scope)

        # 遍历所有数据进行搜索
        for idx, item in enumerate(self.cache_data):
            # 如果要求仅搜索标记行，先过滤
            if self.is_flagged_only:
                if not self._is_item_flagged(item):
                    continue

            # 执行搜索
            if self._matches_search(item, search_fields):
                self.search_results.append((idx, item))

        # 显示搜索结果
        if self.search_results:
            self.console.print(f"\n[green]找到 {len(self.search_results)} 个匹配项[/green]")
            self._show_results()
            return True
        else:
            self.console.print(f"\n[yellow]未找到匹配项[/yellow]")
            return False

    def _is_item_flagged(self, item: Dict) -> bool:
        """检查条目是否被标记"""
        cache_item = item.get('cache_item')
        if not cache_item or not hasattr(cache_item, 'extra') or not cache_item.extra:
            return False

        # 根据搜索范围检查对应的标记
        if self.search_scope == SearchScope.POLISHED:
            return cache_item.extra.get('language_mismatch_polish', False)
        elif self.search_scope == SearchScope.TRANSLATION:
            return cache_item.extra.get('language_mismatch_translation', False)
        elif self.search_scope == SearchScope.ALL:
            return (cache_item.extra.get('language_mismatch_translation', False) or
                    cache_item.extra.get('language_mismatch_polish', False))
        else:  # SOURCE范围不支持标记过滤
            return False

    def _matches_search(self, item: Dict, search_fields: List[str]) -> bool:
        """检查条目是否匹配搜索条件"""
        if not self.search_query:
            return True  # 空搜索匹配所有（经过标记过滤后）

        query = self.search_query

        for field in search_fields:
            text = item.get(field, '')
            if not text:
                continue

            if self.is_regex:
                try:
                    if re.search(query, text, re.IGNORECASE):
                        return True
                except re.error:
                    pass
            else:
                if query.lower() in text.lower():
                    return True

        return False

    def _show_results(self):
        """显示搜索结果"""
        self.console.print()

        # 创建结果表格
        table = Table(
            title=f"搜索结果 ({len(self.search_results)} 项)",
            show_header=True,
            header_style="bold cyan"
        )
        table.add_column("索引", style="cyan", width=6)
        table.add_column("行号", style="cyan", width=6)
        table.add_column("内容预览", style="white")

        # 显示前20个结果
        for i, (idx, item) in enumerate(self.search_results[:20]):
            # 高亮当前行
            if idx == self.current_line:
                table.add_row(
                    str(i + 1),
                    f"{idx + 1} ●",
                    self._get_preview_text(item),
                    style="on blue"
                )
            else:
                table.add_row(
                    str(i + 1),
                    str(idx + 1),
                    self._get_preview_text(item)
                )

        if len(self.search_results) > 20:
            table.add_row(
                "...",
                "...",
                f"还有 {len(self.search_results) - 20} 个结果",
                style="dim"
            )

        self.console.print(table)

        # 询问是否跳转到某个结果
        self._ask_navigation()

    def _get_preview_text(self, item: Dict) -> str:
        """获取预览文本"""
        preview_fields = SearchScope.get_fields(self.search_scope)

        for field in preview_fields:
            text = item.get(field, '')
            if text:
                # 截断长文本
                if len(text) > 60:
                    return text[:57] + "..."
                return text

        return "(无内容)"

    def _ask_navigation(self):
        """询问导航选项"""
        self.console.print()
        self.console.print("[cyan]导航选项:[/cyan]")
        self.console.print("  [1] 跳转到下一个匹配项")
        self.console.print("  [2] 跳转到上一个匹配项")
        self.console.print("  [3] 跳转到指定结果")
        self.console.print("  [q] 返回编辑器")

        choice = Prompt.ask(
            "\n[cyan]选择操作[/cyan]",
            choices=["1", "2", "3", "q"],
            default="1"
        )

        if choice == "q":
            return
        elif choice == "1":
            self._navigate_next()
        elif choice == "2":
            self._navigate_prev()
        elif choice == "3":
            self._navigate_to_index()

    def _navigate_next(self):
        """导航到下一个匹配项"""
        # 找到当前位置之后的第一个匹配
        for idx, item in self.search_results:
            if idx > self.current_line:
                self._jump_to_result(idx)
                return

        # 如果没有找到，循环到第一个
        if self.search_results:
            first_idx = self.search_results[0][0]
            self._jump_to_result(first_idx)

    def _navigate_prev(self):
        """导航到上一个匹配项"""
        # 找到当前位置之前的第一个匹配
        for idx, item in reversed(self.search_results):
            if idx < self.current_line:
                self._jump_to_result(idx)
                return

        # 如果没有找到，循环到最后一个
        if self.search_results:
            last_idx = self.search_results[-1][0]
            self._jump_to_result(last_idx)

    def _navigate_to_index(self):
        """导航到指定结果索引"""
        max_index = len(self.search_results)
        if max_index == 0:
            return

        prompt_text = f"[cyan]输入结果编号 (1-{max_index}):[/cyan]"
        try:
            result_index = int(Prompt.ask(prompt_text)) - 1
            if 0 <= result_index < max_index:
                idx, item = self.search_results[result_index]
                self._jump_to_result(idx)
            else:
                self.console.print("[red]无效的编号[/red]")
        except (ValueError, KeyboardInterrupt):
            pass

    def _jump_to_result(self, index: int):
        """跳转到指定索引"""
        self.console.print(f"\n[green]跳转到第 {index + 1} 行[/green]")
        self.current_result_index = index
        # 返回跳转目标供调用者使用

    def get_next_match(self) -> Optional[int]:
        """获取下一个匹配项的索引"""
        if not self.search_results:
            return None

        for idx, item in self.search_results:
            if idx > self.current_line:
                return idx

        # 循环到第一个
        return self.search_results[0][0]

    def get_prev_match(self) -> Optional[int]:
        """获取上一个匹配项的索引"""
        if not self.search_results:
            return None

        for idx, item in reversed(self.search_results):
            if idx < self.current_line:
                return idx

        # 循环到最后一个
        return self.search_results[-1][0]

    def get_all_matches(self) -> List[int]:
        """获取所有匹配项的索引"""
        return [idx for idx, _ in self.search_results]

    def has_results(self) -> bool:
        """检查是否有搜索结果"""
        return len(self.search_results) > 0