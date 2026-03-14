from playwright.sync_api import Playwright, sync_playwright, expect

def run():
    # 连接到本地已经运行的 Chrome 实例
    # 注意：需要先启动 Chrome，命令如下（Windows）：
    # "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9224 --user-data-dir="C:\chrome_dev_temp"
    
    try:
        with sync_playwright() as p:
            print("正在尝试连接到本地 Chrome (端口 9224)...")
            # 使用 connect_over_cdp 连接到指定端口
            browser = p.chromium.connect_over_cdp("http://localhost:9224")
            
            # 获取当前上下文（通常连接上来会有一个默认上下文）
            default_context = browser.contexts[0]
            
            # 创建一个新页面或使用现有页面
            page = default_context.new_page()
            
            # 开启 Playwright Inspector (调试器)，点击 "Record" 按钮即可开始录制操作并生成代码
            # 这就是如何在现有浏览器连接中通过代码触发录制功能的方法！
            print("正在暂停脚本以启动 Inspector... 请在弹出的窗口中点击 'Record' 开始录制")
            page.pause() 
                
            page.goto("https://www.chanmama.com/")

            # 悬停在“抖音分析平台”上
            page.get_by_role("link", name="抖音分析平台").first.hover()
            # 悬停后点击出现的子菜单项
            with page.expect_popup() as page2_info:
                page.get_by_role("link", name="找视频 打造爆款视频").click()
            
            # 获取新弹出的页面
            page2 = page2_info.value
            page2.wait_for_load_state("networkidle")
            print(f"新页面标题: {page2.title()}")

            # 在新页面操作
            try:
                page2.get_by_text("带货视频").nth(1).click()
                page2.get_by_role("textbox", name="请输入视频标题、商品标题或达人昵称").click()
                page2.get_by_role("textbox", name="请输入视频标题、商品标题或达人昵称").fill("胡说老王")
                page2.get_by_role("textbox", name="请输入视频标题、商品标题或达人昵称").press("Enter")
                
                # 等待搜索结果加载
                page2.wait_for_timeout(3000)
                print("搜索完成")
            except Exception as e:
                print(f"新页面操作出错: {e}")

            # 关闭新页面
            page2.close()


            

            
            # 等待页面加载完成
            page.wait_for_load_state("networkidle")
            
            print(f"页面标题: {page.title()}")
            
            # 模拟自动记录生成的代码操作
            # 这里我们尝试获取一些页面上的文本数据作为示例
            # 例如获取导航栏的文本
            nav_items = page.locator(".header-nav-item").all_inner_texts()
            if nav_items:
                print("导航栏项目:", nav_items)
            else:
                print("未找到导航栏项目，尝试打印页面部分文本...")
                print(page.locator("body").inner_text()[:200])

            # 探索：尝试点击“抖音”相关链接（如果有）
            # 注意：实际选择器需要根据页面结构调整，这里使用文本选择器演示
            try:
                douyin_link = page.locator("text=抖音")
                if douyin_link.count() > 0:
                    print("找到'抖音'相关链接，尝试点击...")
                    douyin_link.first.click()
                    page.wait_for_timeout(2000) # 等待2秒
                    print("点击后的页面标题:", page.title())
                else:
                    print("未找到明确的'抖音'文本链接")
            except Exception as e:
                print(f"点击操作仅供演示，发生错误: {e}")

            print("演示结束，关闭页面（不关闭浏览器）")
            page.close()
            # browser.close() # 通常不关闭连接的浏览器实例
            
    except Exception as e:
        print(f"发生错误: {e}")
        print("请确保 Chrome 已使用 --remote-debugging-port=9224 启动")

if __name__ == "__main__":
    run()
