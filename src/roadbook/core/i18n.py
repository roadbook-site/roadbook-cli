import locale
import os
import sys

# Optional try-except since this is core utility
try:
    from .config import load_config
except ImportError:
    def load_config():
        return {}

TRANSLATIONS = {
    "en": {
        # initialize.py
        "init_success": "Successfully initialized roadbook scaffold for '{name}' (ID: {rb_id})",
        "init_dir": "Directory: [cyan]{book_dir}[/cyan]",
        "launch_editor": "[bold cyan]Launching Roadbook Editor...[/bold cyan]",
        "ai_feedback_title": "[bold yellow]🤖 Subsequent Guidance for AI Agent[/bold yellow]",
        "ai_feedback_scaffold_gen": "Roadbook scaffold has been generated in the {book_dir} directory.",
        "ai_feedback_mode_ai": "Mode: [AI Autonomous Exploration Mode]",
        "ai_feedback_next_steps": "Next steps recommendation:",
        "ai_feedback_ai_step1": "1. Please read and analyze the target (Description) in `roadbook.md`.",
        "ai_feedback_ai_step2": "2. Start writing or modifying `scripts/script.py`, and use tools like playwright to explore how to achieve the target.",
        "ai_feedback_ai_step3": "3. After successful exploration, please clean up the execution path and write the valid AARP action primitives back into `roadbook.md` to complete the roadbook body.",
        "ai_feedback_mode_manual": "Mode: [Human-Machine Collaboration / Manual Guidance Mode]",
        "ai_feedback_manual_step1": "1. Please have the user or AI Agent prioritize modifying `roadbook.md` to fill in specific Sheet (scenario) information.",
        "ai_feedback_manual_step2": "2. Editor recommendation: Run `roadbook edit {rb_id}` to launch the visual editor.",
        "ai_feedback_manual_step3": "3. In the editor, you can upload images using the screenshot tool and make annotations using the drawing feature.",
        "ai_feedback_manual_step4": "4. Once the description in `roadbook.md` is clear, it can be translated into specific execution code in `scripts/script.py`.",
        
        # browser.py.tpl
        "browser_not_found": "Playwright browser core not found!",
        "browser_install_prompt": "Please run the following command in terminal to install (only needed once globally):",
        
        # executor.py
        "exec_no_script_warning": "If there is no script, warn the user and switch to semantic guidance mode (open).",
    },
    "zh": {
        # initialize.py
        "init_success": "成功为 '{name}' 初始化路书脚手架 (ID: {rb_id})",
        "init_dir": "目录: [cyan]{book_dir}[/cyan]",
        "launch_editor": "[bold cyan]正在启动路书编辑器...[/bold cyan]",
        "ai_feedback_title": "[bold yellow]🤖 给 AI Agent 的后续引导[/bold yellow]",
        "ai_feedback_scaffold_gen": "路书脚手架已生成在 {book_dir} 目录下。",
        "ai_feedback_mode_ai": "模式：[AI 自主探索模式]",
        "ai_feedback_next_steps": "下一步建议：",
        "ai_feedback_ai_step1": "1. 请阅读并分析 `roadbook.md` 中的目标 (Description)。",
        "ai_feedback_ai_step2": "2. 开始编写或修改 `scripts/script.py`，使用 playwright 等工具探索如何达成目标。",
        "ai_feedback_ai_step3": "3. 探索成功后，请清洗执行路径，将有效的 AARP 动作原语回写到 `roadbook.md` 中，完善路书本体。",
        "ai_feedback_mode_manual": "模式：[人机协同/手动引导模式]",
        "ai_feedback_manual_step1": "1. 请用户或 AI 代理优先修改 `roadbook.md`，填充具体的 Sheet（场景）信息。",
        "ai_feedback_manual_step2": "2. 推荐使用编辑器：运行 `roadbook edit {rb_id}` 启动可视化编辑器。",
        "ai_feedback_manual_step3": "3. 在编辑器中，你可以使用截图工具上传图片，并使用涂鸦功能进行标注。",
        "ai_feedback_manual_step4": "4. 当 `roadbook.md` 描述清晰后，可将其翻译为 `scripts/script.py` 中的具体执行代码。",
        
        # browser.py.tpl
        "browser_not_found": "无法找到 Playwright 浏览器内核！",
        "browser_install_prompt": "请使用终端运行以下命令进行安装（全局仅需一次）：",
        
        # executor.py
        "exec_no_script_warning": "如果没有脚本，则警告用户并切换到语义引导模式 (open).",
    }
}

def get_system_language() -> str:
    """Detect system language."""
    # Check environment variables first
    for env_var in ('LANGUAGE', 'LC_ALL', 'LC_MESSAGES', 'LANG'):
        val = os.environ.get(env_var)
        if val:
            if val.lower().startswith('zh'):
                return 'zh'
            return 'en'
            
    # Fallback to sys/locale
    try:
        if sys.platform == 'win32':
            import ctypes
            windll = ctypes.windll.kernel32
            lang_id = windll.GetUserDefaultUILanguage()
            # 0x0804 is zh-CN, 0x0404 is zh-TW, etc. 0x04 is Chinese primary language ID
            if (lang_id & 0x3ff) == 0x04:
                return 'zh'
            return 'en'
        else:
            lang, _ = locale.getlocale()
            if lang and lang.lower().startswith('zh'):
                return 'zh'
            return 'en'
    except Exception:
        return 'en'

def get_language() -> str:
    """Get the current configured language."""
    try:
        config = load_config()
        lang = config.get("core", {}).get("language", "auto")
        if lang == "auto":
            return get_system_language()
        if lang in ["zh", "en"]:
            return lang
        if lang.startswith("zh"):
            return "zh"
        return "en"
    except Exception:
        return get_system_language()

def t(key: str, **kwargs) -> str:
    """Translate a key."""
    lang = get_language()
    text = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except KeyError:
            return text
    return text
