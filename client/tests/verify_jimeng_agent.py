import sys
import re
from playwright.sync_api import sync_playwright

CDP_URL = "http://localhost:9224"

def run_verification():
    print("Connecting to browser via CDP for Agent Mode Verification...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(CDP_URL)
            context = browser.contexts[0]
            if not context.pages:
                page = context.new_page()
            else:
                page = context.pages[0]
            
            print(f"Connected to page: {page.title()}")
            
            # --- Sheet 1: Initialization ---
            print("\n[Sheet 1: Initialization]")
            url = "https://jimeng.jianying.com/ai-tool/generate/?type=agentic&workspace=0"
            print(f"Navigating to: {url}")
            page.goto(url)
            page.wait_for_load_state("domcontentloaded")
            
            print("Waiting for input area...")
            page.wait_for_selector("[contenteditable]", timeout=30000)
            print("Page loaded successfully.")

            # --- Sheet 2: Input ---
            print("\n[Sheet 2: Input]")
            prompt_selector = "[contenteditable]"
            prompt_text = "Create a video of a futuristic city with 16:9 ratio and 5s duration"
            print(f"Filling prompt: '{prompt_text}'")
            page.click(prompt_selector)
            page.fill(prompt_selector, prompt_text)
            
            # --- Sheet 3: Generation ---
            print("\n[Sheet 3: Generation]")
            generate_locator = page.locator("button[class*='submit']")
            
            if generate_locator.count() > 0:
                gen_btn = generate_locator.last
                print("Found generate button.")
                
                if gen_btn.is_disabled():
                    print("Generate button is disabled.")
                else:
                    print("Clicking Generate button...")
                    gen_btn.click()
                    
                    print("Waiting for task status update...")
                    try:
                        # Wait for "排队" or "生成中"
                        status_locator = page.locator("body").filter(has_text=re.compile(r"排队|生成中"))
                        status_locator.first.wait_for(timeout=10000)
                        print("Task successfully submitted and is running/queuing.")
                    except:
                        print("Warning: Did not detect 'Queuing' or 'Generating' status within timeout.")
            else:
                print("Generate button NOT found.")
            
            print("\nVerification completed.")
            browser.close()

    except Exception as e:
        print(f"Critical Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_verification()
