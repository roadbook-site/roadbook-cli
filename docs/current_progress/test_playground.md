# 路书 MVP 测试靶场与实操路线

这份文档整理了用于测试路书（Roadbook）MVP 核心能力（基于语义路标、非刚性自动化、人机协同）的经典挑战和靶场。你可以勾选复选框来追踪你的测试进度。

## 🎯 核心测试靶场

### 1. 终极语义路标测试：RPA Challenge
* **网址**: [rpachallenge.com](https://rpachallenge.com/)
* **挑战内容**: 网站提供了一个包含 10 行数据的 Excel 文件。你需要点击 "Start"，然后将数据填入网页表单并提交。
* **核心验证点**: 
  * **动态 DOM 的噩梦**：每次点击 Submit 后，表单中输入框的**位置**和 **HTML ID** 都会完全随机改变！传统的 XPath 或 ID 定位会立刻崩溃。
  * **语义匹配**：验证 Agent-Browser 能否真正通过“视觉/语义”找到正确的输入框（例如 `landmark: { role: "textbox", keyword: "First Name" }`），而不是依赖底层 DOM 结构。

### 2. 复杂交互与异常挂起测试：The Internet (by Sauce Labs)
* **网址**: [the-internet.herokuapp.com](https://the-internet.herokuapp.com/)
* **挑战内容**: 专门为自动化测试搭建的“刁钻场景”集合站，包含了网页交互中所有让人头疼的边缘情况。
* **推荐测试子任务**:
  * [ ] **Dynamic Loading (动态加载)**: 点击按钮后，元素会在随机延迟后才出现在 DOM 中。👉 *验证 `wait` 机制和 `dom_stable` 条件。*
  * [ ] **Challenging DOM (挑战性 DOM)**: 页面上有一堆长得一样的按钮，且 ID 都在动态变化，还有一个巨大的 Canvas 干扰。👉 *验证精简 DOM 提取和 `@eXX` 标记能力。*
  * [ ] **Basic Auth / Login (登录)**: 👉 *验证 `wait_for_human`（人类介入）机制，遇到复杂登录时挂起，人类输入后再 `continue`。*

### 3. 现代 Web 框架与 AJAX 测试：Scrape This Site
* **网址**: [scrapethissite.com](https://www.scrapethissite.com/pages/)
* **挑战内容**: 提供了几个不同技术栈的沙盒页面。
* **推荐测试子任务**:
  * [ ] **Oscar Winning Films (AJAX)**: 数据是通过 JavaScript 异步加载的。👉 *验证路书在执行 `goto` 后，能否正确等待网络请求停止（`networkIdle`）再进行下一步。*
  * [ ] **Spoofing Headers (伪造请求头)**: 👉 *验证 CDP 底层能否有效绕过基础的反爬校验。*

### 4. 列表与翻页提取测试：ToScrape
* **网址**: [toscrape.com](https://toscrape.com/) (包含 Books to Scrape 和 Quotes to Scrape)
* **挑战内容**: 模拟真实的电商网站和名言网站。
* **核心验证点**:
  * 测试**“阶段划分 (Stage)”**能力。例如：Stage 1 搜索某本书 -> Stage 2 点击进入详情页 -> Stage 3 提取价格。验证路书能否在多个页面跳转间保持状态稳定。

### 5. 进阶：学术界 Agent 评测基准 (WebArena / Mind2Web)
* **WebArena**: 包含电商、论坛、CMS、GitLab 等真实开源软件搭建的沙盒。任务类似：“在购物网站上找到评价最高的 256GB 手机并加入购物车”。
* **Mind2Web**: 跨网站的复杂任务，比如：“在 Expedia 上订一张明天从纽约到伦敦的单程机票”。
* *注：MVP 阶段仅作为灵感参考，暂不需要跑完整的评测框架。*

---

## 🚀 建议的 MVP 实操路线图

- [ ] **第一战 (Hello World)：基础流程跑通**
  - **目标**: [Quotes to Scrape](https://quotes.toscrape.com/)
  - **任务**: 录制一个“点击 Login -> 输入假账号密码 -> 点击 Submit”的路书。
  - **验证**: 跑通最基础的 `goto`, `type`, `click` 动作。

- [ ] **第二战 (核心能力自证)：动态 DOM 挑战**
  - **目标**: [RPA Challenge](https://rpachallenge.com/)
  - **任务**: 录制填写一个人的信息并提交。然后回放。
  - **验证**: 系统能否在表单大变样的情况下，依然准确填入数据。（只要这个跑通，项目的核心价值就立住了！）

- [ ] **第三战 (人机协同)：真实世界挂起与恢复**
  - **目标**: 真实的网站（如 GitHub 或 V2EX 的登录页）
  - **任务**: 录制到输入密码环节触发 `wait_for_human`，在真实浏览器里手动过掉图形验证码，然后在终端敲 `roadbook continue`。
  - **验证**: 系统能否顺利挂起，并在人类介入后接管后续的验证工作。
