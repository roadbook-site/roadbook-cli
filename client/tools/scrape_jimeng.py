import sys
import re
import os
import time
from playwright.sync_api import sync_playwright

CDP_URL = "http://localhost:9224"
ASSETS_DIR = r"c:\code_dev\roadbook\library\assets\jimeng"

def run_scrape():
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
            if page.url != url:
                print(f"Navigating to: {url}")
                page.goto(url)
                page.wait_for_selector("textarea[placeholder*='输入文字']", timeout=30000)
            
            # Screenshot 1: Full Page
            time.sleep(1) # wait for render
            screenshot_path = os.path.join(ASSETS_DIR, "sheet_init.png")
            page.screenshot(path=screenshot_path)
            print(f"Saved screenshot: {screenshot_path}")

            # --- Sheet 2: Configuration - Ratio ---
            print("\n[Sheet 2: Configuration - Ratio]")
            
            # Use text-based locator for Ratio button (e.g. "16:9", "9:16")
            # We look for a button or clickable element containing the ratio text
            ratio_regex = re.compile(r"^\d+:\d+$")
            # Find the span with text, then go up to button or clickable container
            ratio_el = page.locator("span").filter(has_text=ratio_regex).first
            
            available_ratios = []
            if ratio_el.count() > 0:
                print(f"Found ratio text: {ratio_el.inner_text()}")
                # Click parent or the element itself if clickable
                # Usually it's inside a button
                ratio_btn = ratio_el.locator("..") # Parent
                print(f"Clicking ratio button parent: {ratio_btn}")
                ratio_btn.click()
                time.sleep(1.0)
                
                # Scrape options
                # They might be in a popover/tooltip
                # Look for all ratio texts again
                # But filter only visible ones in the dropdown
                options = page.locator("div[role='radio']") # Try role again
                if options.count() == 0:
                    # Fallback: look for text
                    options = page.locator("span").filter(has_text=ratio_regex)
                
                count = options.count()
                print(f"Found {count} ratio options (potential).")
                
                for i in range(count):
                    if options.nth(i).is_visible():
                        opt_text = options.nth(i).inner_text()
                        if re.match(r"^\d+:\d+$", opt_text) and opt_text not in available_ratios:
                            available_ratios.append(opt_text)
                            print(f"  - Ratio Option: {opt_text}")
                
                # Screenshot Ratio Menu
                screenshot_path = os.path.join(ASSETS_DIR, "sheet_config_ratio.png")
                page.screenshot(path=screenshot_path)
                print(f"Saved screenshot: {screenshot_path}")
                
                # Close menu
                page.keyboard.press("Escape")
                time.sleep(0.5)
            else:
                print("Ratio text not found.")

            # --- Sheet 2: Configuration - Duration ---
            print("\n[Sheet 2: Configuration - Duration]")
            
            # Look for "5s" or "10s"
            duration_regex = re.compile(r"^\d+s$")
            duration_el = page.locator("span").filter(has_text=duration_regex).first
            
            available_durations = []
            if duration_el.count() > 0:
                print(f"Found duration text: {duration_el.inner_text()}")
                duration_btn = duration_el.locator("..")
                print(f"Clicking duration button: {duration_btn}")
                duration_btn.click()
                time.sleep(1.0)
                
                # Scrape options
                options = page.locator("div[role='option']")
                if options.count() == 0:
                    options = page.locator("span").filter(has_text=duration_regex)

                count = options.count()
                print(f"Found {count} duration options.")
                
                for i in range(count):
                    if options.nth(i).is_visible():
                        opt_text = options.nth(i).inner_text()
                        if re.match(r"^\d+s$", opt_text) and opt_text not in available_durations:
                            available_durations.append(opt_text)
                            print(f"  - Duration Option: {opt_text}")
                
                # Screenshot Duration Menu
                screenshot_path = os.path.join(ASSETS_DIR, "sheet_config_duration.png")
                page.screenshot(path=screenshot_path)
                print(f"Saved screenshot: {screenshot_path}")
                
                page.keyboard.press("Escape")
                time.sleep(0.5)
            else:
                print("Duration text not found.")

            # --- Sheet 3: Input ---
            print("\n[Sheet 3: Input]")
            prompt_area = page.locator("textarea[placeholder*='输入文字']")
            if prompt_area.count() > 0:
                prompt_area.scroll_into_view_if_needed()
                # Highlight it for screenshot
                prompt_area.evaluate("el => el.style.border = '2px solid red'")
                time.sleep(0.5)
                
                screenshot_path = os.path.join(ASSETS_DIR, "sheet_input.png")
                page.screenshot(path=screenshot_path)
                print(f"Saved screenshot: {screenshot_path}")
                
                # Reset style
                prompt_area.evaluate("el => el.style.border = ''")

            # --- Sheet 4: Generation ---
            print("\n[Sheet 4: Generation]")
            gen_btn = page.locator("button[class*='submit']").last
            if gen_btn.count() > 0:
                gen_btn.scroll_into_view_if_needed()
                gen_btn.evaluate("el => el.style.border = '2px solid red'")
                time.sleep(0.5)
                
                screenshot_path = os.path.join(ASSETS_DIR, "sheet_generate.png")
                page.screenshot(path=screenshot_path)
                print(f"Saved screenshot: {screenshot_path}")
                
                gen_btn.evaluate("el => el.style.border = ''")

            print("\n--- Summary ---")
            print(f"Ratios: {available_ratios}")
            print(f"Durations: {available_durations}")
            
            # Save metadata to file for reference if needed
            with open(os.path.join(ASSETS_DIR, "options.txt"), "w", encoding="utf-8") as f:
                f.write(f"Ratios: {', '.join(available_ratios)}\n")
                f.write(f"Durations: {', '.join(available_durations)}\n")

            browser.close()

    except Exception as e:
        print(f"Critical Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_scrape()
