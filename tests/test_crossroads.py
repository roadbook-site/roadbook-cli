import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from roadbook.sdk.context import RoadbookContext, AgentBreakpointInterrupt

@pytest.fixture
def temp_rb_dir(tmp_path):
    """Provides a temporary directory structure mimicking a roadbook project."""
    root = tmp_path / "my_project"
    rb_dir = root / ".rb"
    run_dir = root / "runtime" / "test_run"
    outputs_dir = root / "outputs" / "test_run"
    
    rb_dir.mkdir(parents=True)
    run_dir.mkdir(parents=True)
    outputs_dir.mkdir(parents=True)
    
    return {
        "root": str(root),
        "rb_dir": rb_dir,
        "run_dir": str(run_dir),
        "outputs_dir": str(outputs_dir)
    }

def test_crossroads_interrupt(temp_rb_dir):
    """Test that calling crossroads raises AgentBreakpointInterrupt and saves state."""
    
    # 1. Initialize context
    ctx = RoadbookContext(
        root_dir=temp_rb_dir["root"],
        run_dir=temp_rb_dir["run_dir"],
        outputs_dir=temp_rb_dir["outputs_dir"]
    )
    
    # Mock page and state
    ctx.page = MagicMock()
    ctx.page.url = "https://example.com/step1"
    ctx.current_sheet = "Sheet_A"
    ctx.state = {"user_id": 123, "items": ["A", "B"]}
    
    # 2. Trigger crossroads
    with pytest.raises(AgentBreakpointInterrupt) as exc_info:
        ctx.crossroads("Which item to click?", options=["A", "B"])
        
    assert "Execution paused at Crossroads" in str(exc_info.value)
    
    # 3. Verify the saved JSON file
    crossroads_file = Path(temp_rb_dir["rb_dir"]) / "crossroads.json"
    assert crossroads_file.exists()
    
    with open(crossroads_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert data["status"] == "waiting_for_agent"
    assert data["sheet_id"] == "Sheet_A"
    assert data["url"] == "https://example.com/step1"
    assert data["question"] == "Which item to click?"
    assert data["options"] == ["A", "B"]
    assert data["state"] == {"user_id": 123, "items": ["A", "B"]}

def test_crossroads_resume_fast_forward(temp_rb_dir):
    """Test that context correctly fast-forwards and returns the agent's reply."""
    
    crossroads_file = Path(temp_rb_dir["rb_dir"]) / "crossroads.json"
    
    # 1. Simulate an Agent having provided a reply
    mock_data = {
        "status": "waiting_for_agent",
        "sheet_id": "Sheet_B",
        "url": "https://example.com/step2",
        "state": {"restored": True},
        "reply": "Option B"
    }
    with open(crossroads_file, "w", encoding="utf-8") as f:
        json.dump(mock_data, f)
        
    # 2. Initialize context (it should load the state in __init__)
    ctx = RoadbookContext(
        root_dir=temp_rb_dir["root"],
        run_dir=temp_rb_dir["run_dir"],
        outputs_dir=temp_rb_dir["outputs_dir"]
    )
    
    # Verify state was loaded
    assert ctx.resume_target_sheet == "Sheet_B"
    assert ctx.state == {"restored": True}
    
    # 3. Test fast-forwarding logic (should_run)
    assert ctx.should_run("Sheet_A") is False  # Skip previous sheet
    assert ctx.should_run("Sheet_B") is True   # Target sheet reached
    assert ctx.resume_target_sheet is None     # Cleared
    assert ctx.should_run("Sheet_C") is True   # Subsequent sheets run normally
    
    # 4. Test retrieving the reply
    ctx.page = MagicMock()
    ctx.page.url = "https://example.com/different" # Simulate starting on a different page
    ctx.current_sheet = "Sheet_B"
    
    reply = ctx.crossroads("Any question?")
    
    # Verify it navigated back to the saved URL
    ctx.page.goto.assert_called_with("https://example.com/step2")
    # Verify it returned the reply
    assert reply == "Option B"
    # Verify the crossroads file was cleaned up
    assert not crossroads_file.exists()

def test_sheet_context_manager_fast_forward():
    """Test that the sheet context manager yields False when skipping."""
    ctx = RoadbookContext()
    ctx.resume_target_sheet = "Target_Sheet"
    
    # Test skipping
    with ctx.sheet("Skip_Me") as active:
        assert active is False
        assert ctx.current_sheet == "Skip_Me"
        
    # Test reaching target
    with ctx.sheet("Target_Sheet") as active:
        assert active is True
        assert ctx.current_sheet == "Target_Sheet"
        
    # Test subsequent
    with ctx.sheet("Run_Me") as active:
        assert active is True
        assert ctx.current_sheet == "Run_Me"