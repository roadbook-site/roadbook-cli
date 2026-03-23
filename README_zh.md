# Roadbook CLI

[English](README.md) | [简体中文](README_zh.md)

欢迎使用 **Roadbook**，这是为您 AI Agent 打造的浏览器自动化“野外探险向导”。

标准的网页自动化通常依赖于固定的脚本，当网站发生变化时，这些脚本很容易失效——就像在不断变化的地形中使用一张刻板的地图。Roadbook 通过充当 **探险手记 (Expedition Log)** 解决了这个问题。它不仅提供必要的步骤，还提供环境诊断和灵活的操作指引。

当您的 AI Agent（探险家）迷路或脚本执行失败时，Roadbook（系统/夏尔巴向导）会提供上下文和语义提示，帮助它自主寻找新路径、修复脚本并完成任务。

## 核心概念
![alt text](images/image-1.png)
- **Roadbook (路书)**: 探险手记。它记录了关键地标（UI 特征）、必经之路和可执行建议，以便动态地导航网页界面。
- **Agent (探险家)**: 探索者。阅读路书、做出决策，并在标准脚本失败时进行视觉/语义推理的 AI 智能体。
- **Guide/CLI (夏尔巴向导/装备)**: 处理繁重工作（驱动浏览器、上下文管理）并提供语义引导的 CLI 与运行系统。

## 安装

### 通过 pip 安装（推荐）

待 Roadbook 发布到 PyPI 后，您可以直接通过 pip 安装 CLI：

```bash
pip install roadbook
```

### 从源码安装

要从源码安装最新版本，请克隆仓库并以可编辑模式安装：

```bash
git clone <repository_url>
cd roadbook-cli
pip install -e .
```

## 快速入门与示例

Roadbook 的设计包含两个主要阶段：**探索 Exploring**（创建路书）和 **执行 Executing**（运行任务）。

### 1. 创建新路书（探索阶段）

通过 CLI 初始化一个新的路书。这将设置必要的工作区和脚手架，允许 Agent 探索网站并测试交互。

```bash
# 初始化一个关于在亚马逊搜索产品的新路书
roadbook init my-first-task --description "Search for a product on Amazon" --entry-url "https://www.amazon.com"
```

这将在您的项目中创建一个新目录，包含标准的 `roadbook.md` 模板和用于开始探索的入门测试脚本。

### 2. 执行路书（执行阶段）

您可以自动运行路书（如果存在稳定的脚本），或在交互式向导模式下运行（Agent 将获得语义指令来探索环境）。

```bash
# 列出本地可用的路书
roadbook list

# 选项 1：通过 Fast Path 运行（自动脚本执行）
# 这将尝试使用预编译的自动化脚本进行快速执行。
roadbook run my-first-task

# 选项 2：通过交互式向导模式运行（语义探索）
# 当网站发生变化或没有可用脚本时使用此模式。它会显示完整的 Markdown 路书，指导 Agent 完成步骤。
roadbook run --guide my-first-task
```

### 3. 管理路书

CLI 提供了工具来组织和查看执行日志。

```bash
# 查看单个路书的详细信息
roadbook inspect my-first-task

# 将本地路书链接到全局库，以便在您的机器上共享
roadbook link

# 查看特定路书的执行日志和历史记录
roadbook logs list my-first-task
```