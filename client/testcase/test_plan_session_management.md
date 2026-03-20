# Roadbook Session Management & Scaffold Verification Test Plan

## 1. Objective
Verify the correctness and robustness of the updated `scaffold.py` logic, specifically:
1. The `get_playwright_context` utility handles `Fresh`, `CDP`, and `Storage State` modes correctly.
2. The generated Python script template correctly passes these parameters.
3. The Session Auto-Update mechanism works as intended when using Storage State.

## 2. Test Environment
- **Workspace**: `C:\code_dev\roadbook\test`
- **Target Site**: `https://jimeng.jianying.com/ai-tool/generate/?type=video&workspace=0` (Requires Authentication)
- **Tools**: Chrome (Canary/Stable), `roadbook-explorer`, `playwright`

## 3. Test Scenarios

### Case 1: CDP Connect Mode (User Specific)
*Validates the ability to hook into an existing, authenticated browser session.*

*   **Pre-condition**:
    *   Chrome started with `--remote-debugging-port=9224`.
    *   User is logged into `jimeng.jianying.com`.
*   **Action**:
    1.  Use `roadbook-explorer` to generate a roadbook `jimeng_scraper` targeting the URL.
    2.  Execute the generated script with input: `{"cdp_url": "http://localhost:9224"}`.
*   **Expected Result**:
    *   Script connects to the existing browser window.
    *   No login page is shown (session reused).
    *   Script successfully extracts the 5 latest videos.
    *   Browser remains open after script completion (CDP usually keeps browser alive, though context closing depends on implementation).

### Case 2: Storage State Generation (Prep for Case 3)
*Validates that we can capture a session from an authenticated CDP session.*

*   **Pre-condition**: Same as Case 1.
*   **Action**:
    *   Create a temporary helper script (or use a Roadbook step) that connects via CDP and calls `context.storage_state(path="jimeng_auth.json")`.
*   **Expected Result**:
    *   `jimeng_auth.json` is created and contains valid Cookies/LocalStorage.

### Case 3: Storage State Mode (Cold Start)
*Validates the ability to restore a session in a fresh browser.*

*   **Pre-condition**:
    *   Close the Debugging Chrome (9224).
    *   `jimeng_auth.json` exists.
*   **Action**:
    1.  Execute the `jimeng_scraper` script with input: `{"storage_state": "./jimeng_auth.json"}`.
*   **Expected Result**:
    *   A new browser launches (headless or headed).
    *   Page opens directly to the Dashboard (Login skipped).
    *   Script succeeds.

### Case 4: Storage State Auto-Update (Rolling Session)
*Validates that the script updates the session file after execution.*

*   **Pre-condition**: `jimeng_auth.json` exists.
*   **Action**:
    1.  Note the modification time of `jimeng_auth.json`.
    2.  Run Case 3 again.
*   **Expected Result**:
    *   Script runs successfully.
    *   `jimeng_auth.json` modification time is updated (proving the auto-save logic in `finally` block worked).

### Case 5: Fresh Browser (Negative/Baseline Test)
*Validates default behavior without session injection.*

*   **Action**:
    1.  Execute `jimeng_scraper` with empty inputs `{}`.
*   **Expected Result**:
    *   New browser launches.
    *   Redirects to Login Page.
    *   Script likely fails (element not found) or extracts nothing, confirming that auth is indeed required.

## 4. Execution Plan (Immediate Next Step)

We will proceed with **Case 1** as requested:

1.  **Launch Chrome**: Ensure user has Chrome open on port 9224.
2.  **Generate Roadbook**: Use `roadbook-explorer` to scaffold the scraping logic.
3.  **Refine & Run**: Verify the generated code and run via `roadbook run` or direct python execution with CDP args.
