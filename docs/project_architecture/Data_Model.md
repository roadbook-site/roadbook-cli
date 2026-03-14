# Roadbook Runtime Model Specification v1.0

## 1. 概述
本文档定义了 Roadbook 在本地运行时（Local Runtime）的文件系统结构、数据存储格式及关键文件的 Schema。所有运行时数据均存储在用户主目录下的 `~/.roadbook` (Linux/macOS) 或 `%USERPROFILE%\.roadbook` (Windows) 中。

## 2. 目录结构 (Directory Structure)

采用**完全内聚 (Fully Cohesive)** 的设计模式。每个路书包（Roadbook Package）都是一个独立的、自包含的工作区，既包含静态协议，也包含动态运行时数据。

```text
~/.roadbook/
├── config.yaml                 # 用户全局配置
├── books/                      # 本地路书库 (Local Registry)
│   ├── index.json              # 路书索引文件
│   └── <book_dir>/             # 路书包目录 (自包含工作区，目录名不强制等于 roadbook_id)
│       ├── roadbook.md         # [Source] 路书协议文件
│       ├── README.md           # [Source] 说明文档
│       ├── assets/             # [Source] 图片/附件资源
│       ├── scripts/            # 编译后的脚本缓存 (可执行)
│       │   ├── <hash>.py
│       │   └── <hash>.js
│       └── runtime/            # [Runtime] 运行时数据 (动态素材与产物)
│           └── runs/           # 运行历史 (进化素材)
│               ├── last.json   # 最近一次运行结果
│               └── <run_id>/   # 单次运行完整记录
│                   ├── trace.json
│                   └── screenshots/
```

这种结构使得 `books/<book_dir>/` 成为一个完整的“进化单元”。Agent 可以直接读取 `runtime/runs/` 中的历史数据来优化 `roadbook.md`，而无需跨目录寻找素材。

## 3. 关键文件 Schema

### 3.1 本地路书索引 (`books/index.json`)
维护本地已安装路书的元数据列表，用于快速 `list` 和 `search`。

```json
{
  "updated_at": "2023-10-27T10:00:00Z",
  "books": {
    "rb-amazon-v1": {
      "name": "Amazon Checkout",
      "version": "1.0.2",
      "description": "Amazon 购物下单流程",
      "local_path": "books/rb-amazon-v1",
      "installed_at": "2023-10-01T12:00:00Z",
      "source": "remote-registry",
      "tags": ["shopping", "e-commerce"]
    },
    "rb-github-login": {
      "name": "GitHub Login",
      "version": "0.9.0",
      "description": "GitHub 自动登录",
      "local_path": "books/rb-github-login",
      "installed_at": "2023-10-02T14:30:00Z",
      "source": "local-dev"
    }
  }
}
```

### 3.2 运行结果记录 (`books/<book_dir>/runtime/runs/<run_id>/trace.json`)
记录一次执行的完整生命周期。

```json
{
  "run_id": "run_20231027_100123_a1b2",
  "roadbook_id": "rb-amazon-v1",
  "status": "completed",  // pending | running | completed | failed
  "start_time": "2023-10-27T10:01:23Z",
  "end_time": "2023-10-27T10:02:45Z",
  "mode": "auto",         // auto | script | agent
  "inputs": {
    "keyword": "iphone 15"
  },
  "outputs": {
    "order_id": "123-4567890-1234567",
    "total_price": "9999.00"
  },
  "steps": [
    {
      "step_id": "login_01",
      "status": "success",
      "action": "input",
      "target": "#username",
      "value": "***",
      "timestamp": "2023-10-27T10:01:25Z",
      "screenshot": "screenshots/step_01.png"
    },
    {
      "step_id": "search_02",
      "status": "success",
      "action": "click",
      "target": "#search-btn",
      "timestamp": "2023-10-27T10:01:30Z"
    }
  ],
  "error": null // { "code": "ElementNotFound", "message": "...", "stack": "..." }
}
```

### 3.3 脚本缓存命名与头部 (`books/<book_dir>/scripts/`)

*   **命名规范**: `<content_hash>.py`
    *   `content_hash`: 路书文件内容的 SHA256 哈希前 8 位。
    *   **变更说明**: 脚本现在位于路书目录下，因此不再需要在文件名中包含 `roadbook_id`。

*   **脚本头部 (Header)**:
    脚本必须包含自动生成的元数据头部，以便 CLI 识别。

```python
# META_START
# roadbook_id: rb-amazon-v1
# version: 1.0.2
# source_hash: a1b2c3d4
# generated_at: 2023-10-27T10:00:00Z
# generator: roadbook-cli v0.1.0
# META_END

import sys
from playwright.sync_api import sync_playwright

# ... 脚本逻辑 ...
```

## 4. 配置规范 (`config.yaml`)

```yaml
core:
  log_level: "INFO"       # DEBUG | INFO | WARN | ERROR
  headless: false         # 是否默认无头模式
  browser_type: "chromium" # chromium | firefox | webkit

paths:
  home: "~/.roadbook"     # 允许用户自定义根目录

registry:
  url: "https://registry.roadbook.ai"
  token: "sk-..."         # 认证 Token
```
