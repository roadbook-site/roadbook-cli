import argparse
import sys
from .core.config import ensure_roadbook_dir
from .commands import library, search, executor, script, run

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
    open      Start an interactive guidance session (Recommended)
    run       Execute automation script (Auto-fallback to interactive)

  [Observe]   Review execution history and logs
    logs      Manage and inspect run logs

  [Develop]   Manage automation scripts
    script    Manage local scripts
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
    open_parser = subparsers.add_parser("open", help="Open roadbook interactive session")
    open_parser.add_argument("id", help="Roadbook ID")
    open_parser.add_argument("--inputs", help="JSON inputs")
    open_parser.set_defaults(func=executor.start_session)

    # Command: run
    run_parser = subparsers.add_parser("run", help="Run roadbook (Script/Auto)")
    run_parser.add_argument("id", help="Roadbook ID")
    run_parser.add_argument("--inputs", help="JSON inputs")
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

    # --- Group: Develop ---
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

    # Ensure environment is ready
    ensure_roadbook_dir()

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
