import sys
import os
from pathlib import Path
import json

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.append(str(src_path))

from roadbook.server.parser import RoadbookParser

def test_parser():
    parser = RoadbookParser()
    sample_path = Path(__file__).parent / "sample_roadbook.md"
    
    with open(sample_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    print("--- Parsing ---")
    model = parser.parse(content)
    
    print(f"Meta: {model.meta}")
    print(f"Sheets count: {len(model.sheets)}")
    
    for i, sheet in enumerate(model.sheets):
        print(f"\nSheet {i+1}: {sheet.title}")
        print(f"  ID: {sheet.id}")
        print(f"  Steps: {len(sheet.steps)}")
        if sheet.steps:
            print(f"  First Step: {sheet.steps[0].original_text}")
        if sheet.extra_content:
            print(f"  Extra Content: {len(sheet.extra_content)} chars")
            
    print("\n--- Dumping ---")
    dumped = parser.dump(model)
    print(dumped[:500] + "...") # Print first 500 chars
    
    # Verify idempotency (mostly)
    print("\n--- Re-Parsing Dumped Content ---")
    model2 = parser.parse(dumped)
    print(f"Sheets count: {len(model2.sheets)}")
    assert len(model.sheets) == len(model2.sheets)
    assert model.meta == model2.meta

if __name__ == "__main__":
    test_parser()
