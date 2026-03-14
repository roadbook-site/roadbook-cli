# 基于路书（Roadbook）执行自动化任务的复盘与建议

## 任务背景
本次任务旨在基于 `jimeng-video-download-v1` 路书，从即梦 AI 平台自动下载最新的 5 个视频，并保存到本地指定目录（`C:\code_dev\roadbook\test`）。

在执行过程中，经历了从尝试 CLI 一键运行到改为读取路书手动执行的策略转变，期间暴露了部分自动化执行的痛点，也深刻体现了路书系统作为 Agent 导航工具的价值。

---

## 一、 执行过程中遇到的核心问题

### 1. 路书执行器（CLI）的参数解析问题（Shell 环境兼容性）
- **现象**：最初尝试直接通过 `roadbook run --inputs '{"count":5}'` 命令行来自动执行时，在 Windows PowerShell 环境下遭遇了严重的引号剥离（Quote Stripping）和 JSON 解析错误，导致无法直接通过 CLI 传参启动。
- **结果**：迫使放弃了一键运行模式，转而采用读取路书 Markdown 文件，手动解析步骤并结合 MCP 浏览器控制工具进行“交互式/半自动”执行。

### 2. 动态 DOM 与选择器超时问题（前端框架复杂性）
- **现象**：在处理第 2 个及后续视频时，路书中定义的 `WAIT "button:has-text('下载')"` 步骤频繁触发 5000ms 超时错误。
- **原因**：即梦 AI 平台是一个复杂的单页应用（SPA），页面中可能存在多个隐藏的对话框或被遮挡的元素。标准的文本匹配器无法稳定地找到当前激活的“下载”按钮。
- **解决**：转而注入自定义的 JavaScript 脚本，通过遍历所有的 `<button>` 元素，基于 `innerText` 找到目标并直接调用 `.click()` 方法，从而绕过了标准选择器的限制。

### 3. 文件系统权限与状态同步
- **现象**：在使用 PowerShell 的 `Move-Item` 将视频从系统的 `Downloads` 文件夹移动到目标文件夹时，遇到了权限拒绝（Permission Denied）的问题。
- **解决**：调整策略，使用 `Copy-Item` 复制文件，并结合文件的修改时间（`LastWriteTime`）和 `Start-Sleep` 等待下载完成，确保文件完整落盘后再进行操作。

---

## 二、 路书在这个过程中提供的帮助

尽管未能直接一键运行，但路书文件（`roadbook.md`）作为一份**标准作业程序（SOP）**，为手动推进任务提供了不可替代的指导：

1. **清晰的宏观策略与状态机**
   路书明确划分了【初始化】 -> 【视频列表处理】 -> 【详情与下载】的生命周期。无需自行摸索即梦平台的交互逻辑（例如：需要先等网络空闲，再滚动到底部，点击视频卡片进入详情，最后按 `Escape` 退出弹窗）。这极大降低了探索成本。

2. **高价值的 CSS 选择器提示**
   诸如 `div[class*='video-node-wrapper']`、`div[class*='video-wrapper']` 等关键选择器，使得能够迅速定位到 DOM 树中的核心元素。即便后来改用 JS 脚本执行，也是基于这些选择器作为锚点进行二次开发的。

---

## 三、 对路书系统的意见与建议

基于这次“实战”体验，对路书系统（特别是其语法设计和执行器）有以下反馈：

### 🌟 好的地方（优势）
- **极高的可读性与复用性**：Markdown 格式的路书非常直观，不仅机器能读，AI Agent 也能轻松理解其业务意图并将其转化为具体动作。
- **解耦了业务逻辑与执行逻辑**：它将“要在什么网站做什么”与“具体怎么写代码”分离开来，使得自动化任务的沉淀变得非常容易。

### ⚠️ 不足之处与改进建议（针对路书系统）

1. **建议：改进 CLI 的输入传参机制**
   - **痛点**：目前依赖命令行传递 JSON 字符串在跨平台（尤其是 Windows PowerShell）时极易出错。
   - **改进**：建议路书 CLI 增加通过文件传参的支持，例如：`roadbook run --inputs-file config.json`。这样可以彻底规避终端引号转义的深坑。

2. **建议：增强选择器的鲁棒性（Robustness）与 Fallback 机制**
   - **痛点**：`WAIT "button:has-text('下载')"` 这种依赖纯文本或单一 CSS 的指令在现代前端页面中很脆弱。
   - **改进**：
     - 路书语法层面可以引入**重试或降级（Fallback）机制**。例如：如果 `CLICK A` 失败，则尝试 `EVAL_JS "..."` 或尝试 `CLICK B`。
     - 执行器底层可以做得更智能：当找不到可见元素时，自动尝试在 Shadow DOM 或所有节点中搜索，或者使用模糊的视觉/坐标点击。

3. **建议：增加原生的“文件下载”指令支持**
   - **痛点**：当前路书在点击“下载”后，只是触发了浏览器的行为，缺乏对下载结果的闭环追踪。目前必须依靠监控操作系统的 `Downloads` 文件夹来判断任务是否完成。
   - **改进**：建议在路书语法中引入类似 `DOWNLOAD_TO "/path/to/dir"` 的指令。执行器可以通过 CDP（Chrome DevTools Protocol）直接拦截下载流并保存到指定位置，从而实现 100% 可靠的文件落盘，无需再依赖系统的文件监控。

4. **建议：增加执行过程的容错与状态恢复**
   - **痛点**：一旦某个步骤（如等待按钮）失败，整个流程就会卡死。
   - **改进**：支持在路书中定义“清理动作（Cleanup）”。例如，如果详情页操作失败，执行器应该知道按 `Escape` 键或者刷新页面来恢复到安全状态（列表页），然后再处理下一个元素，而不是直接抛出异常中断。

---

## 四、 与 Roadbook CLI 交互的历史记录（实录）

在任务初期，为了了解路书详情和尝试自动执行，我们进行了一系列 CLI 交互。以下是核心命令及其返回值的记录整理，这些记录也印证了上文中提到的“参数解析问题”。

### 1. 检查 Roadbook CLI 是否可用
**命令：**
```powershell
Get-Command roadbook
```
**返回值摘要：**
```
CommandType     Name                                               Version    Source
-----------     ----                                               -------    ------
Application     roadbook.exe                                       0.0.0.0    C:\Users\zds\.conda\envs\py312\Scripts\roadbook.exe
```

### 2. 列出本地可用的路书
**命令：**
```powershell
roadbook list
```
**返回值摘要：**
```
Available Roadbooks:
  ID: jimeng-video-download-v1 (v4.0)
  Name: 即梦视频批量下载
  Description: 自动从即梦AI平台下载生成的视频。
  Path: C:\Users\zds\.roadbook\books\jimeng\download\roadbook.md
```

### 3. 查看目标路书详情
**命令：**
```powershell
roadbook inspect jimeng-video-download-v1
```
**返回值摘要：**
```
Roadbook Details:
  ID: jimeng-video-download-v1
  Name: 即梦视频批量下载
  Version: 4.0
  Author: Trae
  Path: C:\Users\zds\.roadbook\books\jimeng\download\roadbook.md

Input Schema:
  count (integer): 需要下载的视频数量 (Default: 5)
  save_dir (string): 视频保存的本地目录 (Default: ./downloads)
  headless (boolean): 是否使用无头模式 (Default: false)

Prerequisites:
  - 启动带有远程调试端口的 Chrome 浏览器: chrome.exe --remote-debugging-port=9224
  - 用户已登录即梦AI平台

Variables:
  - current_count: 0
  - total_count: {{inputs.count}}
```

### 4. 尝试通过 CLI 运行路书（遭遇传参失败）
**命令尝试 1（标准的 JSON 字符串传参）：**
```powershell
roadbook run jimeng-video-download-v1 --inputs '{"count":5,"save_dir":"C:\\code_dev\\roadbook\\test"}'
```
**返回值：**
```
Error: Failed to parse --inputs argument as JSON.
Detail: Expecting value: line 1 column 1 (char 0)
Invalid JSON for --inputs: {count:5,save_dir:C:\code_dev\roadbook\test}
```
*(注：PowerShell 剥离了单引号和双引号，导致 JSON 格式破坏。)*

**命令尝试 2（尝试 PowerShell 转义）：**
```powershell
roadbook run jimeng-video-download-v1 --inputs '{\"count\":5}'
```
**返回值：**
```
usage: roadbook run [-h] [--inputs INPUTS] [--interactive] [--step-by-step] roadbook_id
roadbook run: error: unrecognized arguments: {"count":5}
```
*(注：转义后虽然 JSON 结构得以保留，但 CLI 解析器将其识别为了未知的独立参数。)*

**命令尝试 3（尝试交互式/单步模式并带参数）：**
```powershell
roadbook run jimeng-video-download-v1 --interactive --inputs "{`"count`":5, `"save_dir`":`"C:\\code_dev\\roadbook\\test`"}"
```
**返回值：**
```
Error: Failed to parse --inputs argument as JSON.
Detail: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)
Invalid JSON for --inputs: {count:5, save_dir:C:\code_dev\roadbook\test}
```

**结论：** 经过多次尝试，发现在当前的 PowerShell 环境下，通过 `--inputs` 传递复杂 JSON 参数非常困难，这也是最终选择读取 Markdown 文件并结合 MCP 工具进行“交互式/半自动”执行的直接原因。

---

**总结**：路书系统是一个非常有潜力的 Agent 导航工具，它完美地解决了“目标网站怎么走”的问题。如果能在**参数传递的工程化**、**DOM 交互的容错性**以及**文件下载的生命周期管理**上做进一步增强，它将成为一个端到端体验极佳的自动化利器。
