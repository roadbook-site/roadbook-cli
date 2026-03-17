import os
import re
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from ..core.roadbook import RoadbookManager
from ..core.runtime import RuntimeManager
from ..utils.output import console, print_error, print_success
from . import editor
import argparse

def _generate_id(name: str) -> str:
    """Generate a valid ID from the roadbook name."""
    # Convert to lowercase
    id_str = name.lower()
    # Replace spaces and underscores with hyphens
    id_str = re.sub(r'[\s_]+', '-', id_str)
    # Remove any non-alphanumeric characters except hyphens
    id_str = re.sub(r'[^a-z0-9\-]', '', id_str)
    # Remove duplicate hyphens
    id_str = re.sub(r'-+', '-', id_str)
    # Strip leading/trailing hyphens
    id_str = id_str.strip('-')
    return id_str

def init_book(args):
    """Initialize a new roadbook scaffold."""
    name = args.name
    description = args.description
    goal = args.goal
    
    rb_id = _generate_id(name)
    if not rb_id:
        print_error("Invalid roadbook name. Cannot generate a valid ID.")
        return
        
    # Check for duplicates
    existing_books = RoadbookManager.list_roadbooks()
    for book in existing_books:
        if book.id == rb_id:
            print_error(f"A roadbook with ID '{rb_id}' already exists at {book.path.parent}.")
            return

    # Create directory structure in current workspace
    cwd = Path.cwd()
    book_dir = cwd / ".roadbook" / rb_id
    
    try:
        book_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print_error(f"Failed to create directory {book_dir}: {e}")
        return

    # 1. Generate roadbook.md
    roadbook_path = book_dir / "roadbook.md"
    
    # Base YAML frontmatter
    yaml_frontmatter = f"""---
id: "{rb_id}"
name: "{name}"
version: "1.0"
description: "{description}"
inputs: {{}}
outputs: {{}}
---
"""
    
    if goal:
        # Autonomous exploration scaffold
        content = f"""{yaml_frontmatter}
## 目标定义 (Goal)
**ID**: goal1
**Description**: {goal}

> 请 AI Agent 基于上述目标进行自主探索。探索成功后，请将有效步骤提取并覆盖到本文件中。
"""
    else:
        # Human-guided scaffold
        content = f"""{yaml_frontmatter}
## 第一个场景 (Scene 1)
**ID**: s001
**Description**: [请描述第一个场景或操作意图]
**URL**: `https://example.com`

**Steps**:
1. [请填写具体步骤，例如: `打开 https://example.com`]
2. [补充后续步骤，例如：`点击搜索框，输入关键词，按回车`]
3. [补充后续步骤，获取页面信息，例如：`提取搜索结果的标题和链接`]

---

## 第二个场景 (Scene 2)
**ID**: s002
**Description**: [请描述第二个场景或操作意图]

**Steps**:
1. [补充后续步骤]
"""

    try:
        with open(roadbook_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        print_error(f"Failed to write roadbook.md: {e}")
        return

    # 2. Generate script scaffold
    scripts_dir = RuntimeManager.get_scripts_dir(rb_id, book_dir=book_dir)
    script_path = scripts_dir / "script.py"
    
    script_content = f'''"""
Automation script for roadbook: {name} ({rb_id})
"""
from playwright.sync_api import sync_playwright

def run(inputs: dict) -> dict:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        # TODO: Implement automation steps here
        # Follow the roadbook.md definitions
        
        browser.close()
    
    return {{"status": "success"}}
'''
    
    try:
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_content)
    except Exception as e:
        print_error(f"Failed to write script.py: {e}")
        return

    # Success output with feedback prompt for AI agent
    print_success(f"Successfully initialized roadbook scaffold for '{name}' (ID: {rb_id})")
    console.print(f"Directory: [cyan]{book_dir}[/cyan]")
    
    # Handle auto-edit
    if args.edit:
        console.print("[bold cyan]Launching Roadbook Editor...[/bold cyan]")
        # Construct arguments for editor
        editor_args = argparse.Namespace(
            port=8000, 
            host="127.0.0.1", 
            dir=str(book_dir),
            id=rb_id
        )
        editor.start_editor(editor_args)
        return

    # Constructing AI Agent feedback prompt
    feedback_lines = [
        f"路书脚手架已生成在 {book_dir} 目录下。"
    ]
    
    if goal:
        feedback_lines.extend([
            "模式：[AI 自主探索模式]",
            "下一步建议：",
            "1. 请阅读并分析 `roadbook.md` 中的目标 (Goal)。",
            "2. 开始编写或修改 `scripts/script.py`，使用 playwright 等工具探索如何达成目标。",
            "3. 探索成功后，请清洗执行路径，将有效的 AARP 动作原语回写到 `roadbook.md` 中，完善路书本体。"
        ])
    else:
        feedback_lines.extend([
            "模式：[人机协同/手动引导模式]",
            "下一步建议：",
            "1. 请用户或 AI 代理优先修改 `roadbook.md`，填充具体的 Sheet（场景）信息。",
            "2. 推荐使用编辑器：运行 `roadbook edit {rb_id}` 启动可视化编辑器。",
            "3. 在编辑器中，你可以使用截图工具上传图片，并使用涂鸦功能进行标注。",
            "4. 当 `roadbook.md` 描述清晰后，可将其翻译为 `scripts/script.py` 中的具体执行代码。"
        ])
        
    feedback_text = "\n".join(feedback_lines)
    console.print(Panel(feedback_text, title="[bold yellow]🤖 给 AI Agent 的后续引导[/bold yellow]", border_style="yellow"))
