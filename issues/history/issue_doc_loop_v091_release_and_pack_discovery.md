# Issue: `doc-based-coding-v0.9.1` 存在版本文档漂移、官方 pack 自动发现缺失，以及本地双 wheel 安装体验不顺畅的问题

## 标题

`doc-based-coding-v0.9.1` 在实际工作区安装与接入过程中，暴露出三类容易误导用户和 agent 的问题：

- release 包名与包内文档版本不一致
- runtime 默认无法自动发现已安装的官方实例 pack
- 本地双 wheel 安装在离线/本地文件场景下不够顺畅

## 背景

在一个已经 bootstrap 完成、并带有项目本地 pack 的 workspace 中，使用根目录下的：

```powershell
doc-based-coding-v0.9.1.zip
```

进行安装与接入验证。当前工作区采用：

```powershell
.\.venv-doc-based-coding\Scripts\
```

作为 runtime / CLI / MCP server 的安装位置，并通过：

```json
{
  "mcpServers": {
    "doc-based-coding": {
      "command": "powershell.exe",
      "args": [
        "-NoLogo",
        "-NoProfile",
        "-Command",
        "& \"${workspaceFolder}/.venv-doc-based-coding/Scripts/doc-based-coding-mcp.exe\" --project \"${workspaceFolder}\" --dry-run"
      ]
    }
  }
}
```

注册到当前工作区。

项目本地 pack 声明依赖：

```json
"depends_on": [
  "doc-loop-vibe-coding"
]
```

## 实际检查结果

安装并修正接入方式后，当前工作区最终可以达到以下正常状态：

- `doc-based-coding-runtime 0.9.1` 已安装
- `doc-loop-vibe-coding 0.9.1` 已安装
- `doc-based-coding info` 能同时识别：
  - `doc-loop-vibe-coding`
  - `modern phy. lab-local-pack`
- `doc-based-coding validate` 返回：
  - `command_status: "ok"`
  - `governance_status: "passed"`
- `doc-loop-validate-instance` 可通过
- `doc-based-coding-mcp --help` 可正常启动

也就是说，`v0.9.1` 并不是不可用，而是默认安装路径和发现链路下存在多处容易卡住的接入问题。

## 问题 1：release 包名与包内文档版本漂移 ✅ FIXED

> **修复状态**：当前 release 文件已统一为 `0.9.1`。新增
> `release/verify_version_consistency.py` 预发布验证脚本，自动检查
> pyproject.toml、pack-manifest.json、wheel 文件名、INSTALL_GUIDE.md、
> RELEASE_NOTE.md 之间的版本一致性。

### 现象

外层文件名为：

```text
doc-based-coding-v0.9.1.zip
```

但包内文档中仍保留大量 `1.0.0` 内容，例如：

- `INSTALL_GUIDE.md` 中示例 wheel 名仍为：
  - `doc_based_coding_runtime-1.0.0-py3-none-any.whl`
  - `doc_loop_vibe_coding-1.0.0-py3-none-any.whl`
- `RELEASE_NOTE.md` 标题仍写为：
  - `# doc-based-coding-platform v1.0.0`

### 影响

- 用户会怀疑自己下载错包
- agent 会被误导去按 `1.0.0` 文档操作
- 在回滚、降级、兼容性验证场景里很难快速判断“文档错了”还是“wheel 错了”

### 建议

- release 产物生成时校验 zip 名、wheel 名、`INSTALL_GUIDE.md`、`RELEASE_NOTE.md` 的版本一致性
- 将版本号改为单一来源自动注入，避免手工漏改

## 问题 2：runtime 默认不会自动发现已安装的官方实例 pack ✅ FIXED

> **修复状态**：已在 `src/workflow/pipeline.py` 的 `_discover_packs()` 中实现
> site-packages 自动扫描。`Pipeline.from_project()` 和 `GovernanceTools` 均已
> 透传 `include_site_packages` 参数。测试隔离问题通过在隔离测试中传入
> `include_site_packages=False` 解决。原 5 个失败测试已全部修复并通过。

### 现象

在 `0.9.1` 下，官方实例 pack 即使已通过 pip 安装到：

```text
.venv-doc-based-coding/Lib/site-packages/doc_loop_vibe_coding
```

`doc-based-coding info` / `validate` 仍不会自动加载它。

如果项目本地 pack 声明：

```json
"depends_on": ["doc-loop-vibe-coding"]
```

则会出现类似未解析依赖的现象，直到额外补一个显式配置：

```json
{
  "pack_dirs": [
    ".codex/packs",
    ".venv-doc-based-coding/Lib/site-packages/doc_loop_vibe_coding"
  ]
}
```

### 根因判断

`0.9.1` runtime 的 pack 自动发现逻辑主要扫描：

- `.codex/packs/*.pack.json`
- 项目根目录下一层子目录中的 `pack-manifest.json`

默认并不会扫描 Python 安装目录中的官方实例 pack。

### 影响

- “官方实例 pack 已安装”与“runtime 能加载官方实例 pack”变成两件不同的事
- 用户会误以为 pip 安装失败，或者以为 runtime 存在严重错误
- 带项目本地 overlay pack 的真实 adoption 场景会比文档描述复杂很多

### 建议

优先建议三种方案之一：

1. runtime 自动将已安装的官方实例 pack 纳入发现范围
2. bootstrap 时自动生成 `.codex/platform.json` 并填好 `pack_dirs`
3. 安装文档明确说明：若使用 `0.9.1`，需要显式声明官方实例 pack 的目录

如果希望保持当前发现机制不变，至少应在 `doc-based-coding info` / `validate` 的提示中更直接说明：

> 官方实例 pack 已安装，但当前未被自动发现；请通过 `pack_dirs` 显式声明 pack 路径。

## 问题 3：本地双 wheel 安装在离线/本地文件场景下不够顺畅 ✅ RESOLVED

> **状态**：INSTALL_GUIDE.md 已包含离线安装的推荐命令（`--force-reinstall` /
> `--no-deps` / `--find-links`）及旧版本卸载提示。文档层面已覆盖。

### 现象

本地已有两个 wheel：

- `doc_based_coding_runtime-0.9.1-py3-none-any.whl`
- `doc_loop_vibe_coding-0.9.1-py3-none-any.whl`

但直接执行实例包安装时，`pip` 不会自动从同目录 wheel 中解析本地依赖，表现为：

- runtime 安装后，若旧版本 pack 尚未卸载，会产生版本冲突提示
- 直接安装 `doc_loop_vibe_coding-0.9.1` 时，`pip` 会尝试去默认索引找 `doc-based-coding-runtime<1.0.0,>=0.9.1`
- 在离线/本地包场景下，这一步会失败

### 影响

- 用户很容易遇到“本地明明有 wheel，但安装还是失败”的困惑
- agent 需要额外处理：
  - 先卸旧 pack
  - 再手动安装 runtime
  - 再用 `--no-deps` 或 `--find-links` 安装实例包

### 建议

- 在安装文档中显式给出本地双 wheel 的推荐命令

例如：

```powershell
pip install --force-reinstall .\doc_based_coding_runtime-0.9.1-py3-none-any.whl
pip install --force-reinstall --no-deps .\doc_loop_vibe_coding-0.9.1-py3-none-any.whl
```

或：

```powershell
pip install --force-reinstall --no-index --find-links . doc_loop_vibe_coding-0.9.1-py3-none-any.whl
```

- 更进一步的话，可以考虑在 release 中附带一个统一安装脚本，减少 agent 和用户自行推导安装顺序的成本

## 问题 4：状态提取仍不完整 ✅ RESOLVED

> **状态**：在当前代码中验证，`validate` 已正确输出
> `current_phase: "Phase 35: v1.0 Stable Release Confirmation — 完成"`。
> `active_planning_gate` 为空是因为 checkpoint 中确实为 em-dash（无活跃 gate），
> 属于正确行为。此问题可能在旧版 runtime 下存在，当前版本已修复。

### 现象

在当前工作区已经具备：

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- planning-gate 文档

且 `validate` 已通过的情况下，`doc-based-coding validate` 输出里的：

- `current_phase`
- `active_planning_gate`

仍然为空字符串。

### 影响

- 运行时状态面板和项目真实文档状态不一致
- 上层 agent 无法仅依赖 runtime 输出来恢复当前 phase / active slice

### 建议

- 将 `validate` 的文档状态提取能力补齐，至少覆盖：
  - `Project Master Checklist`
  - `Global Phase Map`
  - `planning-gate` 目录
- 或在文档中明确说明：当前版本只检查约束，不保证抽取当前 phase / planning-gate 元数据

## 为什么这几个问题值得优先处理

这些问题共同指向一个更高层的交互风险：

- 平台本身其实能工作
- 但默认接入路径过于依赖用户或 agent 手动补齐隐式知识
- 最终会让首次 adoption 的人误以为“安装坏了”、“pack 没生效”或“版本不一致”

这会直接削弱 `doc-based-coding` / `doc-loop` 在真实项目里的首次接入体验，尤其是在：

- agent 自动安装
- 旧版本回退
- 离线 wheel 分发
- 项目本地 pack 叠加官方实例 pack

这些本来就更容易出问题的场景中。

## 建议优先级

如果只能先修最关键的部分，建议优先顺序为：

1. 修正 release 包内文档版本漂移
2. 让 runtime 能自动发现已安装的官方实例 pack，或自动生成 `pack_dirs`
3. 给出本地双 wheel 的标准安装指令

## 附：本次工作区中的临时解决方式

为了让 `0.9.1` 在当前工作区恢复到正常可用状态，本次实际采取了以下 workaround：

1. 将 runtime 与实例 pack 都安装到：
   - `.venv-doc-based-coding`
2. 在项目根目录新增：
   - `.codex/platform.json`
3. 显式声明：
   - `.codex/packs`
   - `.venv-doc-based-coding/Lib/site-packages/doc_loop_vibe_coding`

这套方式可以让 `info / validate / MCP` 都恢复正常，但它属于“用户侧补 wiring”，不应成为默认接入路径的隐性前提。
