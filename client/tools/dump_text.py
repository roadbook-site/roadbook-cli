import time
from playwright.sync_api import sync_playwright

CDP_URL = "http://localhost:9224"

def dump_text():
    print("Connecting...")
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()
        
        # 1. Standard Video Mode
        url = "https://jimeng.jianying.com/ai-tool/generate/?type=video"
        if "type=video" not in page.url:
            page.goto(url)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(3)
        
        print(f"Current URL: {page.url}")
        
        # Get all text
        text = page.inner_text("body")
        print("\n--- Page Text ---")
        print(text[:2000]) # Print first 2000 chars
        print("\n-----------------")

        browser.close()

if __name__ == "__main__":
    dump_text()
