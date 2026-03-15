# 浏览器配置与使用指南 (Browser Configuration & Usage Guide)

本文档旨在解决 Roadbook 在浏览器自动化场景下的配置难点，包括如何连接浏览器、Agent 导入配置、常见问题（如验证码）的处理方案，以及在 CI/CD 环境中的集成策略。

## 1. 浏览器连接配置 (Browser Connection)

### 1.1 连接方式
Roadbook 支持多种方式连接浏览器，以适应不同的开发和运行环境。

*   **本地连接 (Local Direct)**: 直接启动本地安装的 Chrome/Edge 浏览器。
    *   *适用场景*: 本地开发调试。
    *   *配置*: 默认模式，无需特殊配置，确保本地已安装浏览器即可。
*   **远程调试连接 (Remote Debugging)**: 连接到已开启远程调试端口的浏览器实例。
    *   *启动命令*: `chrome.exe --remote-debugging-port=9222`
    *   *配置*: 在 Roadbook 中指定 CDP 地址 (e.g., `http://localhost:9222`)。
*   **WSS 连接 (WebSocket)**: 连接到远程浏览器集群或无头浏览器服务（如 Browserless）。
    *   *配置*: 设置 `browser_wss_endpoint`。

### 1.2 Agent 导入与配置
为了让 Agent 能够控制浏览器，需要正确导入并配置相关工具。

*   **Playwright 集成**:
    Roadbook 推荐使用 Playwright 作为底层自动化驱动。
    ```python
    from playwright.sync_api import sync_playwright

    def run(playwright):
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        # ... 业务逻辑 ...
    ```

*   **Roadbook Agent 配置**:
    在 Roadbook 的 Agent 配置中，确保声明了浏览器相关的 Skill 或 Capability。

## 2. 常见问题与解决方案 (Common Issues & Solutions)

在使用浏览器进行自动化任务时，常会遇到反爬虫机制和环境差异导致的问题。

### 2.1 验证码处理 (Captcha Handling)
网站通过验证码（Captcha）阻止自动化脚本是常见障碍。

*   **图形验证码**:
    *   *解决方案*: 使用 OCR 工具（如 Tesseract）或第三方打码平台 API。
*   **滑块验证码**:
    *   *解决方案*: 使用图像识别算法计算滑动距离，模拟人类轨迹拖动。
*   **reCAPTCHA / hCaptcha**:
    *   *解决方案*:
        *   **2Captcha / Anti-Captcha**: 通过 API 对接人工打码服务（推荐，稳定性高）。
        *   **浏览器插件**: 在自动化浏览器中加载自动解决验证码的插件（如 `YesCaptcha`）。

### 2.2 浏览器指纹 (Browser Fingerprinting)
部分网站会检测浏览器指纹（如 WebDriver 属性）来识别自动化工具。

*   **解决方案**:
    *   使用 `playwright-stealth` 插件隐藏自动化特征。
    *   禁用 `navigator.webdriver` 标志。
    *   随机化 User-Agent 和窗口尺寸。

## 3. CI/CD 集成 (CI Integration)

在持续集成环境中运行浏览器自动化任务需要特别关注环境依赖和资源消耗。

### 3.1 Headless 模式
CI 环境通常没有图形界面，必须以 Headless（无头）模式运行浏览器。
*   *配置*: `browser.launch(headless=True)`
*   *注意*: Headless 模式下的渲染行为可能与有头模式不一致，建议在本地先进行 Headless 调试。

### 3.2 依赖管理
确保 CI 容器中安装了浏览器及其依赖库。
*   **Playwright**: 使用官方提供的 Docker 镜像 `mcr.microsoft.com/playwright:v1.xx.x-jammy`，已预装所有浏览器依赖。

### 3.3 示例配置 (GitHub Actions)
```yaml
name: Browser Automation Test
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    container:
      image: mcr.microsoft.com/playwright:v1.40.0-jammy
    steps:
      - uses: actions/checkout@v3
      - name: Install dependencies
        run: npm ci
      - name: Run Roadbook Script
        run: roadbook run my_script.md
```

### 3.4 调试与构件 (Artifacts)
CI 运行失败时，保留现场证据至关重要。
*   **截图/录像**: 配置测试框架在失败时自动截图或录制视频。
*   **Trace Viewer**: Playwright 支持记录完整的执行轨迹（Trace），可在 CI 失败后上传为 Artifact，便于本地回放分析。

## 4. CLI 引导与诊断设计 (CLI Guidance & Diagnostics)

为了在用户遇到问题时提供即时帮助，Roadbook CLI 将在“必经之路”（运行、脚本开发）上植入智能引导机制。

### 4.1 主动诊断 (Proactive Diagnostics)
新增 `roadbook doctor` 命令，用于一键检查环境健康度。

*   **检查项**:
    *   **Python 环境**: 版本是否满足要求 (>=3.8)。
    *   **Playwright**: 是否安装了 `playwright` 包及对应的浏览器二进制文件。
    *   **Node.js**: 是否存在（用于 JS/TS 脚本）。
    *   **CDP 连接**: 尝试连接 `localhost:9222` 验证远程调试端口是否开启。
    *   **网络**: 检查是否能访问关键服务（如 GitHub, npm）。

### 4.2 运行时拦截 (Runtime Interception)
增强 `roadbook run` 的错误处理逻辑，针对常见错误提供“人话”建议。

*   **TargetClosedError**:
    *   *现象*: 浏览器意外关闭。
    *   *引导*: "浏览器似乎意外退出了。请检查内存是否不足，或者是否手动关闭了窗口。建议增加 `slow_mo` 参数减缓执行速度。"
*   **ConnectionRefusedError (CDP)**:
    *   *现象*: 无法连接到调试端口。
    *   *引导*: "无法连接到 Chrome 调试端口 (9222)。请确保已运行 `chrome.exe --remote-debugging-port=9222`。"
*   **TimeoutError**:
    *   *现象*: 等待元素超时。
    *   *引导*: "查找元素超时。请检查页面是否加载完成，或者选择器是否依然有效。您可以尝试使用 `roadbook open` 进入交互模式调试选择器。"

### 4.3 交互式引导 (Interactive Guidance)
在 `roadbook open` 或首次运行失败时，提供交互式问答。

*   **场景**: 用户运行脚本失败，且错误提示找不到浏览器。
*   **引导**:
    ```text
    [!] 未检测到浏览器环境。
    ? 您希望如何连接浏览器？
      > 启动本地浏览器 (自动安装 Playwright)
      > 连接已有的远程调试端口 (localhost:9222)
      > 使用云端浏览器 (WSS)
    ```
