# The Internet - Dynamic Loading Execution Log

## Execution Summary
- **Target**: `https://the-internet.herokuapp.com/dynamic_loading/2`
- **Goal**: Verify handling of elements that appear asynchronously after a delay (AJAX/JS loading).
- **Method**: executed `library/the_internet_dynamic_loading.yaml` using `roadbook-stepper` (manual agent-driven execution via `agent-browser`).

## Key Observations
1.  **Wait Logic is Critical**: The original roadbook used `wait: dom_stable`. In the CLI (`agent-browser`), there's no direct equivalent for "wait until stable" other than network idle, which doesn't always guarantee element visibility. The most robust strategy found was to **wait for a specific element** (the "Hello World!" heading) to appear in the snapshot.
2.  **Dynamic ID Re-indexing**:
    -   Initial state: `Start` button was `@e3`.
    -   After click & wait: New element `Hello World!` appeared as `@e3` (reusing the ID slot or shifting indices).
    -   **Insight**: This confirms that hardcoding IDs like `@e3` is impossible. Agents/Runners *must* re-evaluate the snapshot after every major DOM change (navigation, click that triggers load).
3.  **Verification**: The `extract` action is effectively an assertion. By finding the element with `role: heading` and `keyword: "Hello World!"` in the snapshot, we confirm the test passed.

## Roadbook Improvements (Planned v1.1)
- **Refining `wait` action**: Deprecate generic `dom_stable` in favor of `element_visible`. The `wait` step should explicitly reference the *landmark* it is waiting for. This creates a "Wait for X" logic which is easier to implement in both Agent (loop snapshot until X appears) and Code (Playwright `waitForSelector`).
- **Clarification**: Added explicit timeouts to guide the Agent/Runner on how long to wait before failing.

## Next Steps
- Implement `wait` and `extract` logic in `run_rpa.py` to support this pattern programmatically.
