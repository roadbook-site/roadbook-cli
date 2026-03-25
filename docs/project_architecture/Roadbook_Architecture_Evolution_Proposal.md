# Roadbook CLI 架构重构与演进提案 (SDK化与去 Daemon 化)

**日期**: 2026-03-24
**状态**: 草案 / 待讨论

---

## 1. 核心痛点与历史遗留问题 (To-Do 清单)

当前 `roadbook-cli` 架构存在两个主要瓶颈，这也是我们本次重构需要解决的历史包袱：

- [ ] **痛点 1: 脚手架模式导致的“野马”代码**
  - **现状**: CLI 目前通过生成样板代码（如 `browser.py.tpl`）将底层的 Playwright API 直接暴露给大模型。
  - **问题**: 缺乏统一的输入输出 (I/O) 定义、缺乏敏感信息脱敏的日志系统、缺乏对执行过程（Sheet）的精准监控，导致生成的脚本极难被上层系统统一调度和审计。
- [ ] **痛点 2: `agent-browser` 引入的过度复杂性**
  - **现状**: 采用 Client-Daemon 嵌套模式，通过 subprocess 调用 `agent-browser` CLI 来维持浏览器会话。
  - **问题**: 在 Windows 环境下运行极不稳定，极易产生僵尸进程；且这层封装属于“黑盒”，反而限制了 Playwright 原生能力的发挥，增加了调试难度。
- [ ] **痛点 3: 文档与代码脱节**
  - **现状**: `roadbook.md` 和生成的 `script.py` 之间缺乏强制约束。
  - **问题**: Agent 可能会修改代码逻辑而忘记更新文档，导致 `roadbook.md` 失去作为“单一事实来源 (Single Source of Truth)”的权威性。

---

## 2. 新架构整体构思：轻量化、SDK 驱动、文档为王

我们的核心目标是将 Roadbook 从一个“代码生成工具”升级为一个**“受控的自动化执行框架”**，参考 Apify Actor 的优秀设计理念，但不盲目照搬，做适合本地桌面自动化的精简设计。

### 2.1 彻底移除 `agent-browser` 依赖
**构思**: 放弃 Daemon 守护模式，回归纯粹的 **"Python 进程直驱 Playwright"**。
**细节**:
- 将管理浏览器生命周期（包括 CDP 附着、持久化上下文等）的能力内化到全新的 `roadbook-sdk` 中。
- 借助现有的大模型能力（如 Trae / Cursor），直接阅读我们的 SDK 规范和路书文档，生成原生且健壮的 Playwright 代码。

### 2.2 引入 `roadbook-sdk` (核心抽象层)
**构思**: 不再让用户/Agent 裸写 Playwright 的初始化代码，而是提供统一的上下文管理器 `RoadbookContext`。
**细节**:
- **生命周期接管**: `with RoadbookContext() as rb:` 自动处理浏览器启动、异常捕获、现场截图和资源释放。
- **标准化 I/O**: 提供 `rb.get_input()` 和 `rb.push_data()`，严格规范数据的流入和流出。
- **存储抽象 (Storage)**: 提供 `rb.storage.save_screenshot()` 等接口，确保每次执行的产物（Artifacts）都被整齐地收拢在 `runtime/runs/<run_id>` 目录下。

### 2.3 “文档驱动执行” (Documentation-Driven Execution)
**构思**: 让 `roadbook.md` 成为唯一的执行契约。
**细节**:
- **Markdown Schema 化**: 利用 Markdown 的 YAML Frontmatter (或约定格式的表格) 定义 `inputs` 和 `outputs`，SDK 在初始化时自动加载并作为校验依据。
- **Sheet 级强绑定 (Sheet Binding)**: SDK 提供 `with rb.sheet("Sheet 1")` 语法。代码必须声明当前正在执行 `.md` 文档中的哪一个 Sheet。这不仅能防止代码腐化，还能为未来的 Web UI 进度条渲染和“断点续跑”打下坚实基础。

### 2.4 Agent 探索与 Script Sheet 机制
**构思**: 规范化 Agent 的代码探索和文档更新流程，确保程序化输出与 `roadbook.md` 中的 Sheet 结构保持映射关系。
**细节**:
- **Script Sheet 数据结构**: 参考 Apify 规范（如 `dataset_schema.json`）引入 `Script Sheet` 数据结构定义。该结构与 MD 文档中的 Sheet 严格对应，用于程序化地描述输入输出规范和动作逻辑。
- **程序化输出与探索**: Agent 在探索未知网页时，通常先编写探测脚本（Exploration Script）。脚本运行后，除了完成探索动作外，还会以程序化的方式生成一个初始的 `Script Sheet` 输出（如 JSON 结构）。
- **人工/Agent 修正与回填**: 程序化输出的初始 Sheet 数据不能直接使用，需经由 Agent 的二次审视与修正（如去重、清理无效数据、补全上下文）。修正后的标准内容最终被回填到 `roadbook.md` 中作为一个正式的 Sheet。这确保了探索过程沉淀出的文档既结构化，又经过了智能校验。

---

## 3. 新架构行动计划 (Roadmap)

### 阶段一：清理与破冰 (Cleanup & Prep)
1. **废除 `agent-browser`**: 删除项目中所有与 `agent-browser`、Daemon 相关的文档描述和调用代码。
2. **清理冗余模块**: 清理 `runtime.py` 等文件中为适配多进程而写的回调或轮询逻辑。

### 阶段二：打造核心 `roadbook-sdk`
1. **提取 SDK 包**: 在 `src/roadbook/` 下创建 `sdk/` 目录，封装 `context.py`、`io.py`、`logger.py` 和 `storage.py`。
2. **实现 MD 解析器**: 开发能够解析 `roadbook.md` 提取 Schema 和 Sheet 列表的工具类。
3. **实现 Sheet 钩子**: 在 `RoadbookContext` 中实现 `rb.sheet()` 逻辑，并与终端输出（及未来的 UI）打通。

### 阶段三：重构脚手架与 Agent 技能
1. **极简模板**: 修改 `script.py.tpl`，只保留 `from roadbook.sdk import RoadbookContext` 的空骨架。
2. **更新 Agent Prompt**: 修改 `roadbook-explorer` 和 `roadbook-executor` 的系统提示词，教导 Agent 必须遵守新的 SDK 规范（如强制使用 `rb.sheet` 和 `rb.push_data`），不再提及 `agent-browser`。
3. **整合 Script Sheet 工作流**: 为 Agent 增加基于 `Script Sheet` 结构化输出与文档回填的工作流能力。

### 阶段四：测试与验证
1. 挑选 2-3 个典型的抓取/自动化场景，使用新架构从头生成路书并执行。
2. 验证运行目录 (`runs/`) 下的日志、截图、JSON 产物是否结构清晰、规范。

---
*注：本提案作为我们深入探讨的基石。确认方向无误后，我们再逐个模块展开编码。*
