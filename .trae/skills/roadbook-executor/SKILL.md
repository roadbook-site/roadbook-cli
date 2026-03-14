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
    - **Autonomous Explorer Mode**: If no script exists, it will switch to interactive guidance.

3.  **Autonomous Explorer Loop**:
    - Once a session is started, you are the **Explorer**.
    - Enter the loop:
        a.  **Get Sheet Context**: Run `roadbook next` to get the context and instructions for the current Sheet (Scene).
        b.  **Execute Autonomously**: Read the Sheet context. Use your browser automation tools (`agent-browser` or `playwright-cli`) to achieve the goal described in the Sheet. **You are free to execute multiple actions to complete the Sheet.**
        c.  **Verify Checkpoints**: If the Sheet has `Assertions` or `断言`, run `roadbook check` to review them and ensure your current browser state meets the requirements.
        d.  **Proceed**: Once you are confident the Sheet's goal is met, run `roadbook next` to get the next Sheet.
        e.  **Repeat**: Continue until `roadbook next` indicates all sheets are completed.

4.  **Error Handling & Script Generation**:
    - If an action fails, report the error to the user and ask for guidance or try to debug using `agent-browser` tools.
    - You can use `roadbook logs inspect <run_id>` to see detailed logs of the session.

## CLI Commands Reference

- `roadbook list`: List all installed roadbooks.
- `roadbook inspect <id>`: Show details of a roadbook (alias for `show`).
- `roadbook run <id>`: Execute a roadbook automatically (script-first).
- `roadbook open <id>`: Start an interactive session.
- `roadbook next`: Get the next instruction in an interactive session.
- `roadbook check`: Check the status of the current step.
- `roadbook logs list <id>`: View run history.

## Script Management

- **Do not delete generated scripts**: If you successfully generate a script that completes the task, **save it** instead of deleting it.
- **Installation**: Move the working script to the roadbook's script directory (usually found via `roadbook inspect`) so `roadbook run` can use it in the future.
- **Verification**: Always verify the script works before finalizing.
