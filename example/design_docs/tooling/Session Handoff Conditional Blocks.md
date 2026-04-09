# Session Handoff Conditional Blocks

## 1. 文档定位

本文件定义 handoff 协议中的 conditional blocks。

它解决的问题是：

- 哪些场景下，handoff 必须额外记录专门信息
- 这些额外信息的触发条件是什么
- 每类场景最少需要哪些字段
- 如何让 handoff 协议保持可扩展，而不是不断膨胀 core fields

本文件是 conditional blocks 的 authoritative source。

---

## 2. Conditional Block 注册表格式

每个 conditional block 必须以统一结构定义：

- `block_key`
- `purpose`
- `trigger`
- `required_fields`
- `verification_expectation`
- `authoritative_refs`

说明：

- `block_key` 用于 handoff frontmatter 中的 `conditional_blocks`
- `trigger` 描述何时必须启用该 block
- `required_fields` 描述正文中该 block 必须提供的信息
- `verification_expectation` 描述该 block 对验证信息的最低要求
- `authoritative_refs` 指向接手方应优先核对的正式来源

---

## 3. 当前启用的 Blocks

当前第一版启用以下 blocks：

- `code-change`
- `cli-change`
- `transport-recovery-change`
- `authoring-surface-change`
- `phase-acceptance-close`
- `dirty-worktree`

---

## 4. Block Definitions

### 4.1 `code-change`

`purpose`:
记录本轮确实发生了代码改动时，接手方必须知道的最小实现信息。

`trigger`:
本轮 handoff 覆盖范围内存在代码新增、删除或修改。

`required_fields`:

- `Touched Files`
- `Intent of Change`
- `Tests Run`
- `Untested Areas`

`verification_expectation`:

- 必须说明已跑过的针对性验证
- 若未跑全量验证，必须明确说明
- 若只改文档却误触发本 block，应视为结构错误

`authoritative_refs`:

- 相关源码路径
- 相关测试路径
- 若涉及阶段收口，则还应参考对应阶段文档

### 4.2 `cli-change`

`purpose`:
确保 CLI 变化不会只留在对话里，而能被正式帮助、文档与回归追踪。

`trigger`:
本轮 handoff 覆盖范围内新增或修改了 CLI 指令、help 输出、观察入口或命令行为。

`required_fields`:

- `Changed Commands`
- `Help Sync Status`
- `Command Reference Sync Status`
- `CLI Regression Status`

`verification_expectation`:

- 必须说明 `help`、`help <command>`、`help all` 是否已同步
- 必须说明命令参考文档是否已同步
- 必须说明是否有对应自动化或手测

`authoritative_refs`:

- `demo/command_reference.py`
- `design docs/CLI Command Reference.md`
- 对应 CLI 回归测试

### 4.3 `transport-recovery-change`

`purpose`:
记录 transport、predictive、replay、resync、recover 类变化在交接时需要的额外验证信息。

`trigger`:
本轮 handoff 覆盖范围内修改了 transport、预测、重播、恢复、快照重建或相关诊断路径。

`required_fields`:

- `Changed Recovery Surface`
- `Asymmetric Verification Status`
- `Manual Recovery Check`
- `Known Recovery Risks`

`verification_expectation`:

- 必须说明是否进行了非对称注入验证
- 必须说明是否做了手测或等价恢复验证
- 若未验证，必须直接写明而非模糊带过

`authoritative_refs`:

- `tests/support/scenario_tools.py`
- `design docs/Verification Gate and Phase Acceptance Workflow.md`
- 相关 host/session/recovery 文档与测试

### 4.4 `authoring-surface-change`

`purpose`:
确保作者化入口的变化同步到使用文档与发现路径，而不是只改实现。

`trigger`:
本轮 handoff 覆盖范围内新增或修改了作者化入口、registry/discovery surface 或其文档标准相关实现。

`required_fields`:

- `Changed Authoring Surface`
- `Usage Guide Sync Status`
- `Discovery Surface Status`
- `Authoring Boundary Notes`

`verification_expectation`:

- 必须说明对应 usage guide 是否同步
- 必须说明 discovery/CLI 入口是否同步
- 必须说明当前支持边界是否更新

`authoritative_refs`:

- `design docs/tooling/Authoring Documentation Standard.md`
- 对应 usage guide
- 若涉及 CLI，则还应参考命令参考文档

### 4.5 `phase-acceptance-close`

`purpose`:
确保阶段或 phase 收口时，handoff 能携带最小验收信息，而不是只给一句“已完成”。

`trigger`:
本轮 handoff 是阶段或 phase 的正式收口交接。

`required_fields`:

- `Acceptance Basis`
- `Automation Status`
- `Manual Test Status`
- `Checklist/Board Writeback Status`

`verification_expectation`:

- 必须说明验收依据是什么
- 必须说明自动化、手测、状态板回写是否完成
- 若存在缺口，必须明确列出

`authoritative_refs`:

- `design docs/Verification Gate and Phase Acceptance Workflow.md`
- `design docs/Project Master Checklist.md`
- 当前阶段对应范围文档与手测文档

### 4.6 `dirty-worktree`

`purpose`:
让接手方知道当前 workspace 中是否存在未清理但重要的现实状态。

`trigger`:
生成 handoff 时，工作区存在未提交修改、未跟踪文件，或其他会影响判断的脏状态。

`required_fields`:

- `Dirty Scope`
- `Relevance to Current Handoff`
- `Do Not Revert Notes`
- `Need-to-Inspect Paths`

`verification_expectation`:

- 必须说明这些脏状态是否与本次交接直接相关
- 必须区分“已知重要修改”和“可忽略噪音”
- 不得用模糊描述替代路径级说明

`authoritative_refs`:

- 当前 workspace 现实状态
- 相关路径本身
- 若需要，可附带最小 git 状态摘要

---

## 5. 新 Block 的扩展流程

新增 conditional block 时，应满足以下条件：

- 该类信息已不适合继续塞进 core fields
- 该类信息重复出现，且对接手质量有稳定影响
- 它不是一次性的临时例外
- 它能够定义出稳定的 `trigger` 与 `required_fields`

新增 block 不应只是为了容纳一条随手备注。

新增 block 时，应同步更新：

- 本文件
- `Session Handoff Standard.md` 中的相关引用
- handoff 模板
- 校验逻辑
- 对应 fixtures 与测试

---

## 6. `Other -> 正式 Block` 的晋升规则

当同类 `Other` 条目重复出现时，不应长期停留在 `Other`。

若满足以下任一条件，应考虑晋升为正式 conditional block：

- 同类 `Other` 连续出现两次以上
- 接手时反复需要额外解释
- 该类信息已有稳定 trigger
- 该类信息已有明确验证期望

晋升后：

- 未来同类信息应优先进入新 block
- 不再继续默认写入 `Other`

---

## 7. 校验要求

handoff 校验至少应检查：

- frontmatter 中声明的 `conditional_blocks` 是否与正文 block 一致
- 命中的 trigger 是否真的成立
- 每个 block 的 `required_fields` 是否齐全
- block 内信息是否误写到 `Other`
- 未命中的 block 是否被漏掉

若发现某条信息应属于现有 block，却被写到 `Other`，应判为结构错误而不是仅给 warning。

---

## 8. 当前边界

本文件当前只定义：

- conditional blocks 的结构
- 当前已启用 blocks
- 扩展与晋升规则
- 最小校验要求

本文件当前不定义：

- 具体 skill 调用方式
- 脚本实现细节
- handoff 文件轮转命令
- 模板渲染实现

这些内容应保留在项目专用的 `.codex/handoff-system/` 下。
