# Roadbook CLI `open` Command Logic Improvement Proposal

Current logic in `executor.py` simply checks if a script exists. If not, it generates a scaffold. This lacks context for the Agent.

## Proposed States and Logic

We propose distinguishing 4 states for script status in `start_session` to provide better context to the Agent:

### 1. No Script (未生成)
- **Condition**: `RuntimeManager.find_script(...)` returns `None`.
- **Action**: Generate scaffold (current behavior).
- **Message**: "Script scaffold generated. Please implement automation logic."
- **Agent Hint**: "已为您生成了脚本脚手架 `scripts/script.py`。当前处于语义引导模式，请阅读路书内容，并开始编写自动化逻辑。"

### 2. Scaffold Only (仅脚手架)
- **Condition**: Script file exists.
- **Detection**: 
  - Contains specific marker string (e.g., `# TODO: Implement your automation logic here`).
  - OR file content matches the template hash/size closely.
- **Message**: "Script exists but appears to be unmodified scaffold."
- **Agent Hint**: "检测到脚本 `scripts/script.py` 存在，但似乎仍为初始脚手架状态（未检测到有效逻辑实现）。请基于此文件开始编写代码。"

### 3. In Progress (开发中)
- **Condition**: Script exists and is modified (marker removed or significant content change).
- **Detection**: `RuntimeManager.get_last_run(rb_id)` returns `None` OR status is not "success".
- **Message**: "Script exists with modifications but no successful run history found."
- **Agent Hint**: "检测到脚本 `scripts/script.py` 已有修改，但尚未发现成功的运行记录。请继续完善代码或进行调试验证。"

### 4. Verified (已验证)
- **Condition**: Script exists and has successful run history.
- **Detection**: `RuntimeManager.get_last_run(rb_id)` returns a run with `status == "success"`.
- **Message**: "Script exists and has been successfully verified."
- **Agent Hint**: "检测到该脚本 `scripts/script.py` 已有历史成功运行记录。您可以：1. 直接运行脚本：使用 `roadbook run <id>`。 2. 继续修改：在当前模式下编辑并调试代码。"

## Implementation Details
- Modify `start_session` in `src/roadbook/commands/executor.py`.
- Add helper methods/logic to detect "Scaffold" state (check for TODO string).
- Leverage `RuntimeManager.get_last_run` for verification status.
