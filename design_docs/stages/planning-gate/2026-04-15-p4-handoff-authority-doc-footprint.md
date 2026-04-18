# Planning Gate — Handoff Authority-Doc Footprint

## 元信息

| 字段 | 值 |
|------|-----|
| Gate ID | 2026-04-15-p4-handoff-authority-doc-footprint |
| Scope | 为最新 active canonical handoff 增加最小 authority-doc / checkpoint footprint，使 safe-stop 的 handoff 发生可长期回溯 |
| Status | DONE |
| 来源 | design_docs/subagent-research-synthesis.md §P4，design_docs/subagent-tracing-writeback-direction-analysis.md Gap E，design_docs/direction-candidates-after-phase-35.md After A1，design_docs/tooling/Session Handoff Standard.md |
| 前置 | 2026-04-15-stub-worker-payload-producer-alignment 已完成 |
| 测试基线 | 936 passed, 2 skipped |

## 文档定位

本文件用于把 P4 `handoff 审计痕迹 / authority-doc footprint` 收敛成一个可审核的窄 scope planning contract。

目标不是重做 tracing / audit 系统，也不是把 handoff 正文复制进状态板，而是给“最新 active canonical handoff”补一个**最小、稳定、可回溯**的 footprint，并把它同步到 authority-doc / checkpoint / safe-stop helper 面。

## 当前问题

当前仓库已经具备：

1. canonical handoff 存放在 `.codex/handoffs/history/`。
2. `CURRENT.md` 作为当前 active canonical handoff 的 mirror entrypoint。
3. safe-stop writeback bundle 明确要求 handoff generation + CURRENT refresh + Checklist / Phase Map / checkpoint sync。

但当前仍有一个明确缺口：

1. handoff 的发生主要只留在 `.codex/handoffs/` 内部对象里。
2. `Project Master Checklist` 与 `Global Phase Map` 会说明“最近完成了哪个切片”，但不会显式指出“哪个 canonical handoff 关闭了这次 safe stop”。
3. `checkpoint` 当前也没有单独的 `Current Handoff` / `Latest Canonical Handoff` 结构段。

结果是：

1. 长期回溯时，authority docs 不能直接把人引到对应 handoff。
2. 一旦 `CURRENT.md` 再次轮转，前一个 safe stop 的 handoff footprint 就只剩历史文件，状态板本身不再可追溯。
3. Gap E 仍然处于“handoff 已存在，但 authority-doc footprint 不清晰”的状态。

## 权威输入

- `design_docs/subagent-research-synthesis.md`
- `design_docs/subagent-tracing-writeback-direction-analysis.md`
- `design_docs/tooling/Session Handoff Standard.md`
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `.codex/handoffs/CURRENT.md`
- `src/workflow/checkpoint.py`
- `src/workflow/safe_stop_writeback.py`

## 候选阶段名称

- `P4: Handoff Authority-Doc Footprint`

## 推荐方案

推荐把当前问题拆成两个明确边界，而不是混成一个“大审计改造”：

1. **footprint data surface**：定义 latest active canonical handoff 的最小 footprint 字段，只保留 pointer 信息，不复制 handoff 正文。
2. **authority/recovery sync surface**：把同一份 footprint 同步到 Checklist / Phase Map / checkpoint / safe-stop helper 输出，保证 recovery 与长期状态面能指向同一个 handoff。

其中第 1 项是数据 contract，第 2 项是落点同步；本轮不碰新的 audit event 设计，也不做历史 handoff ledger。

第一版规则：

1. latest handoff footprint 只允许包含最小 pointer 字段，例如：`handoff_id`、`source_path`、`scope_key`、`created_at`。
2. Checklist 只新增一个 compact footprint 入口，不复制 handoff 的 `Summary` / `Boundary` / `Open Items` 正文。
3. Phase Map 只增加当前 safe-stop 对应 handoff 的 compact trace 指针，不扩成历史流水账。
4. checkpoint 增加 dedicated `Current Handoff`（或等价命名）结构段，且必须继续可被 `read_checkpoint()` 稳定解析。
5. safe-stop helper / writeback helper 输出应暴露同一份 footprint 数据，使手工 writeback 与后续自动化都使用同一 contract。

理由：

1. 这正好命中 Gap E，而不会把范围重新扩回 Gap A-D 那种 tracing 基建层改动。
2. latest handoff footprint 是 pointer，不是第二份 handoff；能补追溯入口，又不会制造新的真相来源。
3. 同步 Checklist / Phase Map / checkpoint / helper 输出，可以把“长期状态面”和“恢复入口”对齐到同一对象。

## 本轮只做什么

1. 定义 latest active canonical handoff 的最小 footprint contract
   - 明确字段边界
   - 明确哪些面只记录 pointer，哪些面继续以 canonical handoff 为真相源

2. 为 checkpoint 增加 handoff footprint 结构段
   - `write_checkpoint()` / `read_checkpoint()` / `validate_checkpoint()` 保持一致
   - recovery 后无需只靠 `CURRENT.md` 才知道当前 safe-stop 的 handoff 指针

3. 为 authority docs 增加 compact handoff footprint 落点
   - `design_docs/Project Master Checklist.md`
   - `design_docs/Global Phase Map and Current Position.md`
   - 仅同步最小 pointer，不复制 handoff 正文

4. 为 safe-stop helper 输出补 handoff footprint 数据
   - 使 `safe_stop_writeback` / next-step helper 能提供同一份 handoff pointer，减少手工回写时的漂移

5. 补 targeted tests
   - checkpoint 新结构段可读写、可校验
   - helper 输出包含 footprint contract
   - authority-doc sync 所需格式在测试或 fixture 中固定

## 本轮明确不做什么

- 不新增新的 audit event type
- 不改 decision logs 字段模型
- 不把 Phase Map / Checklist 变成 handoff 历史流水账
- 不回填历史 handoff 的 authority-doc footprint
- 不把 handoff 正文复制进 authority docs
- 不同时启动 `LLMWorker` payload producer 方向

## 关键实现落点

- `src/workflow/checkpoint.py`
- `src/workflow/safe_stop_writeback.py`
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- 可能补充：相关 MCP / workflow helper 输出测试

## 验收与验证门

- [x] latest active canonical handoff 的最小 footprint contract 已固定
- [x] checkpoint 能稳定读写 handoff footprint，且 parser / validator 不回退
- [x] Checklist / Phase Map 能指向当前 safe-stop 对应的 canonical handoff
- [x] authority docs 仍不复制 handoff 正文，只保留 pointer footprint
- [x] safe-stop helper 输出与 checkpoint / authority docs 使用同一份 footprint 数据
- [x] targeted tests 新增 >= 6（实际新增 8；定向回归 72 passed）
- [x] 全量回归继续通过（936 passed, 2 skipped）

## 需要同步的文档

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/direction-candidates-after-phase-35.md`（若状态变化需要回写）
- `design_docs/tooling/Session Handoff Standard.md`（若 helper contract 文案需要对齐）
- 本 planning-gate 文档自身

## 子 agent 切分草案

- 本轮不引入子 agent。
- 理由：P4 需要同时把握 handoff 标准、checkpoint 结构与 authority-doc footprint，主 agent 直接收口更稳妥。

## 收口判断

- **为什么这条切片可以单独成立**：它只解决“handoff 如何在 authority-doc / checkpoint 面留下最小可回溯 footprint”，不扩成新的 tracing 基建或 handoff ledger。
- **做到哪里就应该停**：latest active canonical handoff 的 pointer footprint 能稳定同步到 authority docs / checkpoint / helper 输出，且 recovery 入口与长期状态面一致，即停。
- **下一条候选主线**：若本切片完成，再决定是扩到 `LLMWorker` structured payload producer，还是继续 controlled dogfood 观察 signal。

## 执行结果

- 状态：DONE
- 完成日期：2026-04-15
- 改动文件：
   - src/workflow/handoff_footprint.py
   - src/workflow/checkpoint.py
   - src/workflow/safe_stop_writeback.py
   - tests/test_checkpoint.py
   - tests/test_safe_stop_writeback.py
   - tests/test_mcp_tools.py
   - design_docs/Project Master Checklist.md
   - design_docs/Global Phase Map and Current Position.md
   - design_docs/direction-candidates-after-phase-35.md
   - design_docs/tooling/Session Handoff Standard.md
   - .codex/checkpoints/latest.md
- 说明：
   - 新增共享 helper `src/workflow/handoff_footprint.py`，从 `CURRENT.md` 提取统一的 4 字段 pointer contract：`handoff_id`、`source_path`、`scope_key`、`created_at`。
   - `write_checkpoint()` 现在会写出 dedicated `Current Handoff` 结构段，`read_checkpoint()` / `validate_checkpoint()` / `sync_checkpoint_phase()` 同步消费同一 contract，并保持对旧 checkpoint 的向后兼容。
   - `build_safe_stop_writeback_bundle()` 现在会暴露 `current_handoff_footprint`，使 helper 输出与 authority docs / checkpoint 使用同一份 pointer 数据。
   - Checklist 与 Phase Map 已补入 compact current-handoff footprint，而不复制 handoff 正文。
- 验证：
   - targeted tests：72 passed
   - full regression：936 passed, 2 skipped