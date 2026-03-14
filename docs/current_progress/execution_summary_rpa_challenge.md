# RPA Challenge Loop Log

## Execution Summary
- **Target**: `https://rpachallenge.com/`
- **Goal**: Verify ability to handle dynamic forms where input fields change position after each reload/submit.
- **Method**: executed `library/rpa_challenge.yaml` using `roadbook-stepper` (manual agent-driven execution via `agent-browser`).

## Key Observations
1.  **Dynamic ID Stability**: The `agent-browser` relies on generated IDs (e.g., `@e12`) that are session-specific and DOM-state specific. They cannot be hardcoded in the roadbook. The roadbook **must** describe *how* to find the element (Landmarks), not *where* it is (IDs/Selectors).
2.  **Snapshot Analysis**: The `snapshot` provided by `agent-browser` is critical. It transforms the DOM into a readable list of semantic elements (e.g., `text: "First Name"`, `textbox [ref=e4]`).
    - **Strategy**: The best strategy for the Agent is to look for the *Label* text in the snapshot, then identify the *immediately following* interactable element (usually an input/textbox).
3.  **Efficiency**:
    - **Batching**: Grouping multiple `type` commands into a single execution block (e.g., `type e4 "John"; type e8 "Doe"`) significantly reduces latency compared to step-by-step interactive execution.
    - **Pre-Validation**: Validating the "Start" state (ensuring we occupy the correct page context) before attempting bulk entry prevents cascading errors.

## Roadbook Improvements (v1.1)
Based on this run, `library/rpa_challenge.yaml` was updated to version 1.1:
- **Added `label` field to Landmarks**: Explicitly stating the label text helps the Agent (and future programmatic runners) know exactly what text to search for in the DOM snapshot.
- **Clarified Descriptions**: Added descriptions to ambiguous buttons (like "Start") to distinguish them from other potential buttons.
- **Standardized Landmarks**: Ensured all form fields have consistent landmark attributes (`role`, `keyword`, `label`, `xpath`).

## Next Steps
- Implement an automated `Roadbook Runner` script that can programmatically parse these landmarks and map them to `agent-browser` IDs without human/LLM intervention for every step.
- Test the roadbook against multi-round execution (looping the "Fill Form" stage).
