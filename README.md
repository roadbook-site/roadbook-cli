# Roadbook CLI

[English](README.md) | [简体中文](README_zh.md)

Welcome to **Roadbook**, your AI agent's "Wilderness Trekking Guide" for browser automation.

Standard web automation often relies on fixed scripts that easily break when websites change—like a rigid map in a shifting landscape. Roadbook solves this by acting as an **Expedition Log**. It provides not just the necessary steps, but also environment diagnosis and flexible operational guidance. 

When your AI Agent (the Explorer) gets lost or a script fails, Roadbook (the System/Sherpa) provides the context and semantic hints needed to autonomously find a new path, fix the script, and complete the task.

## Key Concepts

- **Roadbook**: The Expedition Log. It records key landmarks (UI features), required paths, and actionable advice to dynamically navigate web interfaces.
- **Agent**: The Explorer. The AI agent that reads the Roadbook, makes decisions, and performs visual/semantic reasoning when standard scripts fail.
- **Guide/CLI**: The CLI and runtime system that handles the heavy lifting (browser driving, context management) and provides semantic guidance.

## Installation

### Install via pip (Recommended)

When Roadbook is published to PyPI, you can install the CLI directly:

```bash
pip install roadbook
```

### Install from Source

To install the latest version from source, clone the repository and install it in editable mode:

```bash
git clone https://github.com/roadbook-site/roadbook-cli.git
cd roadbook-cli
pip install -e .
```

## Quick Start & Examples

Roadbook is designed to be used in two main phases: **Exploring** (creating the roadbook) and **Executing** (running the task).

### 1. Creating a New Roadbook (Explorer Phase)

Initialize a new roadbook via the CLI. This sets up the necessary workspace and scaffolding, allowing an agent to explore a website and test interactions.

```bash
# Initialize a new roadbook for searching on Amazon
roadbook init my-first-task --description "Search for a product on Amazon" --entry-url "https://www.amazon.com"
```

This creates a new directory in your project containing the standard `roadbook.md` template and starter test scripts to begin exploration.

### 2. Executing a Roadbook (Executor Phase)

You can run a roadbook automatically (if a stable script exists) or in interactive guide mode where the agent gets semantic instructions to explore the environment.

```bash
# List available local roadbooks
roadbook list

# Option 1: Run via Fast Path (Automatic Script Execution)
# This will attempt to use pre-compiled automation scripts for fast execution.
roadbook run my-first-task

# Option 2: Run via Interactive Guide Mode (Semantic Exploration)
# Use this when the site has changed or no script exists. It displays the full markdown Roadbook to guide the agent in completing the steps.
roadbook run --guide my-first-task
```

### 3. Managing Roadbooks

The CLI provides tools to organize and review execution logs.

```bash
# View detailed information about a single roadbook
roadbook inspect my-first-task

# Link local roadbooks to the global library to share across your machine
roadbook link

# View execution logs and history for a specific roadbook
roadbook logs list my-first-task
```
