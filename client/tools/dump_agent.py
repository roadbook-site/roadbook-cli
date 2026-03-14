import time
from playwright.sync_api import sync_playwright

CDP_URL = "http://localhost:9224"

def dump_agent_mode():
    print("Connecting...")
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()
        
        # 2. Agent Mode
        url = "https://jimeng.jianying.com/ai-tool/generate/?type=agentic&workspace=0"
        print(f"Navigating to {url}...")
        page.goto(url)
        page.wait_for_load_state("domcontentloaded")
        time.sleep(3)
        
        print(f"Current URL: {page.url}")
        
        # Get all text
        text = page.inner_text("body")
        print("\n--- Agent Page Text ---")
        print(text[:2000])
        print("\n-----------------")
        
        # Check for Input
        inputs = page.locator("textarea").count()
        print(f"Found {inputs} textareas.")
        
        # Check for Buttons
        buttons = page.locator("button").all()
        print(f"Found {len(buttons)} buttons.")
        for i, b in enumerate(buttons[:10]):
             if b.is_visible():
                print(f"Button {i}: {b.inner_text()}")

        browser.close()

if __name__ == "__main__":
    dump_agent_mode()
