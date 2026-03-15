# Modified script
import sys
import json
import os
import time
from pathlib import Path
from contextlib import contextmanager

# Runtime artifacts (downloads, screenshots) should be saved to a timestamped output directory
RUNTIME_DIR = Path(__file__).parent.parent / "runtime"
# Try to get session ID from environment (passed by CLI)
SESSION_ID = os.environ.get("ROADBOOK_RUN_ID")
if SESSION_ID:
    OUTPUT_DIR = RUNTIME_DIR / "runs" / SESSION_ID / "artifacts"
else:
    # Fallback for manual runs
    OUTPUT_DIR = RUNTIME_DIR.parent / f"output_{time.strftime('%Y_%m_%d_%H_%M')}"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Step Profiling Helper
STEPS_TIMING = {}

@contextmanager
def step(name):
    print(f"[*] Step Started: {name}...")
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        STEPS_TIMING[name] = duration
        print(f"    -> Step Finished: {name} (Duration: {duration:.2f}s)")

def run(inputs):
    print(f"Running with inputs: {inputs}")
    print(f"Artifacts will be saved to: {OUTPUT_DIR}")
    
    # Initialize structured outputs
    outputs = {}

    with step("Initialization"):
        time.sleep(0.1)
    
    with step("Processing"):
        time.sleep(0.2)
        outputs["status"] = "processed"

    # Save structured outputs to outputs.json
    outputs_file = OUTPUT_DIR / "outputs.json"
    
    # Attach timing metrics to outputs (optional, but helpful)
    outputs["_steps_timing"] = STEPS_TIMING
    
    with open(outputs_file, "w", encoding="utf-8") as f:
        json.dump(outputs, f, indent=2, ensure_ascii=False)
    print(f"Structured outputs saved to: {outputs_file}")

if __name__ == "__main__":
    inputs = {}
    if len(sys.argv) > 1:
        try:
            inputs = json.loads(sys.argv[1])
        except:
            pass
    run(inputs)
