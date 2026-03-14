import time
import os
from playwright.sync_api import sync_playwright

CDP_URL = "http://localhost:9224"
ASSETS_DIR = r"c:\code_dev\roadbook\library\assets\jimeng"

def diagnose():
    print("Connecting...")
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()
        
        # Ensure dir
        if not os.path.exists(ASSETS_DIR):
            os.makedirs(ASSETS_DIR)

        # 1. Video Mode Diagnosis
        url = "https://jimeng.jianying.com/ai-tool/generate/?type=video"
        if "type=video" not in page.url:
            page.goto(url)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(3)
        
        print(f"Current URL: {page.url}")
        
        # Frames
        print(f"Total Frames: {len(page.frames)}")
        for i, frame in enumerate(page.frames):
            print(f"  Frame {i}: {frame.name} | {frame.url}")
            try:
                tas = frame.locator("textarea").count()
                inputs = frame.locator("input").count()
                ce = frame.locator("[contenteditable]").count()
                print(f"    - Textareas: {tas}")
                print(f"    - Inputs: {inputs}")
                print(f"    - ContentEditables: {ce}")
            except:
                print("    - Error accessing frame")

        # Screenshot
        ss_path = os.path.join(ASSETS_DIR, "diag_video.png")
        page.screenshot(path=ss_path)
        print(f"Saved screenshot: {ss_path}")

        # 2. Agent Mode Diagnosis
        url_agent = "https://jimeng.jianying.com/ai-tool/generate/?type=agentic&workspace=0"
        page.goto(url_agent)
        page.wait_for_load_state("domcontentloaded")
        time.sleep(3)
        
        print(f"\nAgent URL: {page.url}")
        ss_path = os.path.join(ASSETS_DIR, "diag_agent.png")
        page.screenshot(path=ss_path)
        print(f"Saved screenshot: {ss_path}")
        
        # Check inputs again for Agent mode
        tas = page.locator("textarea").count()
        print(f"Agent Mode Textareas: {tas}")

        browser.close()

if __name__ == "__main__":
    diagnose()
