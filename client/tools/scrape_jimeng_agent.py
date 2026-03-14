import sys
import os
import time
from playwright.sync_api import sync_playwright

CDP_URL = "http://localhost:9224"
ASSETS_DIR = r"c:\code_dev\roadbook\library\assets\jimeng"

def run_scrape_agent():
    print("Connecting to browser via CDP...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(CDP_URL)
            context = browser.contexts[0]
            if not context.pages:
                page = context.new_page()
            else:
                page = context.pages[0]
            
            # Navigate to Agent Mode
            url = "https://jimeng.jianying.com/ai-tool/generate/?type=agentic&workspace=0"
            print(f"Navigating to: {url}")
            page.goto(url)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(3)
            
            # Sheet 1: Init
            screenshot_path = os.path.join(ASSETS_DIR, "agent_init.png")
            page.screenshot(path=screenshot_path)
            print(f"Saved screenshot: {screenshot_path}")

            # Sheet 2: Input (ContentEditable)
            print("\n[Sheet 2: Input]")
            # Find the contenteditable div
            # It might be inside a specific container.
            # Usually agent chat inputs are at the bottom.
            # Let's try to find it by attribute
            input_el = page.locator("[contenteditable]").last
            if input_el.count() > 0:
                print("Found input area.")
                input_el.scroll_into_view_if_needed()
                input_el.evaluate("el => el.style.border = '2px solid red'")
                time.sleep(0.5)
                
                screenshot_path = os.path.join(ASSETS_DIR, "agent_input.png")
                page.screenshot(path=screenshot_path)
                print(f"Saved screenshot: {screenshot_path}")
                
                input_el.evaluate("el => el.style.border = ''")
            else:
                print("Input area not found.")

            # Sheet 3: Generate (Send Button)
            print("\n[Sheet 3: Generate]")
            # Usually an arrow icon or "Send" button
            # Based on previous dump, there was a primary button that was disabled.
            # "Button 5: | Class: ... submit-button-..."
            submit_btn = page.locator("button[class*='submit-button']").last
            if submit_btn.count() > 0:
                print("Found submit button.")
                submit_btn.evaluate("el => el.style.border = '2px solid red'")
                time.sleep(0.5)
                
                screenshot_path = os.path.join(ASSETS_DIR, "agent_generate.png")
                page.screenshot(path=screenshot_path)
                print(f"Saved screenshot: {screenshot_path}")
                
                submit_btn.evaluate("el => el.style.border = ''")
            else:
                print("Submit button not found.")

            browser.close()

    except Exception as e:
        print(f"Critical Error: {e}")

if __name__ == "__main__":
    run_scrape_agent()
