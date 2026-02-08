"""
校对报告TUI展示
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.prompt import Prompt, Confirm
from typing import List, Optional

console = Console()


class ProofreadTUI:
    """校对报告TUI展示"""

    def __init__(self, i18n=None):
        self.i18n = i18n

    def _get_text(self, key: str, default: str = "") -> str:
        """获取国际化文本"""
        if self.i18n:
            return self.i18n.get(key) or default
        return default

    def display_summary(self, report) -> None:
        """显示报告摘要"""
        meta = report.meta
        summary = report.summary

        # 标题面板
        title = f"AI校对报告 - {meta.source_file}"
        console.print(Panel(f"[bold]{title}[/bold]"))

        # 基本信息表格
        info_table = Table(show_header=False, box=None)
        info_table.add_row("校对完成时间:", meta.created_at)
        info_table.add_row("使用模型:", meta.model)
        info_table.add_row(
            "统计:",
            f"总条目 {meta.total_items} | "
            f"检查 {meta.checked_items} | "
            f"发现问题 {meta.items_with_issues}"
        )
        console.print(info_table)
        console.print()

        # 问题统计
        console.print("[bold]问题统计:[/bold]")
        
        ai_issues = summary.ai_issues
        console.print(
            f"  AI检查: "
            f"[red]高危 {ai_issues.get('high', 0)}[/red] | "
            f"[yellow]中危 {ai_issues.get('medium', 0)}[/yellow] | "
            f"[dim]低危 {ai_issues.get('low', 0)}[/dim]"
        )

        if summary.rule_issues:
            rule_parts = [
                f"{k} {v}" for k, v in summary.rule_issues.items()
            ]
            console.print(f"  规则检查: {' | '.join(rule_parts)}")

        console.print()

    def display_issue_detail(self, item, issue_num: int) -> None:
        """显示单个问题详情"""
        severity_colors = {
            "high": "red",
            "medium": "yellow", 
            "low": "dim"
        }

        # AI检查问题
        if item.ai_check.get("has_issues"):
            for issue in item.ai_check.get("issues", []):
                severity = issue.get("severity", "low")
                color = severity_colors.get(severity, "white")

                panel_content = (
                    f"类型: {issue.get('type', 'unknown')}\n"
                    f"位置: 第{item.index}行\n"
                    f"原文: {item.source_text[:60]}...\n"
                    f"译文: {item.translated_text[:60]}...\n"
                    f"问题: {issue.get('description', '')}\n"
                    f"建议: {issue.get('suggestion', '')}\n"
                    f"置信度: {issue.get('confidence', 0):.2f}"
                )

                console.print(Panel(
                    panel_content,
                    title=f"问题 #{issue_num} [{severity}]",
                    border_style=color
                ))

    def display_action_menu(self) -> str:
        """显示操作菜单"""
        table = Table(show_header=False, box=None)
        table.add_row("[cyan]1.[/]", "逐条审阅问题")
        table.add_row("[cyan]2.[/]", "一键采纳所有高危修改")
        table.add_row("[cyan]3.[/]", "导出校对后文件")
        table.add_row("[cyan]4.[/]", "导出报告为JSON")
        table.add_row("[dim]0.[/]", "返回")

        console.print(Panel(table, title="操作选项"))
        return Prompt.ask("请选择", choices=["0", "1", "2", "3", "4"])

    def display_warning(self) -> bool:
        """显示校对前警告，返回用户是否确认"""
        console.print()
        console.print("[yellow]⚠️ 警告：[/yellow]")
        console.print("[yellow]此功能依赖LLM自身性能，推荐使用带有[/yellow]")
        console.print("[yellow]推理能力的模型（如DeepSeek-R1、o1等）[/yellow]")
        console.print("[yellow]校对效果因模型而异，请自行评估。[/yellow]")
        console.print()
        console.print("[yellow]⚠️ 费用提示：[/yellow]")
        console.print("[yellow]校对需要同时传入原文和译文，将产生额外[/yellow]")
        console.print("[yellow]API费用，请确认后继续。[/yellow]")
        console.print()

        return Confirm.ask("确认开始校对？", default=False)
