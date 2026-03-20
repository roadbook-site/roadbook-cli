# AI-Agent Roadbook Protocol (AARP) Specification v4.0

## 1. 概述 (Overview)

**AARP (AI-Agent Roadbook Protocol)** 是一种声明式的、上下文感知的自动化协议，旨在成为人类意图与 AI 执行之间的标准桥梁。

> v4.0 更新: 
> 1. **Markdown-First**: 采用 Markdown 作为路书定义的载体，更加自然、易读。
> 2. **面向对象 (Object-Oriented)**: 引入“手稿页 (Sheet)”作为核心对象，打破线性的过程化描述。
> 3. **协议纯粹性 (Protocol Purity)**: 明确协议仅承载“知识与路标”，将运行时状态（脚本、日志、结果）剥离给 CLI 管理。

AARP 将自动化任务视为一次**“旅程”**。路书通过定义旅程中的关键**手稿页 (Sheets)**，引导 Agent 智能地完成任务。它不是一段可直接运行的代码，而是一份供 Agent 阅读和参考的**“探险手记”**。

## 2. 协议结构 (Schema)

AARP v4.0 路书是一个标准的 Markdown 文件，结构上分为 **Meta (元数据)** 和 **Sheets (手稿页列表)** 两大部分。

### 2.1 Meta (元数据)
使用 YAML Frontmatter 定义路书的身份标识、基本属性及运行参数。
元数据是路书的“身份证”，对于路书的索引、版本管理和执行环境配置至关重要。

**注意**：Meta 中**不包含**任何运行时状态（如 `last_run_status`）、脚本路径（如 `script_path`）或本地环境绑定信息。这些信息由 CLI 的 Runtime 模块在本地维护。

```yaml
---
id: "rb-amazon-checkout-v1"  # [新增] 路书唯一标识符
name: "Amazon Checkout"
version: "4.0"               # 协议版本
owner: "user_123"            # 责任人/创建者
platform: "desktop"          # desktop | mobile
locale: "zh-CN"              # 语言环境 (e.g. zh-CN, en-US)
region: "CN"                 # 适用地域 (e.g. CN, US)
entry_url: "https://www.amazon.com" # [新增] 路书入口URL
description: "在亚马逊上搜索商品并完成下单流程"
inputs:                      # 输入参数定义
  keyword: "搜索关键词"
  max_price: "最高价格限制"
outputs:                     # 输出数据定义
  order_id: "订单编号"
  total_amount: "总金额"
---
```

### 2.2 Roadbook Sheets (路书手稿页)

在 AARP v4.0 中，路书被隐喻为一本包含多张手稿（Sheets）的活页指南。每一张（Sheet）对应任务旅程中的一个特定场景（Scene）或逻辑闭环。

**拆分原则 (Granularity)**:
*   **一页一景 (One Sheet, One Scene)**: 通常，当 URL 发生变更，或者页面视图发生重大切换（如全屏弹窗）时，应翻开新的一页。
*   **逻辑分块 (Logical Block)**: 即使在同一个 URL 下，如果任务包含多个相对独立的逻辑步骤（如“填写表单”和“上传文件”），也可以拆分为不同的 Sheet。
*   **不要跨页**: 避免在一个 Sheet 中描述跨越多个不同 URL 的长流程。

#### 2.2.1 Sheet (基础手稿页)
**Sheet** 是路书的基础组成单元。一个标准的 Sheet 包含以下要素：
*   **Title**: 页标题（对应 Markdown 的 `##` 标题），通常包含该页的意图摘要。
*   **ID**: 页唯一标识符。建议使用 4-5 位的短随机码（如 `a1b2`），作为内部索引键。
*   **Type** (Optional): 页类型，用于指示运行时的执行策略。默认为 `process`。
    *   `setup`: 环境检查与前置准备（如：确认浏览器启动方式、连接状态、以及是否满足登录校验）。
    *   `process`: 标准业务流程（默认）。
    *   `delivery`: 结果交付与用户反馈（如：展示文件路径、确认数据提取）。
*   **Description**: 对当前页任务的自然语言描述。
*   **URL** (Optional): 该页对应的 Web 页面 URL 模式（定义了“在哪一页”执行）。
*   **Locators** (Optional): 关键元素的语义化定位符（用于确认“是否在这一页”）。
*   **Reference** (Optional): 参考图片，辅助视觉确认。
*   **Steps** (Optional): 在该页上执行的具体动作序列


### 2.3 Action Primitives (标准动作原语)

为了保证路书的可执行性，**Steps** 部分的描述应尽量遵循统一的动作原语。推荐格式为：`ACTION [Selector] [Value/Options]`。

| 动作 (Action) | 描述 (Description) | 语法示例 (Syntax) |
| :--- | :--- | :--- |
| **GOTO** | 跳转到指定 URL | `GOTO "https://example.com"` |
| **CLICK** | 点击元素 | `CLICK "#submit-btn"` |
| **INPUT** | 在输入框填写内容 | `INPUT "#search" "keyword"` |
| **PRESS** | 模拟键盘按键 | `PRESS "Enter"` |
| **HOVER** | 鼠标悬停 | `HOVER ".menu-item"` |
| **WAIT** | 等待时间或条件 | `WAIT 5000` (ms) 或 `WAIT "networkidle"` |
| **CHECK** | 勾选复选框 | `CHECK "#agree-terms"` |
| **SELECT** | 下拉框选择 | `SELECT "#country" "China"` |
| **EXTRACT** | 提取数据 | `EXTRACT "text" FROM ".price"` |
| **SCROLL** | 滚动页面 | `SCROLL "bottom"` 或 `SCROLL 500` |
| **ASSERT** | 断言条件 | `ASSERT "text=登录成功" EXISTS` |

> **Note**: Action Primitives support fallback selectors. If you provide a list of selectors (e.g., `CLICK ["#id", ".class"]`), the executor should try them in order until one succeeds.

### 2.4 Reference Images (参考图片)

路书中可以使用图片来辅助 Agent 定位 (Landmark) 或操作 (Step)。推荐使用标准的 Markdown 图片语法，并支持本地路径与远程 URL。

*   **Syntax**: `![Image Description](Path/To/Image)`
*   **Best Practice**: 
    *   **Local**: `./assets/login_btn.png` (推荐，随路书一起分发)
    *   **Remote**: `https://example.com/assets/login_btn.png` (需确保网络可达)

### 2.5 路书目录结构 (Roadbook Directory Structure)

AARP v4.0 将路书定义为一个包含多层级信息的标准目录包。这种结构设计确保了**“本体定义”**、**“执行逻辑”**与**“运行结果”**的清晰解耦。

一个标准的路书包（Roadbook Package）包含以下四个核心层级：

*   **本体层 (The Roadbook)**: 
    *   **性质**: 静态、核心、可分享。
    *   **内容**: 任务意图、关键路标、断言条件、输入输出定义。
    *   **载体**: 根目录下的 `roadbook.md` 文件。它是路书的 Single Source of Truth。
*   **脚本层 (The Script)**:
    *   **性质**: 静态、逻辑实现、可版本控制。
    *   **内容**: 路书对应的自动化执行脚本（如 Python Playwright）。
    *   **载体**: `scripts/` 目录。
        *   入口文件通常为 `scripts/script.py`。
        *   该目录可包含 `utils/` 等辅助模块，与 `roadbook.md` 同级，随路书一起分发。
*   **输出层 (The Output)**:
    *   **性质**: 动态、持久化、结构化。
    *   **内容**: 每次运行产生的交付物。
        *   **结构化数据**: 如抓取的商品列表 (`products.json`)、提取的表格 (`data.csv`)。
        *   **媒体文件**: 关键步骤截图、下载的文件（PDF/Excel）。
    *   **载体**: `outputs/` 目录。
        *   **目录结构**: 建议按**运行ID (Run ID)** 隔离，即 `outputs/<run_id>/`。
        *   此目录应在 `.gitignore` 中被忽略（除非特定的样例数据），不随路书代码分发。
*   **运行时层 (The Runtime)**:
    *   **性质**: 动态、临时、本地隐私。
    *   **内容**: 
        *   **系统日志**: 详细的 debug 日志、报错堆栈。
        *   **浏览器状态**: User Data Dir、Cookies、Local Storage、Session 缓存。
        *   **临时文件**: 运行时生成的中间文件。
    *   **载体**: `.roadbook/` 隐藏目录（项目级）或 `~/.roadbook`（全局级）。此目录完全由 CLI 管理，不应被提交到版本控制。

**目录结构示例**:
```text
my-roadbook-project/
├── roadbook.md           # [本体层] 任务定义
├── scripts/              # [脚本层] 自动化逻辑
│   ├── script.py         #    入口脚本
│   └── utils.py
├── outputs/              # [输出层] 运行结果 (Git Ignored)
│   ├── run_20231001_a1/  #    按 Run ID 隔离
│   │   ├── data.json
│   │   └── screenshot.png
│   └── latest/           #    指向最新运行结果的软链 (可选)
└── .roadbook/            # [运行时层] 系统缓存 (Git Ignored)
    ├── runtime/
    └── logs/
```

这种分层设计确保了：
1.  **可移植性**: `roadbook.md` 和 `scripts/` 构成了完整的可执行单元。
2.  **数据隔离**: 用户数据 (`outputs/`) 与系统状态 (`.roadbook/`) 分离，便于用户管理和归档结果。
3.  **清晰交付**: 用户只需关注 `outputs/` 目录即可获取所有价值产出。

## 3. 路书正文示例 (Roadbook Body)

路书正文通过 Markdown 的标题层级来组织节点。建议使用二级标题 (`##`) 定义主要节点。

```markdown
## 启动与搜索
**ID**: a1b2
**Description**: 打开亚马逊主页并搜索指定商品。
**URL**: `https://www.amazon.cn`

**Steps**:
1. `GOTO "https://www.amazon.cn"`
2. `INPUT "#twotabsearchtextbox" "{keyword}"`
3. `CLICK "#nav-search-submit-button"`
4. `WAIT "networkidle"`

---

## 列表页定位
**ID**: 3c4d
**Description**: 确认已进入搜索结果页。
**URL**: `s?k=`
**Locators**: `text="结果"`, `.s-result-list`

---

## 选择商品
**ID**: 5e6f
**Description**: 从列表中选择第一个符合价格要求的商品。
**Reference**: ![Target Product Example](./assets/product_example.png)

**Steps**:
1. `WAIT ".s-result-item"`
2. `CLICK ".s-result-item:has-text('{price}') img"` (使用 Playwright 扩展语法)

---

## 详情页验证
**ID**: 7g8h
**Description**: 验证是否成功进入商品详情页且商品有货。

**Assertions (断言)**:
- 页面标题包含商品名称
- 存在 "加入购物车" 按钮 (`#add-to-cart-button`)
- 价格显示正常

---

## 结账
**ID**: 9i0j
**Description**: 将商品加入购物车并完成下单。

**Steps**:
1. `CLICK "#add-to-cart-button"`
2. `WAIT 2000`
3. `CLICK "input[name='proceedToRetailCheckout']"`

---

## 结果交付 (Delivery)
**ID**: delivery
**Description**: 验证订单已生成并提取关键信息。

**Assertions**:
- 订单号已提取
- 支付状态确认
```

## 4. 最佳实践 (Best Practices)

### 4.1 拆分粒度 (One Sheet, One Scene)
不要把所有操作都塞进一个 Sheet。务必遵循“一页一景”原则。
*   **Good**: 
    *   Sheet 1: 登录页输入账号密码 -> 点击登录
    *   Sheet 2: 首页验证登录成功 -> 搜索商品
*   **Bad**: 
    *   Sheet 1: 登录 -> 搜索 -> 详情页 -> 下单 (跨越了多个 URL 和场景)

### 4.2 显式定义“坑”
不要让 Agent 去猜。如果你知道某个步骤容易失败（比如网络延迟大、弹窗多），请务必在 **Pitfalls** 章节显式写出来。

### 4.5 脚本与本体分离 (Script Separation)

Agent 在执行路书时，可能会将其“编译”为可执行脚本（如 Python Playwright 脚本）以提升效率和减少 Token 消耗。

*   **原则**: 脚本是运行时的**优化产物**，不是本体的一部分。
*   **实践**: 
    *   不要把脚本代码直接写在路书 Markdown 里（除非是作为示例）。
    *   不要在 Meta 中指定 `script_path: /local/path/to/script.py`。
    *   CLI 会根据路书 ID 在本地 Runtime 目录中查找或生成对应的脚本。

### 4.6 语义化选择器优先 (Semantic Selectors First)
为了提高路书的鲁棒性和可读性，强烈建议优先使用**语义化选择器**，避免使用脆弱的 CSS/XPath 路径。这与 Playwright 的最佳实践一致。

*   **推荐 (Recommended)**:
    *   `text="Login"` (通过文本内容定位)
    *   `label="Username"` (通过表单关联 Label 定位)
    *   `placeholder="Search"` (通过占位符定位)
    *   `role="button", name="Submit"` (通过 ARIA 角色定位)
    *   `data-testid="submit-btn"` (通过测试专用属性定位)

### 4.7 鲁棒性与多重选择器 (Robustness & Fallback)
由于现代网页经常变动，单一选择器容易失效。建议在定义关键动作时提供**备选方案 (Fallback)**。

*   **Syntax**: `CLICK ["selector_primary", "selector_secondary"]`
*   **Example**: `CLICK ["#submit-btn", "button:has-text('Submit')", "input[type='submit']"]`
*   **Behavior**: 执行器应依次尝试列表中的选择器，直到找到一个可操作的元素为止。如果所有选择器都失败，则抛出异常或寻求人工介入。

### 4.8 显式定义下载行为 (Download Handling)
虽然路书本身不强制要求具体的下载路径，但在涉及到文件下载时，建议使用明确的指令或描述，指导执行器进行文件管理。

*   **Example**: `CLICK "Download"` (Implicit) -> Executor implies download.
*   **Better**: `DOWNLOAD_TO "/path/to/save"` (Explicit) -> Executor intercepts the download and saves it to the specific path.

*   **避免 (Avoid)**:
    *   `div > div:nth-child(3) > span` (脆弱的层级结构)
### 4.4 视觉高亮 (Visual Highlighting)

在生成参考图片（Reference Images）时，强烈建议通过脚本为目标元素动态添加高亮边框（如红色 `2px solid red`）。这能显著提升人类审核者和多模态 Agent 对操作对象的识别效率。

**实现技巧 (Playwright 示例)**:
在截图前注入 JS 修改样式，截图后还原。

```python
# 1. Highlight
element.evaluate("el => el.style.border = '3px solid red'")

# 2. Screenshot
page.screenshot(path="ref_image.png")

# 3. Restore (Optional)
element.evaluate("el => el.style.border = ''")
```

![Highlight Example](./assets/highlight_example.png)


