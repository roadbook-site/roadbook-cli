import argparse
import sys

# Ensure stdout uses UTF-8 to prevent UnicodeEncodeError and garbled Chinese text on Windows
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

import warnings

# Suppress requests dependency warning
warnings.filterwarnings("ignore", message="Unable to find acceptable character detection dependency")

from .core.config import ensure_roadbook_dir
from .commands import library, search, executor, script, run, editor, auth, remote, config, doctor, initialize, browser
from . import __version__

class RichHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Custom help formatter to display commands by category."""
    pass

def main():
    description = """
AI-Agent Roadbook CLI - Your guide to automated operations.

Command Categories:
  [Explore]   Find and view roadbooks
    list      List all available roadbooks
    search    Search roadbooks by keyword
    show      Show details of a roadbook

  [Navigate]  Execute and interact with roadbooks
    run       Execute automation script (Auto-downgrade to semantic guide mode)

  [Observe]   Review execution history and logs
    logs      Manage and inspect run logs

  [Develop]   Create and manage roadbooks
    init      Initialize a new roadbook scaffold
    edit      Start Roadbook Editor (WebUI)
    script    Manage local scripts
    link      Symlink local roadbook to global
    unlink    Remove symlink of a roadbook
    remove    Delete a roadbook
    
  [Diagnose]  System diagnostics
    doctor    Check environment health and dependencies

  [Configure] Manage CLI settings
    config    Get/Set/List configuration values
    browser   Initialize dedicated browser settings

  [Remote]    Interact with Roadbook Server
    login     Login to server
    push      Push roadbook to server
    pull      Pull roadbook from server
    remote    Manage remote resources
"""
    parser = argparse.ArgumentParser(
        prog="roadbook",
        description=description,
        formatter_class=RichHelpFormatter
    )
    
    # Intercept --version to also check PATH
    if '--version' in sys.argv:
        print(f"roadbook {__version__}")
        try:
            from .utils.env import check_path_warning
            check_path_warning()
        except ImportError:
            pass
        sys.exit(0)
        
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    subparsers = parser.add_subparsers(dest="command", help=argparse.SUPPRESS)

    # --- Group: Explore ---
    # Command: list
    list_parser = subparsers.add_parser("list", help="List all roadbooks")
    list_parser.add_argument("-g", "--global", dest="global_scope", action="store_true", help="Operate on global roadbooks")
    list_parser.set_defaults(func=library.list_books)

    # Command: search
    search_parser = subparsers.add_parser("search", help="Search roadbooks")
    search_parser.add_argument("keyword", help="Search keyword")
    search_parser.add_argument("-g", "--global", dest="global_scope", action="store_true", help="Operate on global roadbooks")
    search_parser.set_defaults(func=search.search_books)

    # Command: show
    show_parser = subparsers.add_parser("show", aliases=["inspect"], help="Show roadbook details")
    show_parser.add_argument("id", help="Roadbook ID")
    show_parser.add_argument("-g", "--global", dest="global_scope", action="store_true", help="Operate on global roadbooks")
    show_parser.set_defaults(func=library.show_book)

    # --- Group: Navigate ---
    # Command: run
    run_parser = subparsers.add_parser("run", help="Run roadbook (Script execution)")
    run_parser.add_argument("id", help="Roadbook ID")
    run_parser.add_argument("--inputs", help="JSON inputs (string)")
    run_parser.add_argument("--inputs-file", help="JSON inputs file path")
    run_parser.add_argument("--mock-input", help="Mock JSON inputs (string) for testing 'role: module' roadbooks directly")
    run_parser.add_argument("--format", dest="output_format", choices=["jsonl", "json", "csv", "quick"], default="jsonl", help="Output format for dataset (default: jsonl). 'quick' mode prints concise result to stdout.")
    run_parser.add_argument("-g", "--global", dest="global_scope", action="store_true", help="Operate on global roadbooks")
    run_parser.set_defaults(func=executor.run_book)

    # --- Group: Observe ---
    # Command: logs
    logs_parser = subparsers.add_parser("logs", help="Manage run logs")
    logs_subparsers = logs_parser.add_subparsers(dest="subcommand", help="Logs subcommands")

    # logs list
    logs_list_parser = logs_subparsers.add_parser("list", help="List run logs")
    logs_list_parser.add_argument("id", help="Roadbook ID")
    logs_list_parser.set_defaults(func=run.run_history)

    # logs inspect
    logs_inspect_parser = logs_subparsers.add_parser("inspect", help="Inspect a specific run log")
    logs_inspect_parser.add_argument("run_id", help="Run ID")
    logs_inspect_parser.set_defaults(func=run.run_inspect)

    # logs last
    logs_last_parser = logs_subparsers.add_parser("last", help="Show last run log")
    logs_last_parser.set_defaults(func=run.run_last)

    # logs cat (New)
    logs_cat_parser = logs_subparsers.add_parser("cat", help="Print full log content")
    logs_cat_parser.add_argument("run_id", help="Run ID")
    logs_cat_parser.set_defaults(func=run.run_cat)

    # logs show (New)
    logs_show_parser = logs_subparsers.add_parser("show", help="Show structured run details")
    logs_show_parser.add_argument("run_id", help="Run ID")
    logs_show_parser.add_argument("--error", action="store_true", help="Show error details only")
    logs_show_parser.set_defaults(func=run.run_show)

    # --- Group: Develop ---
    # Command: edit
    edit_parser = subparsers.add_parser("edit", help="Start Roadbook Editor (WebUI)")
    edit_parser.add_argument("id", nargs="?", help="Optional: Open specific roadbook ID")
    edit_parser.add_argument("--port", type=int, default=8000, help="Port to run server on")
    edit_parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind server to")
    edit_parser.add_argument("--dir", type=str, default=None, help="Directory to serve roadbooks from (default: ~/.roadbook/books)")
    edit_parser.add_argument("-g", "--global", dest="global_scope", action="store_true", help="Operate on global roadbooks")
    edit_parser.set_defaults(func=editor.start_editor)

    # --- Group: Develop ---
    # Command: init
    init_parser = subparsers.add_parser("init", help="Initialize a new roadbook scaffold")
    init_parser.add_argument("name", help="Name of the roadbook")
    init_parser.add_argument("--description", "-d", help="Optional description of the roadbook", default="")
    init_parser.add_argument("--entry-url", help="Initial URL for the roadbook to start exploration", default="https://www.example.com")
    init_parser.add_argument("--edit", "-e", help="Immediately open in editor after initialization", action="store_true")
    init_parser.add_argument("-g", "--global", dest="global_scope", action="store_true", help="Initialize in global directory")

    # Interactive/Advanced Scaffolding options
    init_parser.add_argument("--browser-mode", choices=["new", "cdp"], default=None, help="Browser connection mode: 'new' (fresh profile) or 'cdp' (existing browser)")
    init_parser.add_argument("--login", type=str, choices=["y", "n", "yes", "no", "true", "false"], default=None, help="Website requires login (y/n)")
    
    init_parser.set_defaults(func=initialize.init_book)

    # Command: script
    script_parser = subparsers.add_parser("script", help="Manage local scripts")
    script_subparsers = script_parser.add_subparsers(dest="subcommand", help="Script subcommands")
    
    # script ls
    script_ls_parser = script_subparsers.add_parser("ls", help="List scripts")
    script_ls_parser.add_argument("id", help="Roadbook ID")
    script_ls_parser.add_argument("-g", "--global", dest="global_scope", action="store_true", help="Operate on global roadbooks")
    script_ls_parser.set_defaults(func=script.script_ls)

    # script clean
    script_clean_parser = script_subparsers.add_parser("clean", help="Clean scripts")
    script_clean_parser.add_argument("id", help="Roadbook ID")
    script_clean_parser.add_argument("-g", "--global", dest="global_scope", action="store_true", help="Operate on global roadbooks")
    script_clean_parser.set_defaults(func=script.script_clean)

    # Command: link
    link_parser = subparsers.add_parser("link", help="Symlink local roadbook to global")
    link_parser.add_argument("id", nargs="?", help="Optional: Roadbook ID to link (defaults to all local roadbooks)")
    from .commands import link as link_cmd
    link_parser.set_defaults(func=link_cmd.link_book)

    # Command: unlink
    unlink_parser = subparsers.add_parser("unlink", help="Remove symlink of a roadbook")
    unlink_parser.add_argument("id", nargs="?", help="Optional: Roadbook ID to unlink (defaults to all local roadbooks)")
    from .commands import unlink as unlink_cmd
    unlink_parser.set_defaults(func=unlink_cmd.unlink_book)

    # Command: remove
    remove_parser = subparsers.add_parser("remove", aliases=["rm"], help="Delete a roadbook")
    remove_parser.add_argument("id", help="Roadbook ID")
    remove_parser.add_argument("-g", "--global", dest="global_scope", action="store_true", help="Operate on global roadbooks")
    from .commands import remove as remove_cmd
    remove_parser.set_defaults(func=remove_cmd.remove_book)

    # --- Group: Diagnose ---
    # Command: doctor
    doctor_parser = subparsers.add_parser("doctor", help="Check environment health")
    doctor_parser.set_defaults(func=doctor.run_doctor)

    # --- Group: Configure ---
    # Command: config
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_subparsers = config_parser.add_subparsers(dest="subcommand", help="Config subcommands")

    # config list
    config_list_parser = config_subparsers.add_parser("list", help="List all configurations")
    config_list_parser.set_defaults(func=config.config_list)

    # config get
    config_get_parser = config_subparsers.add_parser("get", help="Get configuration value")
    config_get_parser.add_argument("key", help="Configuration key (e.g. browser.headless)")
    config_get_parser.set_defaults(func=config.config_get)

    # config set
    config_set_parser = config_subparsers.add_parser("set", help="Set configuration value")
    config_set_parser.add_argument("key", help="Configuration key")
    config_set_parser.add_argument("value", help="Configuration value")
    config_set_parser.add_argument("-g", "--global", dest="global_config", action="store_true", help="Set global configuration")
    config_set_parser.set_defaults(func=config.config_set)
    
    # Command: browser
    browser_parser = subparsers.add_parser("browser", aliases=["init-browser"], help="Manage dedicated browser settings and lifecycle")
    browser_subparsers = browser_parser.add_subparsers(dest="subcommand", help="Browser subcommands")

    # browser init
    browser_init_parser = browser_subparsers.add_parser("init", help="Initialize dedicated browser settings and create shortcut")
    browser_init_parser.set_defaults(func=browser.browser_init)

    # browser open
    browser_open_parser = browser_subparsers.add_parser("open", help="Open the dedicated browser")
    browser_open_parser.set_defaults(func=browser.browser_open)

    # browser close
    browser_close_parser = browser_subparsers.add_parser("close", help="Close the dedicated browser gracefully")
    browser_close_parser.set_defaults(func=browser.browser_close)

    # browser kill
    browser_kill_parser = browser_subparsers.add_parser("kill", help="Force release the CDP port by killing the occupying process")
    browser_kill_parser.set_defaults(func=browser.browser_kill)

    # browser diagnose
    browser_diagnose_parser = browser_subparsers.add_parser("diagnose", aliases=["doctor"], help="Diagnose CDP port, connectivity, and user data directory")
    browser_diagnose_parser.set_defaults(func=browser.browser_diagnose)

    # Ensure backward compatibility for `roadbook browser` without subcommand (fallback to init or help)
    browser_parser.set_defaults(func=browser.browser_main)

    # --- Group: Remote ---
    # Command: login
    login_parser = subparsers.add_parser("login", help="Login to Roadbook Server")
    login_parser.set_defaults(func=auth.login)


    # Command: push
    push_parser = subparsers.add_parser("push", help="Push roadbook to server")
    push_parser.add_argument("id", help="Roadbook ID")
    push_parser.add_argument("-g", "--global", dest="global_scope", action="store_true", help="Operate on global roadbooks")
    push_parser.set_defaults(func=remote.push)
    
    # Command: pull
    pull_parser = subparsers.add_parser("pull", help="Pull roadbook from server")
    pull_parser.add_argument("id", help="Roadbook ID")
    pull_parser.add_argument("-g", "--global", dest="global_scope", action="store_true", help="Operate on global roadbooks")
    pull_parser.set_defaults(func=remote.pull)

    # Command: remote
    remote_parser = subparsers.add_parser("remote", help="Manage remote roadbooks")
    remote_subparsers = remote_parser.add_subparsers(dest="subcommand", help="Remote subcommands")
    
    # remote list
    remote_list_parser = remote_subparsers.add_parser("list", help="List remote roadbooks")
    remote_list_parser.set_defaults(func=remote.remote_list)

    # Ensure environment is ready
    ensure_roadbook_dir()

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
