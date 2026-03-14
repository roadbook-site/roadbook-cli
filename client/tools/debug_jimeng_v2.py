import time
from playwright.sync_api import sync_playwright

CDP_URL = "http://localhost:9224"

def thorough_debug():
    print("Connecting...")
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()
        
        # 1. Video Mode Analysis
        url = "https://jimeng.jianying.com/ai-tool/generate/?type=video"
        if "type=video" not in page.url:
            page.goto(url)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(3)
        
        print(f"\n[Video Mode Analysis] URL: {page.url}")
        
        # Find Textarea
        ta = page.locator("textarea").first
        if ta.count() > 0:
            print(f"Found Textarea. Placeholder: {ta.get_attribute('placeholder')}")
            # Check surrounding elements for controls
            # Often controls are near the input or above it
            
            # Check for Ratio via text again, but maybe inside specific containers
            # Try to find ANY text matching ratio pattern visible on screen
            visible_text = page.inner_text("body")
            if "16:9" in visible_text:
                print("Text '16:9' is visible on page!")
                # Find where
                el = page.get_by_text("16:9").first
                if el.is_visible():
                     print(f"Found 16:9 element: {el.evaluate('el => el.outerHTML')}")
            else:
                print("Text '16:9' NOT found in visible text.")
                
            # Check for Duration '5s'
            if "5s" in visible_text:
                print("Text '5s' is visible on page!")
        else:
            print("Textarea not found (unexpected, diagnosis said 1 exists).")

        # 2. Agent Mode Analysis
        url_agent = "https://jimeng.jianying.com/ai-tool/generate/?type=agentic&workspace=0"
        page.goto(url_agent)
        page.wait_for_load_state("domcontentloaded")
        time.sleep(3)
        
        print(f"\n[Agent Mode Analysis] URL: {page.url}")
        
        # Check inputs
        inputs = page.locator("input").all()
        print(f"Found {len(inputs)} inputs.")
        for i, inp in enumerate(inputs):
            if inp.is_visible():
                print(f"  Input {i}: type={inp.get_attribute('type')}, placeholder={inp.get_attribute('placeholder')}")
        
        # Check contenteditable again just in case
        ce = page.locator("[contenteditable]").all()
        print(f"Found {len(ce)} contenteditables.")
        
        browser.close()

if __name__ == "__main__":
    thorough_debug()
