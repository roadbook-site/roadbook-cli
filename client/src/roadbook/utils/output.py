import sys
from typing import List, Any
try:
    from rich.console import Console
    from rich.table import Table
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

def print_table(headers: List[str], rows: List[List[str]]):
    if HAS_RICH:
        table = Table(show_header=True, header_style="bold magenta")
        for h in headers:
            table.add_column(h)
        for r in rows:
            table.add_row(*r)
        console.print(table)
    else:
        # Fallback to simple print
        print("\t".join(headers))
        print("-" * 50)
        for r in rows:
            print("\t".join(str(x) for x in r))

def print_info(msg: str):
    if HAS_RICH:
        console.print(f"[bold blue]{msg}[/bold blue]")
    else:
        print(f"[INFO] {msg}")

def print_error(msg: str):
    if HAS_RICH:
        console.print(f"[bold red]{msg}[/bold red]")
    else:
        print(f"[ERROR] {msg}")
