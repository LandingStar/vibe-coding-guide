# Planning Gate — Handoff Recovery Hardening

## 元信息

| 字段 | 值 |
|------|-----|
| Gate ID | 2026-04-15-handoff-recovery-hardening |
| Scope | 修复 handoff recovery 链的 mirror hash、唯一 active 断言与诊断信息 |
| Status | DONE |
| 来源 | 本次 safe-stop 恢复过程 review 中发现的真实阻塞 |
| 前置 | 2026-04-15_1827_worker-registry-executor-integration_stage-close 已 active |
| 测试基线 | 898 passed, 2 skipped |

## 文档定位

本文件用于把本次 safe-stop 恢复过程中暴露出的 handoff recovery 缺口收敛成一个极窄的 remediation slice。

## 当前问题

本次从 safe stop 恢复时，真实踩中了 3 个问题：

1. `CURRENT.md` 一度不是合法 mirror 结构，导致 accept intake 直接 blocked。
2. `history/` 中存在多个 `active` canonical handoff，导致 refresh-current 无法继续。
3. `Authoritative Sources` 的漂移 warning 偏噪声，恢复时需要额外人工判断。

结合现有实现，当前缺口是：

- accept intake 没有校验 `CURRENT.md -> canonical` 的 `source_hash`
- refresh-current 在 multiple active 时只返回泛化错误，不暴露具体冲突项
- safe-stop writeback bundle 目前只产出 contract，不提供最终 handoff recovery invariant 断言

## 权威输入

- `design_docs/tooling/Session Handoff Standard.md`
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `.github/skills/project-handoff-accept/SKILL.md`
- `.github/skills/project-handoff-refresh-current/SKILL.md`
- `.github/skills/project-handoff-accept/scripts/intake_handoff.py`
- `.github/skills/project-handoff-refresh-current/scripts/refresh_current.py`
- `src/workflow/safe_stop_writeback.py`

## 候选阶段名称

- `Recovery Hardening: Handoff Intake / Refresh Invariants`

## 本轮只做什么

1. 补 `CURRENT.md` mirror 完整性校验
   - 在 current intake 路径校验 `source_hash`
   - 当 canonical 内容与 `CURRENT.md` 记录的 hash 不一致时，返回 blocked

2. 补唯一 active canonical 断言
   - 为 recovery 路径提供明确 invariant：`history/` 中应恰好有一个 `active` canonical handoff
   - current intake 在读取 mirror 时，也能识别 `0` 个或 `>1` 个 active canonical 的异常状态

3. 提升 refresh-current 诊断信息
   - `multiple active canonical handoffs already exist` 时，返回具体 handoff id / path 列表
   - `supersedes` 不匹配时，返回当前 active canonical 的具体 id / path

4. 收紧 `Authoritative Sources` 漂移提示
   - 至少支持把“引用路径 + 说明文字”解析为同一个 ref
   - 避免正确引用因附带说明而产生误导性 warning

5. 补 targeted tests
   - hash mismatch
   - multiple active canonical
   - no active canonical
   - refresh 诊断 payload
   - annotated authoritative refs 不再误报

## 本轮明确不做什么

- 不改 handoff 生成内容模型
- 不改 canonical handoff schema
- 不实现新的 safe-stop executor
- 不把 safe-stop bundle 变成全自动写回系统
- 不进入 P2 `Handoff Validator` 正题

## 关键实现落点

- `.github/skills/project-handoff-accept/scripts/intake_handoff.py`
  - `source_hash` 校验
  - active canonical 集合检查
  - ref 解析收紧
- `.github/skills/project-handoff-refresh-current/scripts/refresh_current.py`
  - richer blocking diagnostics
- `tests/`
  - 新增 handoff recovery script tests
- 如有必要：`src/workflow/safe_stop_writeback.py`
  - 仅补 invariant 表达，不引入执行器

## 验收与验证门

- [x] current intake 遇到 `source_hash` 不一致时 blocked
- [x] current intake 遇到 `0` 或 `>1` 个 active canonical 时 blocked
- [x] refresh-current 的 blocked 结果包含冲突 handoff 明细
- [x] annotated authoritative refs 不再产生误导性 warning
- [x] 新增 targeted tests ≥ 6（实际 6）
- [x] 全量回归继续通过（898 passed, 2 skipped）

## 需要同步的文档

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- 本 planning-gate 文档自身

## 子 agent 切分草案

- 本轮不引入子 agent。
- 理由：问题集中在 handoff protocol script 与状态不变量，范围小但需要主 agent 统一把握协议边界。

## 收口判断

- **为什么这条切片可以单独成立**：它只修恢复链可靠性，不引入新的 handoff 语义层。
- **做到哪里就应该停**：3 类不变量与诊断补齐、targeted tests 通过、全量回归通过，即停。
- **下一条候选主线**：回到 [design_docs/stages/planning-gate/2026-04-15-handoff-validator-independent-guard.md](design_docs/stages/planning-gate/2026-04-15-handoff-validator-independent-guard.md) 推进 P2。

## 执行结果

- 状态：DONE
- 完成日期：2026-04-15
- 改动文件：
   - .github/skills/project-handoff-accept/scripts/intake_handoff.py
   - .github/skills/project-handoff-refresh-current/scripts/refresh_current.py
   - tests/test_handoff_recovery_hardening.py
- 验证：
   - targeted tests：6 passed
   - full regression：898 passed, 2 skipped
