import sys
import re
from playwright.sync_api import sync_playwright

CDP_URL = "http://localhost:9224"

def run_verification():
    print("Connecting to browser via CDP...")
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
            url = "https://jimeng.jianying.com/ai-tool/generate/?type=video"
            print(f"Navigating to: {url}")
            page.goto(url)
            
            print("Waiting for prompt input area...")
            page.wait_for_selector("textarea[placeholder*='输入文字']", timeout=30000)
            print("Page loaded successfully.")

            # --- Sheet 2: Configuration ---
            print("\n[Sheet 2: Configuration]")
            
            # 2.1 Ratio (16:9)
            # Using the new robust strategy from scrape_jimeng.py
            # Look for button containing span with "16:9"
            # Or just find the span and click its parent
            ratio_target = "16:9"
            ratio_regex = re.compile(r"^\d+:\d+$")
            
            print(f"Setting Ratio to {ratio_target}...")
            try:
                # Check if already set
                current_ratio_el = page.locator("span").filter(has_text=ratio_target).first
                if current_ratio_el.is_visible():
                    print(f"Ratio {ratio_target} is already visible/selected.")
                else:
                    # Open menu via any visible ratio button
                    ratio_trigger = page.locator("span").filter(has_text=ratio_regex).first
                    if ratio_trigger.count() > 0:
                        print(f"Opening ratio menu via: {ratio_trigger.inner_text()}")
                        ratio_trigger.locator("..").click()
                        page.wait_for_timeout(1000)
                        
                        # Select target ratio
                        target_option = page.locator("div[role='radio']").filter(has_text=ratio_target).first
                        if target_option.is_visible():
                            print(f"Selecting ratio: {ratio_target}")
                            target_option.click()
                        else:
                            print(f"Target ratio {ratio_target} not found in menu.")
                    else:
                        print("No ratio trigger found.")
            except Exception as e:
                print(f"Error setting ratio: {e}")

            # 2.2 Duration (5s)
            duration_target = "5s"
            duration_regex = re.compile(r"^\d+s$")
            
            print(f"Setting Duration to {duration_target}...")
            try:
                current_dur_el = page.locator("span").filter(has_text=duration_target).first
                if current_dur_el.is_visible():
                    print(f"Duration {duration_target} is already visible/selected.")
                else:
                    # Open menu
                    dur_trigger = page.locator("span").filter(has_text=duration_regex).first
                    if dur_trigger.count() > 0:
                        print(f"Opening duration menu via: {dur_trigger.inner_text()}")
                        dur_trigger.locator("..").click()
                        page.wait_for_timeout(1000)
                        
                        target_option = page.locator("div[role='option']").filter(has_text=duration_target).first
                        if target_option.is_visible():
                            print(f"Selecting duration: {duration_target}")
                            target_option.click()
                        else:
                            print(f"Target duration {duration_target} not found in menu.")
                    else:
                        print("No duration trigger found.")
            except Exception as e:
                print(f"Error setting duration: {e}")

            # --- Sheet 3: Input ---
            print("\n[Sheet 3: Input]")
            prompt_selector = "textarea[placeholder*='输入文字']"
            prompt_text = "A futuristic city at sunset, 4k resolution, cinematic lighting"
            print(f"Filling prompt: '{prompt_text}'")
            page.fill(prompt_selector, prompt_text)
            
            # --- Sheet 4: Generation ---
            print("\n[Sheet 4: Generation]")
            # Try multiple selectors for generate button
            generate_locators = [
                page.locator("button").filter(has_text="生成"),
                page.locator("button[class*='submit']"),
                page.locator("div[role='button']").filter(has_text="生成")
            ]
            
            gen_btn = None
            for loc in generate_locators:
                if loc.count() > 0:
                    gen_btn = loc.last
                    print(f"Found generate button: {loc}")
                    break
            
            if gen_btn:
                # Check if button is enabled
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
                # Debug HTML
                # print(page.content()) 
            
            print("\nVerification completed.")
            browser.close()

    except Exception as e:
        print(f"Critical Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_verification()
