import os
import time
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

console = Console()

class FileSelector:
    def __init__(self, i18n):
        self.i18n = i18n

    def select_path(self, start_path=".", select_file=True, select_dir=False):
        current_path = Path(start_path).resolve()

        while True:
            try:
                entries = sorted(os.scandir(current_path), key=lambda e: (e.is_file(), e.name.lower()))
            except OSError as e:
                console.print(f"[red]Error: {e}[/red]")
                current_path = current_path.parent
                continue

            console.clear()
            table = Table(title=f"Current Path: {current_path}", show_header=True)
            table.add_column("Index", style="dim", width=5)
            table.add_column("Type", width=6)
            table.add_column("Name", style="bright_white")
            
            display_list = []

            # Parent directory
            table.add_row("0", "[dir]", "..")
            display_list.append(current_path.parent)

            # Current directory selection
            if select_dir:
                table.add_row("1", "[dir]", f"Select this directory -> '{current_path.name}'")
                display_list.append(current_path)

            idx_offset = len(display_list)

            dirs = [e for e in entries if e.is_dir()]
            files = [e for e in entries if e.is_file()]

            for i, entry in enumerate(dirs + files):
                is_dir = entry.is_dir()
                entry_type = "[dir]" if is_dir else "[file]"
                
                if not select_file and not is_dir:
                    continue
                    
                table.add_row(str(i + idx_offset), entry_type, entry.name)
                display_list.append(Path(entry.path))
            
            console.print(table)
            
            prompt_text = self.i18n.get("prompt_selector_select_adv")
            user_input = Prompt.ask(f"\n{prompt_text}", default="q").strip().strip('"').strip("'")

            if user_input.lower() == 'q':
                return None

            # Check if user entered a path directly
            if os.path.exists(user_input):
                p = Path(user_input).resolve()
                if (p.is_file() and select_file) or (p.is_dir() and select_dir):
                    return str(p)
                elif p.is_dir(): # If user gave a dir path in file mode, navigate there
                    current_path = p
                    continue

            try:
                selected_idx = int(user_input)
                if 0 <= selected_idx < len(display_list):
                    selected_path = display_list[selected_idx]
                    if selected_path.is_dir():
                        # Handle "Select this directory" case
                        if select_dir and selected_idx == 1:
                            return str(selected_path)
                        current_path = selected_path
                    elif select_file:
                        return str(selected_path)
                else:
                    console.print("[red]Invalid index.[/red]"); time.sleep(1)
            except ValueError:
                console.print("[red]Invalid input. Please enter a number or 'q'.[/red]"); time.sleep(1)
