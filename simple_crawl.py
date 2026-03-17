"""
Simple crawl script for testing
"""
from playwright.sync_api import sync_playwright
import time

print("开始执行简单爬取脚本...")
try:
    with sync_playwright() as p:
        print("正在连接到浏览器...")
        # Connect to existing browser via CDP on port 9224
        browser = p.chromium.connect_over_cdp("http://localhost:9224")
        print("连接成功！")
        
        context = browser.contexts[0]
        page = context.pages[0]
        print(f"当前页面: {page.title()}")
        
        # Wait and scroll
        time.sleep(2)
        page.mouse.wheel(0, 1000)
        time.sleep(2)
        
        # Try to find videos
        print("正在查找视频...")
        cards = page.query_selector_all("div")
        print(f"找到 {len(cards)} 个 div 元素")
        
        # Get first 5 divs with content
        videos = []
        for i, card in enumerate(cards[:20], 1):
            text = card.text_content().strip()
            if text and len(text) > 20:
                videos.append({"id": i, "title": text[:100]})
                if len(videos) >= 5:
                    break
        
        print("\n找到的视频:")
        for video in videos:
            print(f"视频 {video['id']}: {video['title']}")
        
        browser.close()
        print("浏览器已关闭")
except Exception as e:
    print(f"错误: {str(e)}")
print("脚本执行完成！")
