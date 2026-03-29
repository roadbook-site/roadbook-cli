# Roadbook SDK: Future Authentication Optimization Design

## 1. Background and Pain Point
Currently, Roadbook uses a declarative approach via `requires_login` in `roadbook.md` and prompts users during the `roadbook init --login y` phase. While this perfectly captures the session state initially and bypasses anti-bot mechanisms using a pure subprocess, it lacks a robust runtime enforcement mechanism. 

If the session expires during execution or an unexpected login page appears while the agent is running the script, the agent might fail or attempt to navigate the login UI (which is typically blocked by captchas).

## 2. Proposed Solution: The `@require_auth` Decorator
To address runtime authentication state loss and encapsulate the check logic, we propose an SDK-level decorator: `@require_auth`. 

This decorator will be applied to script Phase functions or the `run()` entry point to enforce that a valid session exists before executing the business logic.

### 2.1 Developer Experience
The agent or developer simply annotates the phase:

```python
from roadbook.sdk import RoadbookContext, require_auth

@require_auth(
    check_url="https://target-site.com/profile",
    check_selector="text='Welcome'",
    login_prompt="Please log in to your account and press Enter in the terminal."
)
def extract_data_phase(rb: RoadbookContext):
    # Business logic here, guaranteed to be in a logged-in state
    rb.page.goto("https://target-site.com/dashboard")
    ...
```

### 2.2 Decorator Lifecycle & Internal Logic

When the `@require_auth` decorator is triggered, it performs the following:

1. **Passive Verification**: 
   - Before the decorated function runs, the decorator silently opens the `check_url` in the background (using the existing `state.json` from `RoadbookContext`).
   - It verifies the login state using the `check_selector` or by evaluating the DOM/URL.

2. **Fast-Fail & Human-in-the-Loop Interception**:
   - **If logged in**: Execution proceeds to the phase function seamlessly.
   - **If NOT logged in (or state expired)**:
     - The decorator **pauses** the current execution.
     - It detaches the CDP session and uses `subprocess.Popen` to launch a pure Chrome instance (just like `roadbook init --login y`), rendering the login page without automation flags to avoid anti-bot detection. **Ensure to include arguments like `--no-first-run`, `--no-default-browser-check`, and `--disable-features=Translate` to prevent UI popups from interfering with the user.**
     - It displays the `login_prompt` in the user's terminal: *"Your session expired. Please log in on the opened browser, then press Enter here to resume."*
     - Upon the user pressing Enter, the decorator **forcefully kills the browser process tree** (to release the profile lock and ensure CDP ports will be respected on the next launch), and then uses headless Playwright to quickly extract the new `state.json`.
     - Finally, it re-attaches the CDP session, updates the `RoadbookContext` with the fresh state, and **resumes** the execution of the phase function.

## 3. Benefits of this Architecture

1. **Separation of Concerns**: The business logic (extracting data, clicking buttons) inside the phase function is completely decoupled from the authentication logic. The agent doesn't need to write conditional `if not logged_in:` blocks everywhere.
2. **Resilience**: It handles session expiration gracefully. The agent won't crash; it just pauses and waits for the human to refresh the session.
3. **Anti-Bot Compliance**: By reusing the "pure subprocess + state extraction" pattern for the intervention, it guarantees 100% login success rates without triggering captchas or blocks.
4. **Agent-Friendly**: The Agent only needs to know *how* to verify the login (`check_url`, `check_selector`), not *how* to orchestrate the complex state extraction and process management.

## 4. Next Steps for Implementation
1. Add `require_auth` to `src/roadbook/sdk/context.py` (or a new `auth.py` module in the SDK).
2. Refactor the subprocess-launching logic currently in `roadbook init` so it can be shared and called by the decorator during runtime.
3. Update the `RoadbookContext` to support hot-reloading `state.json` without destroying the entire context if possible.
4. Update `SKILL.md` to instruct the Agent on how to use `@require_auth` for sites that have `requires_login: true`.