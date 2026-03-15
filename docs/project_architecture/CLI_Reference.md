# Roadbook CLI Command Specification

本文档定义了 Roadbook CLI 的详细命令规范、参数说明及示例输出。
CLI 旨在提供“路书库管理”与“运行时可观测性”，核心执行逻辑由 `run` 命令承担。

## 1. 通用规范

*   **命令结构**: `roadbook <command> [subcommand] [options] [arguments]`
*   **设计原则**: **Guidance First (引导优先)**。
    *   当用户输入错误命令时，提供近似命令建议。
    *   当执行失败时，提供具体的**Actionable Next Steps (下一步行动建议)**，例如安装缺失依赖、创建缺失文件等。
*   **帮助信息**: 所有命令支持 `--help` / `-h`。
*   **输出格式**: 默认人类可读文本 (Human Readable)，支持 `--json` 输出结构化数据。
*   **全局参数**:
    *   `--verbose, -v`: 显示详细日志。
    *   `--json`: 以 JSON 格式输出结果。
*   **路径约定**: CLI 参数中的 `<id>` 是路书元数据 ID；实际文件路径以路书所在目录 (`<book_dir>`) 为准，不强制要求目录名与 ID 相同。

---

## 2. 路书库管理 (Library Management)

负责本地路书的增删改查与远程同步。

### 2.1 列出路书 (`list`)

列出已安装的路书。支持从以下位置加载：
1.  **当前工作区 (Workspace)**: `./.roadbook/books/` (优先)
2.  **全局库 (Global)**: `~/.roadbook/books/`

*   **Usage**: `roadbook list [options]`
*   **Options**:
    *   `--filter <tag>`: 按标签过滤。
*   **Example Output**:

```text
ID                  NAME                VERSION   STATUS
rb-amazon-v1        Amazon Checkout     4.0       Installed
rb-google-search    Google Search       1.2       Installed
rb-login-template   Universal Login     1.0       Draft
```

### 2.2 查看详情 (`show`)

显示路书的元数据、描述及状态。

*   **Usage**: `roadbook show <id>`
*   **Example Output**:

```text
[Roadbook: rb-amazon-v1]
Name:        Amazon Checkout
Version:     4.0
Description: 在亚马逊上搜索商品并完成下单流程
Path:        ~/.roadbook/books/rb-amazon-v1/roadbook.md
Inputs:
  - keyword: 搜索关键词
  - max_price: 最高价格限制
Tags:        shopping, e-commerce
Runtime:
  Scripts:   Available (Python)
  Last Run:  Success (10 mins ago)
```

### 2.3 搜索路书 (`search`)

(Mock) 在远程仓库或本地缓存中搜索路书。

*   **Usage**: `roadbook search <keyword>`
*   **Example Output**:

```text
Searching for "shop"...

ID                  NAME                DESCRIPTION
rb-amazon-v1        Amazon Checkout     Search and buy on Amazon
rb-shopify-test     Shopify Tester      Test checkout flow on Shopify
```

### 2.4 编辑路书 (`edit`)

使用系统默认编辑器打开指定的路书文件。

*   **Usage**: `roadbook edit <id>`
*   **Behavior**: 打开 `~/.roadbook/books/<book_dir>/roadbook.md`（其中 `<book_dir>` 由 `<id>` 解析得到）。

### 2.5 删除路书 (`delete`)

删除本地路书及其运行时数据。

*   **Usage**: `roadbook delete <id>`
*   **Aliases**: `rm`, `remove`
*   **Example Output**:

```text
Are you sure you want to delete "rb-amazon-v1"? [y/N] y
Deleted roadbook: rb-amazon-v1
```

---

## 3. 核心导航与执行 (Navigate & Execute)

执行路书的核心命令组，支持语义引导与自动化执行。

### 3.1 启动语义引导会话 (`open`)

**推荐的主入口**。打开指定路书，进入语义指引模式 (Semantic Guide Mode)。系统会初始化运行环境、生成会话 ID，并**一次性展示完整的路书内容**。

*   **Auto-Scaffolding (自动脚手架)**: 如果未检测到关联脚本，系统会自动在当前工作区的 `.roadbook/<id>/scripts/script.py` 生成一个基础脚本模板，方便用户直接开始编写自动化逻辑。

*   **Usage**: `roadbook open <id> [options]`
*   **Options**: 
    *   `--inputs <json>`: 传递给路书的输入参数 (JSON 字符串)。
    *   `--inputs-file <path>`: 从 JSON 文件读取输入参数（推荐复杂参数使用）。
*   **Example Output**:

```text
[Setup] Initializing roadbook workspace: ./.roadbook/test-book
[Scaffold] Created workspace script: ./.roadbook/test-book/scripts/script.py
[Action] Outputs will be saved to: ./.roadbook/test-book/output_<timestamp>
== Roadbook Session Started ==
ID: test-book
Session: run_20260313_160820_xxxx
[Mode] Semantic Guide Mode is active.

==================== ROADBOOK CONTENT ====================

--- Sheet 1/2: Open Website ---
Goal: Navigate to https://example.com
...

--- Sheet 2/2: Search ---
Goal: Type "hello" into search box
...

==========================================================

[Agent Action] The entire roadbook has been provided above.
[Agent Action] Please read through all sheets and execute the task step by step using your browser tools.
```

### 3.2 自动运行 (`run`)

尝试自动化执行路书。
*   **脚本查找优先级**:
    1.  当前工作区: `./scripts/script.py` (推荐)
    2.  当前工作区: `./<id>.py`
    3.  路书目录: `<book_dir>/scripts/script.py`
*   如果存在脚本：直接执行。
*   如果不存在脚本：提示用户，并自动降级为语义指引模式 (`open`)，触发自动脚手架生成。

**Guidance Behavior (引导行为)**:
*   **Environment Check**: 在运行前检查环境（如 Python 版本、依赖包）。如果缺失，CLI **必须**明确告知用户如何安装。
    *   *Example*: `[!] Missing dependency 'pandas'. Run 'pip install pandas' to fix.`
*   **Script Location**: 系统会自动在工作区生成脚本模板，并提示用户编辑。
    *   *Example*: `[Scaffold] Created workspace script: .roadbook/test-book/scripts/script.py`

*   **Usage**: `roadbook run <id> [options]`
*   **Options**:
    *   `--inputs <json>`: 输入参数。
    *   `--inputs-file <path>`: 从 JSON 文件读取输入参数。
    *   `--mode <auto|script|agent>`:
        *   `auto` (Default): 优先尝试脚本，失败后回退到 Agent 语义探索。
        *   `script`: 强制仅运行脚本。
        *   `agent`: 强制使用 Agent 语义探索（通常用于首次生成或修复）。

*   **Example Output (Script Found)**:

```text
[Mode] Script execution mode.
[*] Found script: .../scripts/script.py
[*] Executing script...
[Success] Script executed successfully.
[Runtime] Run ID: run_20260313_161000_xxxx
[Action] Use 'roadbook logs inspect <run_id>' to inspect this run.
```

*   **Example Output (No Script)**:

```text
[!] No automation script found for 'test-book'.
[*] 正在切换到语义引导模式，协助您构建脚本...
== Roadbook Session Started ==
[Mode] Semantic Guide Mode is active.
... (Full Roadbook Content) ...
```

---

## 4. 运行时可观测 (Observe / Logs)

管理和查看路书的运行记录（日志）。

### 4.1 列出运行记录 (`logs list`)

查看指定路书的所有运行历史。

*   **Usage**: `roadbook logs list <id>`
*   **Example Output**:

```text
Run History for test-book:
┏━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Run ID                 ┃ Status  ┃ Time                ┃ Details             ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ run_20260313_160820_…  │ running │ 2026-03-13 16:08:20 │ {'current_step': 0} │
│ run_20260312_100000_…  │ success │ 2026-03-12 10:00:00 │ {'steps': 5}        │
└────────────────────────┴─────────┴─────────────────────┴─────────────────────┘
```

### 4.2 查看详细日志 (`logs inspect`)

查看某次特定运行的详细信息（输入、输出、错误堆栈）。

*   **Usage**: `roadbook logs inspect <run_id>`
*   **Behavior**: 打开运行记录所在的文件夹（包含 logs, screenshots 等）。

### 4.3 查看最近一次日志 (`logs last`)

快速查看最近一次运行的详情。

*   **Usage**: `roadbook logs last`
*   **Example Output**:

```text
Run ID:      run_20231027_1024
Roadbook:    rb-amazon-v1
Status:      Success
Duration:    45s
Mode:        Agent Fallback
Timestamp:   2023-10-27 10:24:30
Log Path:    ~/.roadbook/books/rb-amazon-v1/runtime/runs/run_20231027_1024/
```

---

## 5. 脚本开发 (Develop / Script)

管理本地自动化脚本。

### 5.1 列出脚本 (`script ls`)

查看路书关联的本地脚本文件。

*   **Usage**: `roadbook script ls <id>`
*   **Example Output**:

```text
Roadbook: rb-amazon-v1

Script ID       Lang    Created             Status
s_py_v1_hash    Python  2023-10-25 10:00    Active
s_js_v1_hash    NodeJS  2023-10-20 09:00    Outdated
```

### 5.2 清理脚本 (`script clean`)

清理过期的脚本缓存。

*   **Usage**: `roadbook script clean <id>`
