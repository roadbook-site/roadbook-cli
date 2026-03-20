---
name: roadbook-guide
description: Helps the user get started with the Roadbook CLI. It can list available roadbooks, check system health, explain commands, and guide the user through the 'init' and 'run' workflows. Use this skill when the user asks "how do I use roadbook?", "what can roadbook do?", "help me get started", or encounters errors and needs diagnostics.
---

# Roadbook Guide Skill

This skill helps the agent assist the user in navigating the Roadbook CLI ecosystem.

## Capabilities

1.  **Discovery**: Listing and searching for roadbooks.
2.  **Diagnostics**: Running health checks.
3.  **Onboarding**: Guiding the creation of a new roadbook.
4.  **Execution**: Helping the user run roadbooks.

## Workflows

### 1. System Health Check (First Step for Troubleshooting)
If the user reports issues or is just starting:
1.  Run `roadbook doctor`.
2.  Analyze the output. If dependencies are missing, suggest installing them.

### 2. Exploration
To see what roadbooks are available:
1.  Run `roadbook list` to show local roadbooks.
2.  Run `roadbook remote list` (if applicable/login required) to show remote ones.
3.  Use `roadbook search <term>` to find specific functionality.
4.  Use `roadbook show <name>` to display details before running.

### 3. Execution
When the user wants to run a task:
1.  Confirm the roadbook name.
2.  Use `roadbook run <name>` for automation.
3.  Explain that if automation fails, it may downgrade to "Semantic Mode" (interactive guide).
4.  Alternatively, use `roadbook open <name>` if they specifically want the interactive guide.

### 4. Creation (Quick Start)
To create a new roadbook:
1.  Run `roadbook init`.
2.  Follow the prompts (or ask user for name/description).
3.  Once initialized, suggest running `roadbook edit` to open the visual editor, or editing the files directly in `hooks/` or `steps/`.

## Common Commands Reference

- `roadbook list`: Show all local roadbooks.
- `roadbook doctor`: Check environment.
- `roadbook run <name>`: Execute automation.
- `roadbook init`: Create a scaffold.
- `roadbook edit`: Launch WebUI editor.
