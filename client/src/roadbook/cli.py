import argparse
import sys
from .core.config import ensure_roadbook_dir
from .commands import library, search, executor, script, run, editor, auth, remote, config

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
    open      Start semantic guide mode (Interactive)
    run       Execute automation script (Auto-downgrade to semantic mode)

  [Observe]   Review execution history and logs
    logs      Manage and inspect run logs

  [Develop]   Manage automation scripts
    script    Manage local scripts
    
  [Configure] Manage CLI settings
    config    Get/Set/List configuration values

  [Remote]    Interact with Roadbook Server
    login     Login to server
    push      Push roadbook to server
    pull      Pull roadbook from server
    remote    Manage remote resources
"""
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=RichHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help=argparse.SUPPRESS)

    # --- Group: Explore ---
    # Command: list
    list_parser = subparsers.add_parser("list", help="List all roadbooks")
    list_parser.set_defaults(func=library.list_books)

    # Command: search
    search_parser = subparsers.add_parser("search", help="Search roadbooks")
    search_parser.add_argument("keyword", help="Search keyword")
    search_parser.set_defaults(func=search.search_books)

    # Command: show
    show_parser = subparsers.add_parser("show", aliases=["inspect"], help="Show roadbook details")
    show_parser.add_argument("id", help="Roadbook ID")
    show_parser.set_defaults(func=library.show_book)

    # --- Group: Navigate ---
    # Command: open
    open_parser = subparsers.add_parser("open", help="Open roadbook in semantic guide mode")
    open_parser.add_argument("id", help="Roadbook ID")
    open_parser.add_argument("--inputs", help="JSON inputs (string)")
    open_parser.add_argument("--inputs-file", help="JSON inputs file path")
    open_parser.set_defaults(func=executor.start_session)

    # Command: run
    run_parser = subparsers.add_parser("run", help="Run roadbook (Script/Auto)")
    run_parser.add_argument("id", help="Roadbook ID")
    run_parser.add_argument("--inputs", help="JSON inputs (string)")
    run_parser.add_argument("--inputs-file", help="JSON inputs file path")
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
    edit_parser.set_defaults(func=editor.start_editor)

    # Command: script
    script_parser = subparsers.add_parser("script", help="Manage scripts")
    script_subparsers = script_parser.add_subparsers(dest="subcommand", help="Script subcommands")
    
    # script ls
    script_ls_parser = script_subparsers.add_parser("ls", help="List scripts")
    script_ls_parser.add_argument("id", help="Roadbook ID")
    script_ls_parser.set_defaults(func=script.script_ls)

    # script clean
    script_clean_parser = script_subparsers.add_parser("clean", help="Clean scripts")
    script_clean_parser.add_argument("id", help="Roadbook ID")
    script_clean_parser.set_defaults(func=script.script_clean)

    # --- Group: Configure ---
    # Command: config
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_subparsers = config_parser.add_subparsers(dest="subcommand", help="Config subcommands")

    # config list
    config_list_parser = config_subparsers.add_parser("list", help="List all configurations")
    config_list_parser.set_defaults(func=config.config_list)

    # config get
    config_get_parser = config_subparsers.add_parser("get", help="Get configuration value")
    config_get_parser.add_argument("key", help="Configuration key (e.g. scaffold_defaults.language)")
    config_get_parser.set_defaults(func=config.config_get)

    # config set
    config_set_parser = config_subparsers.add_parser("set", help="Set configuration value")
    config_set_parser.add_argument("key", help="Configuration key")
    config_set_parser.add_argument("value", help="Configuration value")
    config_set_parser.set_defaults(func=config.config_set)

    # --- Group: Remote ---
    # Command: login
    login_parser = subparsers.add_parser("login", help="Login to Roadbook Server")
    login_parser.set_defaults(func=auth.login)


    # Command: push
    push_parser = subparsers.add_parser("push", help="Push roadbook to server")
    push_parser.add_argument("id", help="Roadbook ID")
    push_parser.set_defaults(func=remote.push)
    
    # Command: pull
    pull_parser = subparsers.add_parser("pull", help="Pull roadbook from server")
    pull_parser.add_argument("id", help="Roadbook ID")
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
