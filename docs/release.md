# Roadbook CLI 发布指南

本文档记录了 Roadbook CLI 项目发布到 PyPI 的自动化流程及相关配置。本项目已配置 GitHub Actions 实现全自动发布，不再需要手动在本地执行打包和上传命令。

## 🚀 自动发布流程 (推荐)

我们使用 **Git Tag** 来触发自动发布工作流。只有当代码被打上符合 `v*.*.*` 格式（如 `v0.1.3`）的标签并推送到 GitHub 时，才会触发发布。

### 发布步骤

1. **更新版本号**
   在项目根目录的 `pyproject.toml` 文件中，修改 `version` 字段：
   ```toml
   # pyproject.toml
   version = "0.1.3"
   ```
   *(注：`src/roadbook/__init__.py` 会在运行时自动读取这个版本号，无需手动修改)*

2. **运行发布脚本（自动同步版本）**
   执行本地发布脚本，它会自动：
   - 更新 `pyproject.toml` 中的版本号
   - 同时更新所有 Skill 文件 (SKILL.md) 中的 `version` 字段
   ```bash
   # Windows
   .\scripts\publish.bat
   
   # Linux/macOS
   python scripts/publish.py
   ```
   *按照脚本提示输入新版本号（例如 `0.1.3`），脚本会自动更新所有文件。*

3. **提交代码**
   审查脚本所做的更改，确认无误后提交：
   ```bash
   git add pyproject.toml skills/*/SKILL.md
   git commit -m "chore: bump version to 0.1.3"
   git push origin main
   ```
   *此时会触发 `test.yml` 运行自动化测试，请确保测试通过。*

4. **打标签并触发发布**
   确认代码无误后，打上对应的版本标签并推送到远端：
   ```bash
   git tag v0.1.3
   git push origin v0.1.3
   ```

5. **等待执行**
   前往 GitHub 仓库的 **Actions** 页面，你会看到名为 `Publish to PyPI` 的工作流正在运行。完成后，新版本即在 PyPI 上线。

---

## 📦 技能版本管理

Roadbook CLI 提供两项技能（Skills），它们与 Python 发行包版本保持同步：

### Skill 文件
- `skills/roadbook-executor/SKILL.md` - 执行 Roadbook
- `skills/roadbook-explorer/SKILL.md` - 创建 Roadbook

### 版本同步机制

每当运行发布脚本时，所有 Skill 文件中的以下字段会自动更新：
- `version`: 与 `pyproject.toml` 中的版本号保持一致

实现位置：`scripts/publish.py` 中的 `update_skill_versions()` 会在发布时自动回填每个 `SKILL.md` 的 `version` 字段。

### 用户端版本检查

Skill 文件的 Requirements 部分包含版本检查说明。用户可以通过以下命令验证兼容性：

```bash
# 检查已安装的 Roadbook 包版本
roadbook --version
```

然后直接查看对应 `SKILL.md` 头部的 `version` 字段，确保两者一致。

**版本不匹配时的处理：**
- 如果 Python 包版本 **低于** Skill 要求的版本 → 升级 Python 包
  ```bash
  pip install --upgrade roadbook
  ```
- 如果 Python 包版本 **高于** Skill 提供的版本 → 更新 Skill
  ```bash
  npx skills update
  ```

---

## ⚙️ 系统配置备忘

如果你需要将此项目迁移到新的 GitHub 仓库，或者重新配置 PyPI 权限，请参考以下设置：

### 1. PyPI API Token 申请
1. 登录 [PyPI 账号设置](https://pypi.org/manage/account/)。
2. 找到 **API tokens** 区域，点击 **Add API token**。
3. **Token name**: 建议命名为 `github-actions-roadbook`。
4. **Scope**: 必须选择具体的项目 `roadbook`（以限制该 Token 只能操作此项目，提高安全性）。
5. 复制生成的以 `pypi-` 开头的长字符串。

### 2. GitHub Secrets 配置
1. 进入 GitHub 仓库页面。
2. 点击 **Settings** -> **Secrets and variables** -> **Actions**。
3. 点击 **New repository secret**。
4. **Name** 填入：`PYPI_API_TOKEN`
5. **Secret** 填入：刚刚在 PyPI 复制的 Token。

*这些配置已被硬编码在 `.github/workflows/publish.yml` 中。*

---

## 🛠️ 本地手动发布 (备用方案)

如果 GitHub Actions 出现故障，或者你需要在本地强行发布，可以使用以下备用方法：

1. 确保已安装打包工具：
   ```bash
   pip install --upgrade build twine
   ```
2. 运行交互式发布脚本：
   ```bash
   # 在 Windows 环境下
   .\scripts\publish.bat
   ```
   *该脚本会提示你确认版本号、自动清理旧的 `dist/` 目录、同时更新 `pyproject.toml` 和 `SKILL.md` 文件、构建 `wheel` 和 `tar.gz` 包，并调用 `twine` 上传到 PyPI。*
