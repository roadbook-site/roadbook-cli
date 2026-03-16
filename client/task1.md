# Roadbook-CLI 开源发布准备任务 (Task 1)

## 1. 项目命名与结构整理
- [ ] **GitHub 仓库名**：准备将 GitHub 开源仓库命名为 `roadbook-cli`。
- [ ] **PyPI 包名**：保持 `roadbook` 不变（确保 `client/pyproject.toml` 中 `name="roadbook"`）。
- [ ] **Skill 迁移**：将当前的 `.trae/skills/roadbook` 目录移动到代码库的可见目录中（例如根目录的 `skills/roadbook` 或 `agents/roadbook`），作为内置能力一起开源。

## 2. README 双语文档编写
需要提供英文版和中文版，方便国内外开发者了解和使用。
- [ ] 编写主文档 `README.md`（英文）。
- [ ] 编写中文文档 `README_zh-CN.md`。
- [ ] 在两个文档的顶部添加醒目的语言切换链接，格式如下：
  ```markdown
  [English](README.md) | [简体中文](README_zh-CN.md)
  ```
- [ ] **文档核心内容**：需包含项目简介、安装指南（`pip install roadbook`）、快速起步（Quickstart）、核心特性，以及说明“如何为 AI 代理配置 Roadbook 技能”（指向 `skills/roadbook` 目录）。

## 3. 代码清理与脱敏 (高度重要)
- [ ] **敏感信息排查**：全局搜索移除代码、脚本、临时文件中的 API Key、Token、私有 URL 以及数据库密码。
- [ ] **清理冗余文件**：检查 `test/`, `demos/`, `tools/` 和运行目录，删除或 `.gitignore` 掉个人草稿以及庞大的测试生成产物（如 `result.json`、生成的截图或视频等）。
- [ ] **完善 `.gitignore`**：确保 `.env`、`__pycache__` 以及运行时临时目录被正确忽略。

## 4. 依赖检查与开源协议
- [ ] **依赖清理**：梳理 `client/pyproject.toml` 中的 `dependencies`，确保没有把私有开发测试库混入线上依赖。
- [ ] **添加 LICENSE**：在仓库根目录添加开源许可文件 `LICENSE`（如 MIT License）。
