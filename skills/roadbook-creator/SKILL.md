---
name: roadbook-creator
version: "0.1.0"
description: Trigger this skill when the user wants to "generate a roadbook" (生成一个路书), "crawl a webpage" (爬取网页), "crawl based on this screenshot" (按照截图爬取), or build an automation workflow from a visual/textual prompt. This skill guides the agent to interactively collect user intent, analyze provided screenshots, ask clarifying questions, and finally generate a rich and comprehensive `roadbook.md` and project scaffold. It also handles requests to "modify" or "update" an existing roadbook's name or attributes.
---

# Roadbook Creator

This skill guides the Agent to interactively collaborate with the user to design and generate a comprehensive Roadbook from initial intent (text or screenshots). 

## Core Philosophy
1. **Interactive Elicitation**: Don't just run `roadbook init` blindly. Engage the user to extract maximum context (target URL, desired data fields, interaction steps, constraints like login/captcha) before generating code.
2. **Visual Context First**: If the user provides a screenshot, analyze it thoroughly to deduce the website, the layout, and the likely target elements. Give the user the feeling of "manipulating the agent" to create the script step by step.
3. **Rich Generation**: Instead of a bare-bones initialization, generate a fully populated `roadbook.md` with well-defined sheets, actions, and constraints based on the gathered context.

## Workflow

### Step 1: Intent & Visual Analysis (Information Gathering)
When the user triggers this skill (e.g., by providing a screenshot and saying "generate a roadbook for this"):
- **Acknowledge and Analyze**: If a screenshot is provided, explicitly tell the user what you see. Identify the website (if visible), the main data list, filters, pagination, or forms.
- **Identify Gaps**: Determine what information is missing to create a robust automation script:
  - What is the exact Entry URL?
  - Does the site require a login?
  - What specific fields need to be extracted?
  - Are there any user interactions required (e.g., clicking "Next", filling a search box)?
- **Ask Clarifying Questions**: Ask the user 1 to 3 targeted questions to fill the gaps. Use the `AskUserQuestion` tool if appropriate, or just ask conversationally. Wait for the user's response. Do this interactively rather than demanding everything at once.

### Step 2: Schema Design
Before scaffolding, present the proposed Input and Output schemas to the user:
- Show a markdown table of the data fields you plan to extract (e.g., `title`, `price`, `rating`).
- Ask the user if they want to add or remove any fields.

### Step 3: Project Scaffolding
Once you have enough context and the user confirms the schema:
1. Suggest a project name (`kebab-case`).
2. Run the initialization command to create the base structure:
   `roadbook init <project-name> --description "<description>" --entry-url "<url>"`
3. If login is required based on the conversation, append `--login y` to the command if applicable.

### Step 4: Rich Roadbook Generation
After scaffolding, DO NOT leave `roadbook.md` in its default state.
1. Read the newly created `<project-name>/roadbook.md`.
2. Rewrite `roadbook.md` to be rich and detailed based on the user's intent and screenshot analysis:
   - **Setup Sheet**: Add any constraints (e.g., `requires_login: true`, `stealth_mode: true`).
   - **Interaction Sheets**: Break down the workflow into logical sheets (e.g., `Sheet: Search Product`, `Sheet: Extract List`, `Sheet: Pagination`).
   - **Delivery Sheet**: Explicitly list the output JSON schema/fields that the user requested.
3. Update `<project-name>/scripts/script.py` to include the appropriate `TaskInput` and `TaskOutput` Pydantic models based on the confirmed schema.
4. Update `<project-name>/.rb/INPUT.json` with sample inputs.

### Step 5: Handoff to Explorer
Once the rich `roadbook.md` and schema are generated, present the structure to the user.
Explain what you have built and suggest that they can now use the `roadbook-explorer` skill to start writing the actual implementation code, or they can run `roadbook run <project-name>`.

## Modifying an Existing Roadbook

If the user wants to modify an already generated Roadbook project (e.g., change its name or update its login requirement), follow these specific modification logic guidelines:

### 1. Renaming a Roadbook
When the user wants to change the name of an existing Roadbook, ensure you update all relevant references:
- **`roadbook.md`**: Update the `id:` and `name:` fields in the YAML frontmatter.
- **`scripts/script.py`**: 
  - Update the docstring at the top.
  - Update the `rb_id` parameter where the context is initialized: `with RoadbookContext(rb_id="new-id", ...)`.
- **Directory Name**: Suggest or automatically rename the root project directory to match the new `rb_id`.

### 2. Changing Login Requirements
When the user wants to change the `requires_login` attribute:
- **From "No Login" to "Login Required"**:
  - **`roadbook.md`**: Add `- requires_login: true` to the `Constraints` list under the `initialization` (setup) sheet.
  - **`scripts/script.py`**: Update the `site_constraints` dictionary to include `"requires_login": True`. Add or uncomment the authentication logic (e.g., `rb.auth.ensure_login(...)`) in the appropriate phase function.
  - **Inputs**: If explicit credentials are needed, update the `TaskInput` Pydantic model in `script.py` and the sample `.rb/INPUT.json` to include username/password fields.
- **From "Login Required" to "No Login"**:
  - **`roadbook.md`**: Remove `- requires_login: true` or change it to `false`.
  - **`scripts/script.py`**: Remove `"requires_login": True` from `site_constraints` and comment out or remove the `rb.auth.ensure_login(...)` logic.

## DO's and DON'Ts
- **DO** be highly conversational and enthusiastic. Show the user that you understand their visual inputs.
- **DO** deduce schemas automatically from screenshots (e.g., "I see product name, price, and rating. I will add these to the Output Schema").
- **DO** use markdown tables to show the user the proposed schema before writing it to files.
- **DON'T** rush to run `roadbook init` before you know the entry URL and the main objective.
- **DON'T** write the complex Playwright code in this skill. The goal here is **design and scaffolding**. The `roadbook-explorer` skill handles the code implementation.
