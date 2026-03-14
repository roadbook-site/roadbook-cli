# Roadbook MVP (Minimum Viable Product)

本项目旨在验证“基于语义路标和 CDP 控制的非刚性自动化”是否可行。

## 📂 项目结构

```text
roadbook/
├── docs/                   # 设计文档与技能沉淀
│   ├── MVP_Design.md       # 核心架构与设计思考
│   ├── Test_Plan.md        # 测试靶场与实操路线图
│   └── Skill_Simulator.md  # 路书模拟器技能 (Agent Skill)
├── library/                # 路书仓库 (YAML Files)
│   └── quotes_login.yaml   # Hello World 示例
├── src/                    # 源代码
│   └── guide.py            # 核心执行引擎 (The Guide/Sherpa)
└── tests/                  # 测试用例与日志
```

## 🚀 快速开始

1. **环境准备**:
   - 确保安装 `agent-browser` CLI。
   - 启动 Chrome 调试模式: `chrome.exe --remote-debugging-port=9224`

2. **运行路书**:
   - 模拟执行: 使用 `docs/Skill_Simulator.md` 中的 Prompt 让 AI 模拟执行。
   - 真实执行: `python src/guide.py run library/quotes_login.yaml`

## 🎯 核心目标

验证以下假设：
1. **语义路标有效性**: 无需 XPath/CSS，仅凭 `landmark` (role/keyword) 定位元素。
2. **非刚性容错**: 页面结构变化时，路书依然健壮。
3. **人机协同**: 遇到无法处理的情况，能够优雅挂起 (`wait_for_human`) 并恢复。
