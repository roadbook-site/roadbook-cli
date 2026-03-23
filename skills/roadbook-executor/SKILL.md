---
name: "roadbook-executor"
description: "Executes a Roadbook by following its instructions step-by-step using the CLI and browser automation tools. Invoke when the user wants to run or execute a specific Roadbook."
---

# Roadbook Executor

This skill helps you execute a Roadbook, which is a structured guide for automating browser tasks.

## Requirements

- Ensure Python is available before execution (`python --version`).
- Ensure the Roadbook CLI is installed:
    - Linux: `pip3 install roadbook`
    - macOS/Windows: `pip install roadbook`

## Usage

1.  **Identify the Roadbook**:
    - Use `roadbook list` to see available roadbooks.
    - If the user provides a name or ID, try to find it in the list.

2.  **Start Execution**:
    - **Automatic Mode**: Use `roadbook run <id>` to execute the roadbook using any existing automation scripts.
    - **Script Generation**: If no script exists, the CLI will provide guidance on generating scaffolding.

4.  **Robust Execution Guidelines**:
    - **Selector Fallback**: Treat selectors in the Roadbook as **hints**. If a specific CSS selector fails (e.g., timeout), DO NOT give up immediately.
        - **Try alternatives**: Look for other attributes (text, aria-label, etc.) that identify the same element.
        - **Semantic matching**: Use text content or visual relationship to find the element.
        - **Multiple selectors**: If the Roadbook provides a list of selectors, try them in order.
    - **Download Handling**: When a step involves downloading a file (e.g., `CLICK "Download"`):
        - **Intervene**: Use Playwright/Browser tools to intercept the download event (e.g., `page.on('download')`).
        - **Verify**: Ensure the file is saved to the correct path and verify its existence. Do not rely solely on the browser's default behavior.
    - **Input Handling**: When passing complex JSON inputs to `roadbook run`:
        - **Use File**: Write the JSON to a temporary file and use `--inputs-file <path>` instead of `--inputs` string to avoid shell escaping issues on Windows/PowerShell.

5.  **Error Handling & Script Generation**:
    - If an action fails, report the error to the user and ask for guidance or try to debug.
    - You can use `roadbook logs inspect <run_id>` to see detailed logs of the session.

## CLI Commands Reference

- `roadbook list`: List local roadbooks in the current project (`.roadbook/`).
- `roadbook list -g`: List all globally installed roadbooks.
- `roadbook inspect <id> [-g]`: Show details of a roadbook (alias for `show`).
- `roadbook run <id> [-g]`: Execute a roadbook automatically (script-first). Use `-g` if roadbook is in the global library.
- `roadbook logs list <id>`: View run history.
- `roadbook link`: Link local roadbooks to the global scope for easy testing.
- `roadbook remove <id> [-g]`: Delete a roadbook (use `-g` for global).

## Script Management & Artifacts

- **IMPORTANT - Reusability & Token Efficiency**: Scripts are the core of Roadbook's efficiency. They can be reused without consuming tokens. **Always strive to generate a robust script instead of relying on interactive semantic execution every time.**
- **Workspace Structure**: Roadbooks are executed in a dedicated workspace directory. For local roadbooks, this is `.roadbook/<roadbook_id>/`.
    - **Scripts**: Located in `.roadbook/<roadbook_id>/scripts/script.py`.
    - **Outputs**: Located in `.roadbook/<roadbook_id>/outputs/`.
    - **Runtime**: Located in `.roadbook/<roadbook_id>/runtime/` (internal system use).
- **Output Management**:
    - All execution outputs (downloads, screenshots, logs) MUST be saved in `.roadbook/<id>/outputs/<session_id>/`.
    - The scaffolded script automatically detects the `ROADBOOK_RUN_ID` environment variable and sets `OUTPUT_DIR` accordingly.
    - If running manually without CLI context, it falls back to a timestamped directory in `outputs/`.
- **Do not move to global**: Keep the script and artifacts in the workspace `.roadbook/` directory.
- **Verification**: Always verify the script works before finalizing.
