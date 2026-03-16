---
name: "roadbook-explorer"
description: "Explores a website to achieve a user goal and generates a new Roadbook file. Invoke when the user wants to create a Roadbook or explore a new task/site."
---

# Roadbook Explorer

This skill helps you create a new Roadbook by exploring a website and recording the steps required to achieve a specific goal.

## Usage

1.  **Understand the Goal**:
    - Clarify the user's objective (e.g., "Login to Amazon", "Search for a product").
    - Identify the starting URL.

2.  **Start Exploration**:
    - Use browser automation tools (like `agent-browser` or `playwright-cli`) to navigate to the starting URL.
    - Perform actions to achieve the goal (click, type, navigate).
    - **Crucial**: Keep track of every action you take (URL, selector, value, description).

3.  **Draft the Roadbook**:
    - Once the goal is achieved, organize the recorded steps into the Roadbook AARP format.
    - **Structure**:
        - **Meta**: ID, Name, Description, Version.
        - **Steps**: A list of steps, each with:
            - `id`: Unique step ID.
            - `action`: The action type (e.g., `open`, `click`, `type`).
            - `params`: Parameters for the action (url, selector, text).
            - `description`: A human-readable description of what the step does.
            - `validation`: (Optional) How to verify the step succeeded.

4.  **Save the Roadbook**:
    - Generate a valid Roadbook YAML/Markdown content.
    - Ask the user where to save it, or default to `~/.roadbook/<new_id>/roadbook.md`.
    - Use `write` tool to save the file.

5.  **Verify**:
    - (Optional) detailed run of the new roadbook using `roadbook-executor` to ensure it works.

## Best Practices

- **Selectors**: Use robust selectors (e.g., IDs, data attributes) where possible. Avoid brittle XPath or long CSS chains.
- **Granularity**: Keep steps atomic (one action per step).
- **Descriptions**: Write clear, instructive descriptions for each step.
- **Validation**: Include validation steps (e.g., "Check if 'Login Successful' text appears") to make the roadbook robust.
