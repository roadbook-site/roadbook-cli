# 异常处理经验库 (Experience Log)

## RPA Challenge 测试发现 (动态表单无 Standard Label 关联)

**场景描述:**
在执行 [RPA Challenge](https://rpachallenge.com) 表单填写路书 (`rpa_challenge.yaml`) 时，需要根据类似于 "First Name", "Last Name" 的 Keyword，动态地寻找每次刷新都位置变化的输入框。

**遇到坑与阻碍:**
- **标准 Role 匹配失效**: 路书中定义 `landmark: {role: textbox, keyword: "First Name"}`。尝试在 Playwright / 自动化脚本中直接使用 `getByRole('textbox', {name: 'First Name'})` 会导致**匹配失败 (Count: 0)**。
- **根本原因**: 该网页是 Angular 构建，DOM 中 `<label>First Name</label>` 并没有通过 `for` 属性绑定 ID 给对应的 `<input>`，也没有将 `<input>` 嵌套在内部。缺少标准属性约束，基于 W3C 标准无障碍树 (Accessibility Tree) 的程序化解析器无法感知两者的对应关系。

**Agent 的优势 (Stage 1 中枢):**
- 在未提供精准 CSS/XPath 的探索期，Agent 通过观察精简后的 DOM 快照（如 `agent-browser snapshot`）中的节点顺序，天然利用了**视觉隐式关联**的推理（“文本节点紧挨着紧随其后的 TextBox”）完成了精准点击与输入，展示了智能断言的兜底能力。

**针对半自动化Runner的演进对策 (Stage 2 优化方案):**
仅仅依赖语义 Role/Keyword 对传统或不规则前端页面存在“失明”风险。为了支持阶段二的自动化，路书 Schema 必须支持**显式的结构探针**作为辅助断言。
- 优化了路书结构，不仅保留提供给 Agent 的 `label / keyword` 字段，同时新增或补充了 `xpath` 锚点：
  ```yaml
  landmark:
    role: textbox
    keyword: "First Name"
    xpath: "//label[normalize-space(text())='First Name']/following-sibling::input"
  ```
此举将“动态模糊的意图”降维成了“结构稳定的强绑定”，以确保后续 Runner 的极速、稳定执行。