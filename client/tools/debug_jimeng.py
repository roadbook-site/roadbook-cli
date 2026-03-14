import time
import re
from playwright.sync_api import sync_playwright

CDP_URL = "http://localhost:9224"

def debug_selectors():
    print("Connecting...")
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()
        
        # 1. Standard Video Mode
        url = "https://jimeng.jianying.com/ai-tool/generate/?type=video"
        print(f"Navigating to {url}...")
        if "type=video" not in page.url:
            page.goto(url)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(3) # Wait for hydration
        
        print("Page loaded. Dumping potential ratio buttons...")
        
        # Try to find any element with text matching ratio pattern
        # Common ratios: 16:9, 9:16, 1:1, 4:3, 3:4
        ratios = ["16:9", "9:16", "1:1", "4:3", "3:4"]
        found = False
        for r in ratios:
            elements = page.locator(f"text={r}").all()
            if elements:
                print(f"Found text '{r}' in {len(elements)} elements.")
                for i, el in enumerate(elements):
                    try:
                        # Check if visible
                        if el.is_visible():
                            print(f"  [{i}] Visible. Tag: {el.evaluate('el => el.tagName')}")
                            print(f"      OuterHTML: {el.evaluate('el => el.outerHTML')}")
                            # Check parent
                            parent = el.locator("..")
                            print(f"      Parent HTML: {parent.evaluate('el => el.outerHTML')}")
                            found = True
                    except:
                        pass
        
        if not found:
            print("No ratio text found visible on page.")
            # Dump all buttons to see what's there
            buttons = page.locator("button").all()
            print(f"Total buttons: {len(buttons)}")
            for i, b in enumerate(buttons[:10]): # Print first 10
                try:
                    if b.is_visible():
                        print(f"Button {i}: {b.inner_text()} | Class: {b.get_attribute('class')}")
                except:
                    pass

        browser.close()

if __name__ == "__main__":
    debug_selectors()
