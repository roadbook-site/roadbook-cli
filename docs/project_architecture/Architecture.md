# Roadbook System Architecture

本系统（Roadbook）的核心隐喻从单纯的“车载导航”升级为更具适应性的**“野外探险向导 (Wilderness Trekking Guide)”**。现代网页结构复杂多变，如同不断变化的地形，标准的城市导航（固定路线）往往容易失灵，需要更灵活的指引与决策。

## 1. 核心概念与隐喻 (Core Concepts)

系统采用标准的技术命名，但其设计哲学深受**“野外探险”**隐喻的启发。

| 系统组件 | 核心隐喻 | 隐喻解读与设计原则 |
| :--- | :--- | :--- |
| **Roadbook (路书)** | **Expedition Log (探险手记)** | 路书不是僵化的地图，而是前人留下的**探险手记**。它不仅记录了关键地标（特征）和必经之路，更重要的是提供**环境诊断**与**操作指引**。当 Agent 迷路或环境缺失时，它能告知 Agent "缺什么、装什么、脚本放哪"，一步步引导 Agent 完成任务。 |
| **Agent (智能体)** | **Explorer (探险家)** | 系统的主导者与决策者。他不仅是阅读路书的人，也是在迷路时（脚本失效）能够通过视觉和语义理解自主探索新路径的人。**Agent 拥有最高控制权**。 |
| **Guide (系统)** | **Sherpa (夏尔巴向导)** | 指代整个 Roadbook 运行时系统（CLI + Runtime）。它负责背负重物（浏览器操作、数据搬运、脚本管理），并主动提供环境检查与步骤引导，辅助探险家决策。 |
| **CLI (工具箱)** | **Gear (装备)** | 探险家的交互界面。除了执行命令，它更是一个**语义引导向导**。报错不仅仅是 Error，而是 Actionable Advice（可执行建议）。 |
| **Context (上下文)** | **Backpack (背包)** | 随身携带的记忆与物资。装着当前的装备（Session）、采集到的样本（Data）、以及刚刚走过的足迹（Trace）。 |

---

## 2. 整体架构 (Architecture Layers)

| 层面 | 核心组件 | 功能描述 |
| :--- | :--- | :--- |
| **Agent 交互层** | **API / CLI** | **Semantic Guide (语义引导向导)**。Agent 通过它不仅传达意图，还能接收环境诊断信息。CLI 需具备**引导性 (Guidance)**，在失败时提供具体修复步骤（如“请安装 playwright”或“将脚本保存至 X 路径”）。 |
| **路书管理层** | **Library** | **Base Camp (大本营)**。存储所有的探险手记。负责索引、版本管理，并能根据探险家发回的新路径修正旧的手记（自进化）。 |
| **执行引擎层** | **Guide (agent-browser)** | **Sherpa (向导)**。连接路书与浏览器。**本项目将集成 `agent-browser` 作为底层的 Driver**。它负责将抽象步骤转化为具体的浏览器操作，处理底层脏活（如 CDP 连接、DOM 树精简、元素 Ref 映射）。 |
| **状态/记忆层** | **Context Memory** | **Backpack (背包)**。持久化存储。记录 Session 状态、DOM 快照和变量池，支持热启动与回溯。 |

### 2.1 底层执行引擎集成方案 (Client-Daemon 嵌套)

为了实现稳定、高效的浏览器控制，本系统在“执行引擎层”引入 `agent-browser`。架构上采用 **Client-Daemon 嵌套模式**：

```text
[ Agent (探险家) ] 
       │ (自然语言 / 意图)
       ▼
[ Roadbook CLI (对讲机/大本营) ]  <-- 本项目核心，负责解析路书、状态机、上下文记忆
       │ (生成具体的原子指令，如 click @e1)
       ▼
[ agent-browser CLI (夏尔巴向导) ] <-- 通过 Subprocess 调用，带上 --json 参数
       │ (IPC 通信)
       ▼
[ agent-browser Daemon ] <-- 维持浏览器 Session、处理 Refs 映射、执行动作
       │ (CDP 协议)
       ▼
[ Chrome / 目标网站 ]
```

**集成优势：**
1. **进程解耦与热启动**：`agent-browser` 的 Daemon 机制使浏览器常驻。
2. **免密与状态持久化**：利用其 `--profile` 或 `--session-name` 功能，底层自动复用登录状态。
3. **多模态无缝接入**：支持 `--annotate` 截图，直接返回带数字编号的 UI 截图。
4. **极简的元素定位 (Refs)**：通过 `@e1`, `@e2` 替代复杂的 CSS 选择器。

---

## 3. 核心交互流程 (Interaction Flow)

### 3.1 流程图 (Flowchart)

```mermaid
graph TD
    Start[Agent 意图: 访问网站/执行任务] --> Search(CLI: roadbook search)
    
    Search -- "未找到 (Miss)" --> BranchNoBook[分支 A: 无路书]
    Search -- "找到 (Hit)" --> BranchHasBook[分支 B: 有路书]
    
    %% 分支 A: 无路书
    BranchNoBook --> ReturnMiss[返回: 404 Not Found]
    ReturnMiss --> AgentDecide1{Agent 决策}
    AgentDecide1 -- "探索模式 (Explore)" --> RecordStart(CLI: roadbook record)
    RecordStart --> AgentBrowse[Agent 自由浏览/操作]
    AgentBrowse --> RecordSave(CLI: roadbook save)
    AgentDecide1 -- "仅浏览 (Browse)" --> JustBrowse[普通浏览器操作]
    
    %% 分支 B: 有路书
    BranchHasBook --> CheckScript{检查是否有可用脚本?}
    
    %% 子分支 B1: 有脚本 (Fast Path)
    CheckScript -- "Yes (Script Available)" --> RunScript(CLI: roadbook run --mode script)
    RunScript --> ScriptResult{执行结果?}
    ScriptResult -- "成功" --> ReturnSuccess[返回: 结果数据 + 轨迹]
    ScriptResult -- "失败 (Exception)" --> AutoFallback{策略: 自动回退?}
    
    %% 子分支 B2: 无脚本/脚本失败 (Slow Path)
    CheckScript -- "No" --> SemanticMode
    AutoFallback -- "Yes" --> SemanticMode
    AutoFallback -- "No" --> ReturnError[返回: 报错信息]
    
    subgraph SemanticMode [语义执行模式 (Semantic Mode)]
        LoadBook[加载路书 Markdown] --> ParseIntent[Agent 解析意图与步骤]
        ParseIntent --> VisualLocate[Agent 视觉/DOM 定位]
        VisualLocate --> AgentAction[Agent 执行动作]
        AgentAction --> VerifyState{验证状态}
        VerifyState -- "通过" --> NextStep[下一步]
        VerifyState -- "失败" --> HumanHelp[请求人工介入]
        NextStep --> LoopEnd{结束?}
        LoopEnd -- "Yes" --> GenScript[CLI: 编译新脚本 (Cache)]
    end
    
    GenScript --> ReturnSuccess
```

### 3.2 关键场景

*   **场景一：无路书 (Cold Start)**
    *   Agent 搜索无果 -> 启动探索模式 -> 记录操作 -> 保存为新路书。
*   **场景二：有路书，无脚本 (First Run / Update)**
    *   Agent 读取路书本体 -> 视觉语义定位 -> 执行操作 -> 生成缓存脚本。
*   **场景三：有路书，有脚本 (Fast Path)**
    *   直接运行缓存脚本 -> 毫秒级响应，零 Token 消耗。

### 3.3 执行策略：双通道机制 (Dual Channel)

为了平衡**执行效率**与**泛化能力**，系统采用“脚本优先，语义回退”策略。

1.  **Fast Path (脚本通道)**: 
    *   **机制**: 运行预编译的 Python/Node.js 脚本。
    *   **特点**: 极快，零 Token，适合稳定页面。
    *   **触发**: 默认优先。
2.  **Slow Path (语义通道)**:
    *   **机制**: Agent 实时阅读路书并进行视觉推理。
    *   **特点**: 较慢，消耗 Token，但能处理页面改版。
    *   **触发**: 脚本报错 (`ElementNotFound`) 或无脚本时自动接管。

---

## 4. 架构原则与边界 (Principles & Boundaries)

1.  **协议边界**：**AARP (Protocol)** 只描述任务语义、场景拆分、动作建议，**绝不承载运行态数据**（如上次运行结果、脚本路径）。
2.  **运行时边界**：脚本产物、执行日志、最近运行状态采用**完全内聚**模式，统一放在路书包内部 (`~/.roadbook/books/<book_dir>/runtime/`)。
3.  **执行边界**：Agent 主导执行，CLI 提供管理与辅助能力。弱化 Guide 中心化调度，不以 `debug/step` 为主交互模型。
4.  **CLI 边界**：CLI 聚焦“路书库管理 + 运行时可观测 + 同步服务端”。详细命令请参考 `CLI_Reference.md`。
5.  **服务端边界**：服务端闭源，仅提供上传、查询、版本分发等接口能力，不承担浏览器执行。

---

## 5. 运行时目录结构 (Runtime Directory)

CLI 将所有运行时数据与状态管理在 `~/.roadbook/` 目录下，实现与项目源码的解耦。详细数据模型请参考 `Data_Model.md`。

```text
~/.roadbook/
├── .core/                  # 系统文件 (System files)
│   └── config.yaml         # CLI 用户配置
└── rb-amazon-v1/           # 路书包 (直接位于根目录)
    ├── roadbook.md         # [Source] 路书本体
    ├── assets/             # [Source] 图片资源
    ├── scripts/            # [Script] 可执行脚本
    └── runtime/            # [Runtime] 运行时数据
        └── runs/           # 运行记录 (进化素材)
```

这种结构强调了路书的**自进化特性**：`runtime` 中的数据不仅是执行结果，更是 Agent 优化 `roadbook.md` 的重要素材。
