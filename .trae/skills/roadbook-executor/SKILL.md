---
name: "roadbook-executor"
description: "Executes a Roadbook by following its instructions step-by-step using the CLI and browser automation tools. Invoke when the user wants to run or execute a specific Roadbook."
---

# Roadbook Executor

This skill helps you execute a Roadbook, which is a structured guide for automating browser tasks.

## Usage

1.  **Identify the Roadbook**:
    - Use `roadbook list` to see available roadbooks.
    - If the user provides a name or ID, try to find it in the list.

2.  **Start Execution**:
    - **Automatic Mode**: Try `roadbook run <id>` first. This will attempt to use any existing automation scripts.
    - **Semantic Guide Mode**: If no script exists, it will switch to interactive guidance.

3.  **Semantic Guide Execution**:
    - Once a session is started (via `roadbook run <id>` or `roadbook open <id>`), the **Full Roadbook Content** will be displayed.
    - You are the **Executor**.
    - **Session Context**: The CLI provides a Session ID (e.g., `run_20260315_...`). Use this ID to organize artifacts if you are running manual commands.
    - **Read and Execute**: Read the entire Roadbook content (all Sheets) carefully.
    - **Sequential Execution**: Execute the tasks in each Sheet sequentially using your browser automation tools (`agent-browser` or `playwright-cli`).
    - **Self-Verification**: Verify the "Assertions" (if any) in each Sheet yourself using browser checks (e.g., checking element visibility or text).
    - **Completion**: Once you have completed all Sheets, you can consider the task done.

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
    - If an action fails, report the error to the user and ask for guidance or try to debug using `agent-browser` tools.
    - You can use `roadbook logs inspect <run_id>` to see detailed logs of the session.

## CLI Commands Reference

- `roadbook list`: List all installed roadbooks.
- `roadbook inspect <id>`: Show details of a roadbook (alias for `show`).
- `roadbook run <id>`: Execute a roadbook automatically (script-first) or open interactive mode.
- `roadbook open <id>`: Start an interactive session and view the full roadbook.
- `roadbook logs list <id>`: View run history.

## Script Management & Artifacts

- **IMPORTANT - Reusability & Token Efficiency**: Scripts are the core of Roadbook's efficiency. They can be reused without consuming tokens. **Always strive to generate a robust script instead of relying on interactive semantic execution every time.**
- **Workspace Structure**: Roadbooks are executed in a dedicated workspace directory: `.roadbook/<roadbook_id>/`.
    - **Scripts**: Located in `.roadbook/<roadbook_id>/scripts/script.py`.
    - **Runtime Artifacts**: Located in `.roadbook/<roadbook_id>/runtime/`.
- **Auto-Scaffolding**: When `roadbook open <id>` is executed:
    1.  The system copies the roadbook from the global library (`~/.roadbook/<id>/`) to `.roadbook/<id>/` in the current workspace.
    2.  It scaffolds a template script in `.roadbook/<id>/scripts/script.py`.
    3.  **Edit this file directly** to implement automation logic.
- **Output Management**:
    - All execution outputs (downloads, screenshots, logs) MUST be saved in `.roadbook/<id>/runtime/runs/<session_id>/artifacts/`.
    - The scaffolded script automatically detects the `ROADBOOK_RUN_ID` environment variable and sets `OUTPUT_DIR` accordingly.
    - If running manually without CLI context, it falls back to a timestamped directory.
- **Do not move to global**: Keep the script and artifacts in the workspace `.roadbook/` directory.
- **Verification**: Always verify the script works before finalizing.
