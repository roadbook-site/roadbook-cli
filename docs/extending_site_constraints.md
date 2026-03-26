# 动态扩展网站约束 (Extending Site Constraints) Implementation

AARP v4.0 的 `Constraints` 机制是完全数据驱动和解耦的。如果需要支持新的爬虫约束或环境特征（例如 `auto_solve_captcha`），可以通过以下步骤动态透传到底层。

## 1. 执行端（SDK 层）对接
在 `src/roadbook/sdk/context.py` 的初始化逻辑中，直接从透传下来的 `self.site_overrides` 字典中获取新参数并应用到 Playwright 实例即可。

```python
# 示例：获取并应用新的验证码约束
self.auto_solve_captcha = self.site_overrides.get("auto_solve_captcha", False)
```

## 2. 声明端（模板层）补充
为了让新创建的路书显式展示出支持这个新约束，将其添加到默认的生成模板中。
修改 `src/roadbook/core/templates/roadbook.md.tpl`：

```markdown
**Constraints**:
- `force_headful`: false
- `stealth_mode`: false
- `viewport`: 1280x720
- `global_delay`: 0
- `auto_solve_captcha`: false  <-- 新增字段
```

得益于解析器的动态正则处理和 UI 的 `TextListEditor` 组件，新的键值对会自动在前端被渲染为可编辑字典，并在保存时原样传递给 Agent 和执行脚本。
