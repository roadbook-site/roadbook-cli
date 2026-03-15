# RFC: Roadbook CLI 运维与可观测性增强 (Operations & Observability Enhancement)

## 1. 背景与现状 (Context)

通过对目前 Roadbook CLI 代码库的分析，我们发现当前版本在**长期运行维护**和**故障排查效率**方面存在明显短板。主要表现为：
1.  **资源泄露**：缺乏全局清理机制，运行日志（`runs/`）无限堆积。
2.  **调试中断**：`logs inspect` 依赖操作系统文件管理器，无法在纯终端（SSH/Headless）环境下闭环调试。
3.  **策略缺失**：缺乏基于时间或数量的自动化数据保留（Retention）配置。

本提案旨在通过工程化的设计，系统性地解决上述问题。

---

## 2. 资源生命周期管理 (Resource Lifecycle Management)

替代原有的“工作区清理”概念，引入更精细的 `prune`（修剪）命令。

### 2.1 现有问题
*   `roadbook script clean` 仅清理脚本文件，无法处理日志和临时文件。
*   缺乏按时间、状态筛选的清理能力。

### 2.2 设计方案
新增 `roadbook prune` 命令，支持多维度清理策略。

**命令规范：**
```bash
# 清理指定 Roadbook 下超过 7 天的运行记录
roadbook prune runs <id> --before 7d

# 仅清理失败的运行记录（保留成功记录用于回溯）
roadbook prune runs <id> --status failed

# 清理所有 Roadbook 的临时缓存文件
roadbook prune cache --all

# 模拟执行（不实际删除，仅列出将要删除的文件）
roadbook prune runs <id> --before 30d --dry-run
```

**安全机制：**
*   默认开启 **交互式确认 (Interactive Confirmation)**，除非显式传递 `--force` 参数。
*   建议保留最近 N 次运行记录（即使满足过期时间），防止清空刚跑完的数据。

---

## 3. 可观测性与调试 (Observability & Debugging)

替代原有的“运行结果诊断”，强调**终端内闭环 (Terminal-First)** 的调试体验。

### 3.1 现有问题
*   `logs inspect` 强行打开 GUI 文件夹，切断了心流。
*   缺乏直接查看错误堆栈、运行日志的 CLI 命令。

### 3.2 设计方案
增强 `logs` 子命令，支持流式输出和错误提取。

**命令规范：**
```bash
# [新增] 在终端直接输出指定运行记录的完整日志
roadbook logs cat <run_id>

# [新增] 结构化展示运行详情（包括错误堆栈），而非仅显示元数据
# 自动解析 run_meta.json 中的 error 字段并高亮显示
roadbook logs show <run_id> --error

# [增强] 实时查看当前正在运行的日志（类似 tail -f）
roadbook logs tail <id>
```

**输出格式建议：**
*   使用 ANSI Color 高亮 Error/Warning 信息。
*   对于长日志，默认使用 `less` 分页（可配置）。

---

## 4. 数据保留策略 (Data Retention Policy)

规范化 `config.yaml` 配置，引入自动化维护策略。

### 4.1 现有问题
*   配置项仅包含 Server/Token/Scaffold，缺乏运维配置。
*   全量扫描清理的性能开销未被考虑。

### 4.2 设计方案
在 `config.yaml` 中新增 `history` 配置段。

**配置示例：**
```yaml
history:
  # 自动清理策略
  retention:
    max_days: 30        # 保留最近 30 天的数据
    max_runs: 1000      # 每个 Roadbook 最多保留 1000 条记录
    clean_strategy: "lazy" # lazy (运行时概率触发) | startup (启动时检查) | manual (仅手动)
```

**性能优化 - 惰性清理 (Lazy Cleanup)：**
*   避免在每次 `roadbook run` 时进行全量文件系统扫描。
*   **策略**：
    *   **概率触发**：每次运行有 1/10 概率触发后台清理线程。
    *   **异步执行**：清理操作不应阻塞主进程的启动。

---

## 5. 实施路线图 (Implementation Roadmap)

建议按以下优先级分阶段实施：

### Phase 1: 核心可观测性 (High Priority)
*   [ ] 实现 `roadbook logs cat <run_id>`：支持终端查看日志。
*   [ ] 实现 `roadbook logs show <run_id> --error`：支持错误堆栈解析与展示。

### Phase 2: 手动运维能力 (Medium Priority)
*   [ ] 实现 `roadbook prune runs` 命令基础逻辑。
*   [ ] 支持 `--before` (时间) 和 `--status` (状态) 过滤器。

### Phase 3: 自动化与配置 (Low Priority)
*   [ ] 更新 `config.yaml` Schema，解析 `history` 字段。
*   [ ] 实现惰性清理 (Lazy Cleanup) 钩子。
