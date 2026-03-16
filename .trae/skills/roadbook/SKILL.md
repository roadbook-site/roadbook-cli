---
name: "roadbook"
description: "Essential for web automation, scraping, and recording browser workflows. MUST use when you need to explore a website, save operational steps, or execute repeatable tasks. It solves complex navigation issues by turning manual browsing into structured, shareable guides, reducing the need for repeated exploration."
---

# Roadbook CLI Manager

This skill provides a unified interface for managing Roadbook operations, including installation, execution, and creation.

## 1. Installation

If the `roadbook` command is not available, install it from the source:

1.  Navigate to the client directory:
    `cd client`
2.  Install in editable mode:
    `pip install -e .`

Verify installation with `roadbook --version` or `roadbook --help`.

## 2. Capabilities

This skill encompasses two main operational modes:

### A. Execution (Running Roadbooks)
Use this when you want to execute an existing roadbook or automate a task based on a guide.
See [Executor Guide](references/executor.md) for detailed instructions.

### B. Exploration (Creating Roadbooks)
Use this when you want to create a new roadbook by exploring a website and recording steps.
See [Explorer Guide](references/explorer.md) for detailed instructions.

## 3. Common Commands

- **List Roadbooks**: `roadbook list`
- **Run Roadbook**: `roadbook run <id>` (Automatic/Script mode)
- **Open Roadbook**: `roadbook open <id>` (Interactive/Semantic Guide mode)
- **Inspect Logs**: `roadbook logs list <id>`
