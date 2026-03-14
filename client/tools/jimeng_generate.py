import asyncio
import re
import time
from playwright.async_api import async_playwright, Playwright, expect

# 配置
CDP_URL = "http://localhost:9224"
TARGET_URL = "https://jimeng.jianying.com/ai-tool/generate/?type=video"
PROMPT = "一个赛博朋克风格的未来城市，霓虹灯闪烁，飞行汽车穿梭，4k分辨率，高细节"
OUTPUT_DIR = "C:\\code_dev\\roadbook\\library"

async def run(playwright: Playwright):
    print(f"Connecting to CDP at {CDP_URL}...")
    try:
        browser = await playwright.chromium.connect_over_cdp(CDP_URL)
    except Exception as e:
        print(f"Failed to connect to CDP: {e}")
        print("Please ensure Chrome is running with --remote-debugging-port=9224")
        return

    context = browser.contexts[0]
    page = context.pages[0]

    print(f"Navigating to {TARGET_URL}...")
    try:
        await page.goto(TARGET_URL, timeout=30000)
    except Exception as e:
        print(f"Navigation error or timeout: {e}")
        # Continue anyway if we are on the right page
    
    print("Waiting for page load...")
    # Use domcontentloaded instead of networkidle which might hang on SPAs
    await page.wait_for_load_state("domcontentloaded")
    print("Page loaded (domcontentloaded).")

    # CP1: Arrival
    print("CP1: Checking arrival...")
    await expect(page).to_have_url(re.compile(r".*/ai-tool/generate.*type=video"))
    print("Arrival confirmed.")

    # L2: Prompt Input
    print("L2: Inputting prompt...")
    # Try multiple selectors for robustness
    prompt_box = page.locator("textarea[placeholder*='输入文字，描述你想创作的画面内容']")
    if not await prompt_box.count():
        prompt_box = page.get_by_role("textbox").first
    
    await prompt_box.fill(PROMPT)
    print(f"Prompt filled: {PROMPT[:20]}...")

    # L3: Aspect Ratio (16:9)
    print("L3: Setting aspect ratio to 16:9...")
    # Check current ratio text
    ratio_btn = page.locator("button", has_text=re.compile(r"\d+:\d+")).first
    current_ratio = await ratio_btn.text_content()
    
    if "16:9" not in current_ratio:
        await ratio_btn.click()
        # Wait for tooltip/popover
        option_16_9 = page.locator("div[role='radio']:has-text('16:9')")
        await option_16_9.click()
        print("Ratio set to 16:9")
    else:
        print("Ratio is already 16:9")

    # L4: Duration (5s)
    print("L4: Setting duration to 5s...")
    duration_box = page.locator("div[role='combobox']:has-text('s')").last
    current_duration = await duration_box.text_content()
    
    if "5s" not in current_duration:
        await duration_box.click()
        option_5s = page.locator("div[role='option']:has-text('5s')")
        await option_5s.click()
        print("Duration set to 5s")
    else:
        print("Duration is already 5s")

    # CP2: Ready to Generate or Already Generating
    print("CP2: Checking status...")
    
    # Check if already generating/queueing
    queue_indicators = [
        "排队中",
        "生成中",
        "取消生成"
    ]
    
    is_generating = False
    for indicator in queue_indicators:
        if await page.get_by_text(indicator).count() > 0:
            print(f"Detected existing task status: {indicator}")
            is_generating = True
            break
            
    if is_generating:
        print("Task is already in progress. Skipping generation step.")
    else:
        # Try multiple strategies to find the Generate button
        generate_btn = page.locator("button:has-text('生成')").last
        
        if not await generate_btn.count():
             print("Standard '生成' button not found. Trying alternative selectors...")
             
             # Scroll to bottom first
             await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
             
             # Strategy 2: Button after the duration combobox
             # Construct a single XPath locator for robustness
             # We look for the last combobox containing 's' (likely duration) and find the button immediately following it
             generate_btn = page.locator("(//div[@role='combobox'][contains(., 's')])[last()]/following::button[1]")
             
             if not await generate_btn.count() or not await generate_btn.is_visible():
                 # Strategy 3: Button before "回到底部"
                 print("Strategy 2 failed. Trying Strategy 3 (before '回到底部')...")
                 back_to_bottom = page.locator("button:has-text('回到底部')")
                 if await back_to_bottom.count():
                     generate_btn = page.locator("//button[contains(text(), '回到底部')]/preceding::button[1]")
     
        # Debug: Print all buttons
        print("DEBUG: Listing all visible buttons:")
        buttons = page.locator("button")
        count = await buttons.count()
        for i in range(count):
            btn = buttons.nth(i)
            if await btn.is_visible():
                txt = await btn.text_content()
                print(f"Button {i}: '{txt.strip()}' enabled={await btn.is_enabled()}")
     
        # Wait for it to be enabled
        try:
            await generate_btn.scroll_into_view_if_needed()
            await expect(generate_btn).to_be_enabled(timeout=5000)
            print("Ready to generate.")
            
            # L5: Generate
            print("L5: Clicking Generate...")
            await generate_btn.click()
            
        except AssertionError:
            # Check one last time if we missed the generating status
            found_indicator = False
            for indicator in queue_indicators:
                if await page.get_by_text(indicator).count() > 0:
                    print(f"Button disabled but task seems to be running: {indicator}")
                    found_indicator = True
                    break
            
            if not found_indicator:
                print("Button still disabled or not found. Debugging info:")
                # Print some page content or state
                print(f"Button visible: {await generate_btn.is_visible()}")
                print(f"Button enabled: {await generate_btn.is_enabled()}")
                # Don't raise, just warn
                print("WARNING: Could not click generate button. It might be disabled due to rate limits or invalid inputs.")
                return

    # CP3: Task Submission
    print("CP3: Waiting for task submission confirmation...")
    
    # Check for queue status again
    try:
        # Wait for "排队中" or "生成中" or similar text to appear
        # We use a broad regex to catch status updates
        await expect(page.locator("body")).to_contain_text(re.compile(r"排队|生成中|取消生成"), timeout=10000)
        print("Task confirmed: Queueing or Generating.")
    except:
        print("Warning: Did not see immediate confirmation text. Check browser manually.")
    
    print("Note: Video generation may take a long time (hours for free tier).")
    print("Script will not wait for completion.")
    print("Script finished. Please check the browser for progress.")

    # We don't close the browser because it's a CDP session
    await browser.close()

async def main():
    async with async_playwright() as playwright:
        await run(playwright)

if __name__ == "__main__":
    asyncio.run(main())
