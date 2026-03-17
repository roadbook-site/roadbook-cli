"""
Test script to check Playwright connection
"""
from playwright.sync_api import sync_playwright

print("开始测试 Playwright 连接...")
try:
    with sync_playwright() as p:
        print("Playwright 初始化成功")
        print("尝试连接到浏览器...")
        # 尝试连接到浏览器
        browser = p.chromium.connect_over_cdp("http://localhost:9224")
        print("浏览器连接成功！")
        print(f"浏览器上下文数量: {len(browser.contexts)}")
        if browser.contexts:
            context = browser.contexts[0]
            print(f"页面数量: {len(context.pages)}")
            if context.pages:
                page = context.pages[0]
                print(f"当前页面标题: {page.title()}")
                print(f"当前页面 URL: {page.url}")
        browser.close()
        print("浏览器已关闭")
except Exception as e:
    print(f"错误: {str(e)}")
print("测试完成！")
