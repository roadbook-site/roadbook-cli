---
name: roadbook-explorer
description: Guide the agent to create a new Roadbook by exploring a website, generating intermediate scripts, and finalizing a standard `roadbook.md` file. Invoke when the user wants to "create a roadbook", "explore a site", or "generate a workflow" for a website.
---

# Roadbook Explorer

This skill guides the Agent to create a robust, standard-compliant Roadbook by exploring a website. It bridges the gap between the Agent's preferred mode (writing/running scripts) and the Human's preferred format (declarative `roadbook.md`).

## Core Philosophy
1.  **Standardization**: Always use `roadbook init` to create the scaffold.
2.  **Separation of Concerns**: Use the **Runtime Script (`script.py or script.js`)** for exploration, but the **Roadbook (`roadbook.md`) is the Single Source of Truth**.
3.  **Fast Fail**: If sophisticated login/captcha is encountered, pause and ask for human help.

## Workflow

### Phase 1: Initialization (Scaffold)
1.  **Context Check**:
    -   Confirm the current working directory.
    -   Ensure `roadbook` CLI is available (`roadbook --version`).
2.  **Intent Analysis & Generalization**:
    -   **Generalize**: Convert the user's specific request into a generic, reusable task.
        -   *Example*: "Find an iPhone 15 on Amazon" → **Goal**: "Search for a product on Amazon".
    -   **Identify Inputs**: Determine what values should be parameters.
        -   *Example*: `keyword` ("iPhone 15"), `max_price`.
    -   **Identify Outputs**: Determine what data should be extracted.
        -   *Example*: `product_title`, `price`, `url`.
    -   **Naming**: Propose a concise `kebab-case` name (e.g., `amazon-product-search`).
3.  **Scaffolding**:
    -   Run: `roadbook init <name> --goal "<generalized_goal>"`.
    -   *Note*: The `init` command creates the folder structure at `.roadbook/<id>/`.

### Phase 2: Exploration & Fast Fail
*The Agent should iterate in this phase until the goal is achieved.*

1.  **Scripting Configuration**:
    -   **Browser Setup**: Check `.roadbook/<id>/scripts/utils/browser.py`. This module handles browser initialization. You can adapt it to match the user's preferred connection method (e.g., `launch` for isolated sessions or `connect_over_cdp` for attaching to an existing browser).
    -   **Transient Tests**: If you need to create temporary scripts to test selectors or connections, **MUST** place them in `.roadbook/<id>/scripts/tests/`. Do NOT create files in the project root.
2.  **Develop Workflow**:
    -   Modify `.roadbook/<id>/scripts/script.py` to implement the logic.
    -   Leverage the pre-configured `logger` and `get_playwright_context` helper.
3.  **Fast Fail Strategy (Crucial)**:
    -   **Identify Barriers**: Watch for **Login screens**, **CAPTPHAs**, or **Bot Verification**.
    -   **Stop & Ask**: If blocked, **STOP IMMEDIATELY**. Do not attempt to bypass. Request human intervention.
4.  **Verify & Sync**:
    -   Run the script: `python .roadbook/<id>/scripts/script.py` (ensure you are using the correct python environment).
    -   **Path Cleaning**: Isolate the successful path; remove dead ends.
    -   **Sync**: As steps are verified, proceed to formal transcription.

### Phase 3: Transcription (The AARP Standard)
*Convert the verified script logic into the `roadbook.md` format.*

1.  **Translate Actions**:
    -   Convert Python Playwright calls to **AARP Action Primitives**:
        -   `page.goto(url)` -> `GOTO "url"`
        -   `page.click(selector)` -> `CLICK "selector"`
        -   `page.fill(selector, value)` -> `INPUT "selector" "value"`
        -   `page.wait_for_selector(sel)` -> `WAIT "sel"`
2.  **Semantic Enrichment**:
    -   **Selectors**: Use **Semantic Selectors** (text, role, label) over brittle CSS/XPath where possible.
    -   **Parameters**: Replace hardcoded values with variables defined in Frontmatter (e.g., `{keyword}`).
3.  **Update Roadbook**:
    -   Read `.roadbook/<id>/roadbook.md`.
    -   Replace the placeholder `Steps` with the transcribed actions.
    -   Save the file.

### Phase 4: Finalization
1.  **Sync Verification**:
    -   Ensure the `roadbook.md` (ontology) matches the proven `script.py` (runtime).
2.  **Human Review**:
    -   Display the final Roadbook structure.
    -   If the user wants to refine steps (e.g., add business logic comments), suggest running: `roadbook edit <id>`.
3.  **Execution**:
    -   If the Roadbook is confirmed, instruct the user to validate the full end-to-end flow:
    -   Run: `roadbook run <id>`.

## Best Practices
-   **Variables**: If the script uses a hardcoded value (e.g., "iPhone 15"), replace it with a variable placeholder in the Roadbook (e.g., `{keyword}`) and add it to the `inputs` section in Frontmatter.
-   **Visuals**: If a step is complex, ask the user if they want to capture a screenshot (Reference Image) for that step.
-   **Validation**: Add assertion steps (e.g., "Check if price is displayed") to make the roadbook robust.
