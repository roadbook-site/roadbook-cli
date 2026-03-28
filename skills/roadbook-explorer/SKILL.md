---
name: roadbook-explorer
version: "0.2.1"
description: Guide the agent to create a new Roadbook by exploring a website, generating intermediate scripts, and finalizing a standard `roadbook.md` file. Invoke when the user wants to "create a roadbook", "explore a site", or "generate a workflow" for a website.
---

# Roadbook Explorer

This skill guides the Agent to create a robust, standard-compliant Roadbook by exploring a website. 

## Requirements

- Ensure Python is available before exploration (`python --version`).
- Ensure the Roadbook CLI is installed:
	- Linux: `pip3 install roadbook`
	- macOS/Windows: `pip install roadbook`

### ⚡ Version Compatibility Check (DO THIS FIRST)

This skill requires the Roadbook package version to match the skill frontmatter `version`.
Use the `version` value in this file header as the single source of truth.

> **Note**: If the `roadbook` command is not found, use `python -m roadbook` instead.

1. **Check installed Roadbook version**:
   ```bash
   roadbook --version
   # OR
   python -m roadbook --version
   ```

2. **Version mismatch scenarios**:
   - **If installed version < skill header `version`**: Upgrade the package
     ```bash
     pip install --upgrade roadbook
     ```
   - **If installed version > skill header `version`**: This skill is outdated; update it
     ```bash
     npx skills update roadbook-site/roadbook-cli --skill roadbook-explorer
     ```

3. **Verify compatibility**:
   ```bash
   roadbook --version
   # OR
   python -m roadbook --version
   ```
  Ensure the version equals the skill header `version`.

## Core Philosophy
1. **Standardization**: Always use `roadbook init` to create the scaffold.
2. **Context-in-Place**: The generated `script.py` and `tests/` directory contain specific `[AGENT INSTRUCTION]` blocks. **ALWAYS read these instructions within the generated files** before coding.
3. **SDK-Driven**: ALWAYS use `roadbook.sdk.RoadbookContext` for lifecycle, logging, and I/O. Strictly use `with rb.sheet("Sheet Name")` to declare steps. **CRITICAL**: Use `rb.emit_output()` ONLY for the final data matching the `TaskOutput` schema, not for intermediate variables (use `rb.state`, `rb.kv`, or function returns instead).
4. **Site Constraints**: Support special execution environments (like captchas, stealth mode, or specific viewports) by accurately documenting and extracting `**Constraints**:` from `roadbook.md` and passing them via the `site_overrides` parameter to `RoadbookContext` in `script.py`.
5. **Script Sheet Workflow**: Before finalizing the markdown, structure your script's outputs programmatically (Script Sheet). Review, clean, and then sync to `roadbook.md` as the Single Source of Truth.
6. **Fast Fail**: If sophisticated login/captcha is encountered, pause and ask for human help.

## DO's and DON'Ts
**✓ Do:**
- **DO** always read the `[AGENT INSTRUCTION]` comments in the generated `script.py` and `sample_test.py` after scaffolding.
- **DO** use the `tests/` directory for micro-testing complex UI elements before merging logic into `script.py`.
- **DO** ask the user for help (`AskUserQuestion`) if you receive unclear prompt objectives.
- **DO** guide the user to configure settings (like API keys or specific credentials) if the task requires them, explaining where and how to set them up.
- **DO** define any required site-specific environmental conditions (e.g., `auto_solve_captcha: true`, `stealth_mode: true`) under a `**Constraints**:` block in the setup sheet of `roadbook.md`, and pass them via `site_overrides` when initializing `RoadbookContext` in `script.py`.
- **DO** strictly use `rb.wait_for_human_action(wait_for_user_input=True)` when encountering login structures or CAPTCHAs. Rely on the SDK for state management.
- **DO** remind the user to run scripts requiring human intervention in their own visible terminal, as the agent's background terminal may not display browser UI properly.
- **DO** use semantic selectors (e.g., `get_by_role`, `get_by_text`) whenever possible.

**✗ Don't:**
- **DON'T** manually edit `input_schema.json` or `output_schema.json`. Always update the Pydantic models in `script.py` instead.
- **DON'T** skip the version check step. It must be done before anything else.
- **DON'T** delete or bypass `RoadbookContext` in `script.py` to use raw Playwright API manually. The SDK handles lifecycle safely.
- **DON'T** attempt to bypass or brute-force Login screens or write automated password inputs. Always use `rb.wait_for_human_action`.
- **DON'T** run scripts that require `wait_for_human_action` silently in the background; always prompt the user to execute them in their visible terminal.
- **DON'T** create your own local storage, browser initialization overrides, or CDP configs.
- **DON'T** create temporary test files in the project root. Always use `scripts/tests/`.
- **DON'T** hardcode search queries or dynamic parameters in the script; extract them to the `inputs` section.
- **DON'T** put environment configurations (like debugging ports or headless flags) inside `inputs` or `roadbook.md`. Those are strictly for business data and domain variables.

## Project Directory Structure
All roadbook projects follow a standard directory structure:
- **`.rb/`**: Local configuration layer (e.g., `.rb/config.yaml`). Do not hardcode project paths; the system uses this folder to identify the project root. Configuration loading follows a waterfall flow:
    1. Project Config (`./.rb/config.yaml`) - highest priority.
    2. User Config (`~/.roadbook/.core/config.yaml`).
    3. Default Config.
- **`scripts/`**: Automation scripts (e.g., `scripts/script.py`, `scripts/utils/`).
- **`outputs/`**: Business outputs and data extraction results.
  - **`run_{run_id}/`**: Every execution (both local development and production) generates a unique UUID for historical tracking, auditing, and preventing data overlap. Contains `result.jsonl` (or `.csv`/`.json`) and a `downloads/` directory.
- **`runtime/`**: Execution state, logs, and screenshots for debugging (stored in `runtime/run_{run_id}/`).

## Workflow

### Phase 1: Initialization & Scaffolding
1.  **Context Check (MANDATORY)**: Ensure `roadbook` CLI is available and version MATcHES exactly (`roadbook --version`). If the command is not found, use `python -m roadbook` instead. If not, upgrade or update immediately as per the frontmatter check.
2.  **Intent Analysis & Parameter Extraction**: Convert the user's request into a generic goal (e.g., "Find an iPhone 15 on Amazon" → "Search for a product on Amazon"). Propose a `kebab-case` name.
    - **CRITICAL**: Differentiate between the "Target Site" (Entry URL) and "Business Parameters" (e.g., search queries, `max_items`, filters). The `entry_url` belongs to the Roadbook's core identity, while business parameters belong in `input_schema.json`.
3.  **Scaffolding**: Run `roadbook init <name> --description "<generalized_goal>" --entry-url "<target_url>"` (or `python -m roadbook init ...`). This creates a new project directory `<name>`. In a separate command, move into it with `cd <name>`.
4.  **Schema Configuration**: Open `scripts/script.py` and `.rb/INPUT.json`. Modify the `TaskInput` and `TaskOutput` Pydantic models in `script.py` to define the specific business parameters you extracted in Step 2. Then, update `.rb/INPUT.json` to provide mock values matching the `TaskInput` schema. Do NOT edit the JSON schema files directly.
5.  **Complex Task Triage**: If the task involves multi-step workflows or complex dynamic UIs, **STOP HERE**. Instruct the user to run `roadbook edit <id>` to manually define the high-level steps first.

### Phase 2: Exploration (Test-Driven)
*The Agent should iterate in this phase until the goal is achieved.*
1.  **Micro-Testing**: Open `scripts/tests/sample_test.py` and read the instructions. Write minimal tests for complex interactions here first.
2.  **Develop Workflow**: Read and modify `scripts/script.py`. 
    - **Selectors**: The selectors generated by `roadbook init` are just placeholders. You MUST use the browser inspector or DOM analysis to find the **real** DOM selectors and replace the placeholders.
    - **Anti-bot**: `roadbook init` does not handle advanced anti-bot measures. If the site has strong protections, you must implement the bypasses yourself (e.g., using stealth plugins or custom headers).
    - Follow the inline `[AGENT INSTRUCTION]` blocks for artifact handling. Use `rb.sheet` to map your logic to sheets.
3.  **Programmatic Output (Script Sheet)**: Output structured data (JSON/dict) representing the discovered workflow steps and outputs using `rb.emit_output()` (only final data matching `TaskOutput`).
4.  **Verify & Sync**: Run the script to verify. Clean up dead ends and isolate the successful path.

### Phase 3: Transcription (Sync to Roadbook)
1.  **Translate & Review**: Review the programmatic Script Sheet output. Clean up invalid data, deduplicate, and add context.
2.  **Translate Actions**: Convert the verified Python Playwright calls into AARP Action Primitives. (Refer to the `[AGENT INSTRUCTION - AARP TRANSLATION GUIDE]` inside the generated `script.py`).
3.  **Update Roadbook**: Open `roadbook.md`, replace the placeholder sheets, and finalize expected outputs in the `## Delivery` sheet based on your reviewed Script Sheet.

### Phase 4: Finalization
1.  **Sync Verification**: Ensure the `roadbook.md` matches the proven `script.py`.
2.  **Human Review**: Display the final Roadbook structure and suggest the user run `roadbook run <id>` to validate the full end-to-end flow.
