# 路书生成范式与工作流 (Roadbook Generation Paradigm)

本文档阐述了 Roadbook 项目中关于“路书生成”的核心思考与设计规范。我们的目标是建立一套灵活且标准化的机制，支持从“无中生有”（0 -> 1）的自主探索，以及从“粗糙到标准”（1 -> 2）的人机协同优化。

## 1. 核心理念 (Core Philosophy)

*   **协同 (Synergy)**: 充分利用 CLI 的程序化能力（结构、校验）与 Agent Skill 的语义理解能力（探索、转换）。
*   **标准化 (Standardization)**: 无论过程如何灵活，最终产出必须是符合 [AARP 协议](./AARP_Protocol.md) 的标准路书。
*   **可控性 (Controllability)**: 在关键环节（如验证码、登录），AI 必须懂得“克制”，遵循 Fast Fail 原则，等待人类介入。

---

## 2. 生成模式 (Generation Modes)

### 2.1 模式一：人机协同优化 (From 1 to 2)

**场景**: 用户对业务流程有清晰认知，能提供大概步骤，但不愿处理繁琐的技术细节（如 CSS Selector、断言逻辑）。

**工作流**:
1.  **Scaffold (脚手架)**: 
    *   用户通过 CLI (`roadbook init`) 或编辑器创建一个“草稿路书”。
    *   **内容**: 包含大概的自然语言描述（如“点击搜索框”、“输入 iPhone”），甚至可以是截图、箭头标记。
    *   **结构**: 此时的路书结构完整，但 `action` 和 `params` 字段可能是空的或伪代码。
2.  **Refine (Agent 优化)**:
    *   用户调用优化指令（通过 Skill 触发）。
    *   **Agent 行为**: 
        *   读取草稿，理解用户意图。
        *   启动浏览器 (`agent-browser`) 实际执行流程。
        *   **Translation**: 将“点击搜索框”翻译为 `click(selector="#search-bar")`。
        *   **Validation**: 自动补充执行后的验证步骤（如“确认出现搜索结果列表”）。
3.  **Finalize (定稿)**:
    *   Agent 将补充完整的技术细节回写到路书文件中，形成可重复执行的标准版本。

### 2.2 模式二：Agent 自主探索 (From 0 to 1)

**场景**: 用户仅有一个明确的目标（Goal），完全委托 Agent 去探索如何达成。

**工作流**:
1.  **Define Goal (定义目标)**:
    *   用户指令: `roadbook init my-book --goal "在亚马逊搜索 Docker 书籍并按价格排序"`。
    *   CLI 生成一个仅包含 Goal 描述的空壳路书。
2.  **Explore (自主探索)**:
    *   Agent 基于 Goal 启动浏览器会话。
    *   **试错与回溯**: Agent 可能会走弯路（如点错链接后后退）。
    *   **Path Cleaning (路径清洗)**: **这是关键步骤**。Agent 在探索成功后，必须从繁杂的操作日志中提取出“最短正确路径”，过滤掉无效的尝试步骤。
3.  **Populate (填充)**:
    *   将清洗后的步骤序列化为标准 AARP 格式，填入路书文件。

---

## 3. 关键约束：Fast Fail 与 人工介入

在自动化探索过程中，AI 必须具备边界意识，严禁在未知的高风险领域“瞎猜”。

### 3.1 登录与验证码场景 (Login & CAPTCHA)
*   **现状**: 目前的探索模式暂**不包含**自动处理复杂的登录和验证码交互。
*   **策略**: 
    *   **主动暂停 (Pause for Human)**: 当 Agent 识别到页面要求登录、或出现滑块/文字验证码时，**必须**停止操作。
    *   **交互**: 提示用户 `[Waiting for Human Input]`，等待用户手动在浏览器中完成验证或登录操作，并发出“继续”指令后，Agent 才能恢复接管。
*   **Fast Fail**: 如果没有预置的凭证，且无法联系到用户，Agent 应直接报错退出，而不是尝试暴力破解或随机点击。

> *注: 登录场景的自动化（如通过 Cookie 注入、凭证管理）将作为独立的后续专题进行设计，不混入通用的探索流程中。*

---

## 4. CLI 与 Skill 的协同架构

为了支撑上述流程，CLI 工具与 Agent Skill 需要明确分工：

### 4.1 CLI (The Skeleton - 骨架)
CLI 负责提供“硬性”的工程支撑：
*   **`roadbook init`**: 生成标准目录结构和元数据文件（YAML Frontmatter）。
*   **`roadbook edit`**: 快速打开编辑器，方便人类介入修改草稿。
*   **`roadbook doctor`**: 校验生成的路书是否符合 AARP 协议规范（Schema Validation）。

### 4.2 Skill (The Soul - 灵魂)
Skill (`roadbook-explorer`) 负责“柔性”的智能处理：
*   **意图理解**: 从自然语言草稿中提取操作意图。
*   **动态执行**: 操控浏览器进行探索。
*   **数据清洗**: 从由杂乱的探索日志中提炼出干净的 Steps 数据。
*   **回写**: 调用文件写入工具，将 Result 注入 CLI 提供的骨架中。

---

## 5. 总结

| 维度 | 模式一 (1->2) | 模式二 (0->1) |
| :--- | :--- | :--- |
| **输入** | 粗糙的路书草稿 (Draft) | 明确的目标描述 (Goal) |
| **Agent 角色** | 翻译官 (Translator) & 优化师 (Optimizer) | 探路者 (Explorer) |
| **难点** | 准确理解非结构化的草稿意图 | 路径清洗与无效步骤过滤 |
| **共同点** | 都需要遵循 Fast Fail 原则，都产出标准 AARP 路书 |

此范式将指导后续 `roadbook-explorer` Skill 的 Prompt 设计以及 CLI `init` 命令的功能开发。
