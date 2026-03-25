---
name: roadbook-explorer
version: "0.1.7"
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

1. **Check installed Roadbook version**:
   ```bash
   roadbook --version
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
   ```
  Ensure `roadbook --version` equals the skill header `version`.

## Core Philosophy
1. **Standardization**: Always use `roadbook init` to create the scaffold.
2. **Context-in-Place**: The generated `script.py` and `tests/` directory contain specific `[AGENT INSTRUCTION]` blocks. **ALWAYS read these instructions within the generated files** before coding.
3. **SDK-Driven**: ALWAYS use `roadbook.sdk.RoadbookContext` for lifecycle, logging, and I/O. Strictly use `with rb.sheet("Sheet Name")` to declare steps and `rb.push_data()` for outputs. NEVER mention or use `agent-browser`.
4. **Script Sheet Workflow**: Before finalizing the markdown, structure your script's outputs programmatically (Script Sheet). Review, clean, and then sync to `roadbook.md` as the Single Source of Truth.
5. **Fast Fail**: If sophisticated login/captcha is encountered, pause and ask for human help.

## DO's and DON'Ts
**✓ Do:**
- **DO** always read the `[AGENT INSTRUCTION]` comments in the generated `script.py` and `sample_test.py` after scaffolding.
- **DO** use the `tests/` directory for micro-testing complex UI elements before merging logic into `script.py`.
- **DO** ask the user for help (`AskUserQuestion`) immediately if you encounter a CAPTCHA or Login Wall.
- **DO** use semantic selectors (e.g., `get_by_role`, `get_by_text`) whenever possible.
- **DO** conditionally use `cdp_url` in `RoadbookContext(cdp_url="...")` inside `script.py` if requested or if you need an existing browser.

**✗ Don't:**
- **DON'T** skip the version check step. It must be done before anything else.
- **DON'T** delete or bypass `RoadbookContext` in `script.py` to use raw Playwright API manually. The SDK handles lifecycle safely.
- **DON'T** attempt to bypass or brute-force Login screens or CAPTCHAs autonomously.
- **DON'T** create temporary test files in the project root. Always use `.roadbook/<id>/scripts/tests/`.
- **DON'T** hardcode search queries or dynamic parameters in the script; extract them to the `inputs` section.
- **DON'T** put environment configurations (like CDP debugging ports or headless flags) inside `inputs` or `roadbook.md`. Those are strictly for business data and domain variables.

## Workflow

### Phase 1: Initialization & Scaffolding
1.  **Context Check (MANDATORY)**: Ensure `roadbook` CLI is available and version MATcHES exactly (`roadbook --version`). If not, upgrade or update immediately as per the frontmatter check.
2.  **Intent Analysis**: Convert the user's request into a generic goal (e.g., "Find an iPhone 15 on Amazon" → "Search for a product on Amazon"). Propose a `kebab-case` name.
3.  **Scaffolding**: Run `roadbook init <name> --description "<generalized_goal>" --entry-url "<target_url>"`
4.  **Complex Task Triage**: If the task involves multi-step workflows or complex dynamic UIs, **STOP HERE**. Instruct the user to run `roadbook edit <id>` to manually define the high-level steps first.

### Phase 2: Exploration (Test-Driven)
*The Agent should iterate in this phase until the goal is achieved.*
1.  **Micro-Testing**: Open `.roadbook/<id>/scripts/tests/sample_test.py` and read the instructions. Write minimal tests for complex interactions here first.
2.  **Develop Workflow**: Read and modify `.roadbook/<id>/scripts/script.py`. Follow the inline `[AGENT INSTRUCTION]` blocks for selectors and artifact handling. Use `rb.sheet` to map your logic to sheets.
3.  **Programmatic Output (Script Sheet)**: Output structured data (JSON/dict) representing the discovered workflow steps and outputs using `rb.push_data()`.
4.  **Verify & Sync**: Run the script to verify. Clean up dead ends and isolate the successful path.

### Phase 3: Transcription (Sync to Roadbook)
1.  **Translate & Review**: Review the programmatic Script Sheet output. Clean up invalid data, deduplicate, and add context.
2.  **Translate Actions**: Convert the verified Python Playwright calls into AARP Action Primitives. (Refer to the `[AGENT INSTRUCTION - AARP TRANSLATION GUIDE]` inside the generated `script.py`).
3.  **Update Roadbook**: Open `.roadbook/<id>/roadbook.md`, replace the placeholder sheets, and finalize expected outputs in the `## Delivery` sheet based on your reviewed Script Sheet.

### Phase 4: Finalization
1.  **Sync Verification**: Ensure the `roadbook.md` matches the proven `script.py`.
2.  **Human Review**: Display the final Roadbook structure and suggest the user run `roadbook run <id>` to validate the full end-to-end flow.
