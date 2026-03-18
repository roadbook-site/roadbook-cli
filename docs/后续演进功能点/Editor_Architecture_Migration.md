# Web Editor 架构演进方案：服务端托管 UI + 本地 API

## 1. 概述

当前 Roadbook Editor 采用传统的本地 Web 应用模式，即 Python 后端同时负责 API 服务和静态资源 (HTML/JS/CSS) 的托管。

本方案提议将前端 UI 剥离并托管在云端 (`https://editor.roadbook.site`)，而 Python 后端依然运行在用户本地。用户通过浏览器访问云端页面，云端页面通过 JavaScript 直接连接用户本地的 API (`localhost`) 进行数据交互。

这种 **"Remote UI + Localhost API"** 的架构模式在现代开发者工具（如 Jupyter, Weights & Biases）中已被广泛验证。

## 2. 核心交互逻辑

### 2.1 现状 (Local All-in-One)
*   **启动**：用户运行 `roadbook edit`。
*   **服务**：本地 Python 服务器启动在 `http://localhost:8000`。
*   **访问**：浏览器访问 `http://localhost:8000`。前端资源从本地加载，数据请求发往相对路径 `/api/...`。

### 2.2 目标架构 (Remote UI)
*   **启动**：用户运行 `roadbook edit`。
*   **服务**：本地 Python 服务器启动在 `http://localhost:8000` (只提供 API，不托管 UI)。
*   **访问**：CLI 自动打开浏览器访问 `https://editor.roadbook.site/?port=8000`。
*   **通信**：
    1.  浏览器加载云端的 `index.html` 和静态资源。
    2.  前端 JS 解析 URL 参数获取本地端口 (e.g., `8000`)。
    3.  前端 JS 向 `http://localhost:8000/api/...` 发起跨域 (CORS) 请求进行文件读写。

## 3. 技术实现细节

### 3.1 前端改造 (`index.html`)

前端需要具备动态识别 API 地址的能力。

**关键代码变更：**

```javascript
// 1. 获取 API Base URL
// 优先从 URL 参数获取端口，默认为 8000
const params = new URLSearchParams(window.location.search);
const port = params.get('port') || 8000;

// 如果当前页面就在 localhost (离线模式)，则使用相对路径；
// 否则 (在线模式)，指向本地服务器。
const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const API_BASE = isLocal ? '' : `http://localhost:${port}`;

// 2. 修改 API Client
const api = {
    getConfig: () => fetch(`${API_BASE}/api/config`).then(res => res.json()),
    changeDir: (path) => fetch(`${API_BASE}/api/chdir`, { ... }).then(res => res.json()),
    // ... 其他 API 调用同理
};
```

### 3.2 后端与 CLI 改造

1.  **CORS 配置 (已就绪)**：
    后端 `server/app.py` 必须保留并确保 `CORSMiddleware` 允许来自 `https://editor.roadbook.site` 的请求。
    ```python
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 或指定 ["https://editor.roadbook.site"] 增强安全性
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    ```

2.  **CLI 启动命令**：
    修改 `roadbook edit` 的启动逻辑，默认打开云端 URL。
    ```python
    # 伪代码
    browser_url = f"https://editor.roadbook.site/?port={port}"
    webbrowser.open(browser_url)
    ```

3.  **保留离线能力 (Fallback)**：
    为了支持无网环境，Python 包中仍建议保留一份最小化的 `index.html`。
    提供 `--local` 或 `--offline` 参数，强制打开本地托管的页面。

## 4. 方案优缺点分析

### ✅ 优势 (Pros)
1.  **极速迭代 (Instant Updates)**：
    *   修复 UI Bug、增加新功能（如新的标注工具、样式调整）只需部署服务端，所有用户刷新页面即刻生效，无需等待 Python 包发版和用户更新 (`pip install --upgrade`)。
2.  **包体积瘦身**：
    *   移除 `fabric.js`, `react` 等重型静态资源，显著减小 Python Wheel 包体积。
3.  **用户洞察**：
    *   便于在服务端页面集成 Analytics，统计功能使用率（如：多少人使用了“截图标注”功能），辅助产品决策。
4.  **体验统一**：
    *   确保所有用户看到的都是最新、一致的界面，避免因版本碎片化导致的兼容性支持困难。

### ⚠️ 考量与风险 (Cons)
1.  **混合内容 (Mixed Content) 与 HTTPS**：
    *   **问题**：现代浏览器默认禁止 HTTPS 页面加载 HTTP 资源。但 `http://localhost` 是特例，大多数浏览器（Chrome/Edge/Firefox）视为“安全上下文”，允许 `https://domain.com` 访问 `http://localhost`。
    *   **注意**：Safari 可能有更严格的限制，需进行特定测试。
2.  **网络依赖**：
    *   纯云端模式下，断网无法使用编辑器。**解决方案**：必须保留 `--offline` 本地模式作为兜底。
3.  **跨域安全**：
    *   需要确保 `localhost` API 不会被恶意网站滥用。建议在后端 CORS 配置中严格限制 `allow_origins=["https://editor.roadbook.site"]`。

## 5. 部署建议

1.  **域名**：使用 `editor.roadbook.site`。
2.  **CDN**：前端静态资源建议通过 CDN 分发（如 Vercel, Netlify, Cloudflare Pages），确保全球访问速度。
3.  **版本控制**：
    *   虽然 UI 是云端的，但 API 协议可能会变。
    *   前端需要做简单的版本握手检查：`GET /api/health` 返回后端版本号。如果后端版本过低，前端应提示用户运行 `pip install --upgrade roadbook`。
