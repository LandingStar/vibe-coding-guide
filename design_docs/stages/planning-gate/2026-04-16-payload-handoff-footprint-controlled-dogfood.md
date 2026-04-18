# Planning Gate — Payload + Handoff Footprint Controlled Dogfood

## 元信息

| 字段 | 值 |
|------|-----|
| Gate ID | 2026-04-16-payload-handoff-footprint-controlled-dogfood |
| Scope | 在不继续扩大 producer 语义的前提下，用当前 Stub + LLMWorker payload path 与 latest handoff footprint 做一轮受控 dogfood，并把观察结果写回统一状态面 |
| Status | DONE |
| 来源 | `design_docs/direction-candidates-after-phase-35.md` After LLMWorker Structured Payload Producer Alignment，`review/research-compass.md`，`design_docs/stages/planning-gate/2026-04-16-llmworker-structured-payload-producer-alignment.md` |
| 前置 | `2026-04-16-llmworker-structured-payload-producer-alignment` 已完成 |
| 当前基线 | 942 passed, 2 skipped |

## 文档定位

本文件用于把“先观察真实 signal，再决定是否继续扩 real-worker 实现面”收敛成一个可审核的窄 scope dogfood contract。

目标不是继续改 `LLMWorker`、不是顺手修 `HTTPWorker`，也不是把 controlled dogfood 扩成开放式探索，而是严格围绕当前已经打通的三块能力建立一轮可回放、可记录、可停止的 dogfood：

1. `StubWorker` 的最小 first-party payload path。
2. `LLMWorker` 的 schema-valid 单 payload producer path。
3. latest canonical handoff footprint 作为 safe-stop 恢复与状态面入口。

## 当前问题

当前仓库已经同时具备：

1. `StubWorkerBackend` 的受控 `artifact_payloads` 产出路径。
2. `LLMWorker` 的 schema-valid report baseline 与最小单 payload producer。
3. latest canonical handoff footprint 已同步到 Checklist / Phase Map / checkpoint / CURRENT。

但当前仍有一个明显缺口：

1. 这些路径目前主要由定向测试与 mocked integration 证明可用。
2. 真实使用 signal 仍不足，尤其是“当前 payload path + latest handoff footprint”在受控 dogfood 下的可操作性与恢复体验。
3. 若此时继续直接扩实现，很容易把多 payload、prompt 细化、`HTTPWorker` follow-up 或更宽 dogfood 一次性卷回来，而没有先获得真实使用反馈。

## 权威输入

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/direction-candidates-after-phase-35.md`
- `design_docs/stages/planning-gate/2026-04-16-llmworker-structured-payload-producer-alignment.md`
- `review/research-compass.md`
- `docs/subagent-schemas.md`
- `.codex/handoffs/CURRENT.md`
- `.codex/checkpoints/latest.md`

## 候选阶段名称

- `Payload + Handoff Footprint Controlled Dogfood`

## 推荐方案

推荐把这轮 dogfood 压成“一个受控观察回路”，而不是继续追加功能：

1. **preflight**：先确认当前环境、凭据与目标边界，明确这次 dogfood 是要验证什么，不验证什么。
2. **baseline run**：至少执行一条 `StubWorker` payload 路径，确保基线与 writeback / handoff footprint 恢复面可对照。
3. **real-model run**：在凭据可用时执行一条 `LLMWorker` 真实路径；若凭据不可用，则明确记录 blocked preflight，而不是临时扩 scope。
4. **result writeback**：把观察结果写回一个统一的 dogfood 结果面，并更新 Checklist / Phase Map / checkpoint / handoff 所需结论。

理由：

1. 当前最缺的是 signal，不是更多 producer 语义。
2. baseline + real-model 的双轨 dogfood 可以把“测试可用”和“真实使用可用”区分开来。
3. 明确 preflight blocked 允许在缺凭据时安全停下，而不会把 controlled dogfood 变成无限扩展的实现任务。

## 本轮只做什么

1. 定义一条受控 dogfood 回路
   - 明确 baseline run 与 real-model run 的最小步骤
   - 明确要记录哪些信号：payload 产出、writeback summary、handoff footprint 恢复体验、失败时的 review/blocked 表现

2. 准备 dogfood 执行与记录面
   - 一份窄 scope dogfood guide 或 runbook
   - 一份结果记录面，用于收口 signal 与建议下一步

3. 执行 baseline run
   - 至少跑通一条当前 `StubWorker` payload path
   - 记录与 latest handoff footprint / checkpoint 恢复面的关系

4. 视 preflight 执行 real-model run
   - 若 `LLMWorker` 所需凭据与目标配置可用，则跑一条真实路径
   - 若不可用，则显式记录 blocked preflight 与缺失前置，不改成新的实现任务

5. 写回结论
   - 把结果同步到 dogfood 结果面
   - 若结论足够明确，再更新 direction-candidates / Checklist / Phase Map 的下一步判断

## 本轮明确不做什么

- 不修改 `LLMWorker` / `StubWorkerBackend` 的 producer 逻辑
- 不修改 `HTTPWorker` 成功态或失败态实现
- 不新增 `Subagent Report` schema 字段
- 不继续扩多 payload / 多文件 producer
- 不把 dogfood 结果直接当成新的功能实现切片
- 不修改 handoff / checkpoint 的协议结构

## 关键落点

- `design_docs/stages/planning-gate/2026-04-16-payload-handoff-footprint-controlled-dogfood.md`
- `review/` 下新的 dogfood 记录面，或同等职责文档
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `.codex/checkpoints/latest.md`
- `.codex/handoffs/CURRENT.md`（若本轮最终再次形成 safe stop）

## 验收与验证门

- [x] dogfood preflight 已明确写出所需凭据、目标边界与停止条件
- [x] baseline `StubWorker` run 已执行并记录
- [x] real-model `LLMWorker` run 已执行，且记录了 live payload producer 未稳定收口的真实 signal
- [x] 结果面明确区分“测试证明”“mock 证明”“real signal”三者
- [x] 下一步判断已收口为 1-2 个窄候选，而不是开放式 backlog

## 关键待决问题

- 当前最需要你确认的是：**本轮 controlled dogfood 是否把“真实 LLM 凭据可用并实际跑一条 live path”视为强制完成门。**
- 我当前倾向于把 live run 设为“有凭据则强制执行，无凭据则允许以 blocked preflight 安全收口”，因为这能保持切片窄且不把缺环境误写成实现缺陷。

## 执行结果

- 状态：DONE
- 完成日期：2026-04-16
- 结果记录：`review/payload-handoff-footprint-controlled-dogfood-2026-04-16.md`
- 实际观察：
   - baseline `StubWorker` payload path 在临时目录里可稳定触发 payload-derived writeback，`CURRENT.md` 与 checkpoint 的 latest handoff footprint 一致。
   - live `LLMWorker` 路径成功返回 schema-valid `completed` report，但真实模型给出的 payload candidate 使用了 schema 不接受的枚举值（如 `upsert`、`text/markdown`），因此被保守归一化层丢弃，没有触发 artifact writeback。
- 结论：
   - 当前 baseline 已成立，真实模型路径也已给出高价值 signal。
   - 下一条默认主线应转入更窄的 `LLMWorker live payload contract hardening` / real-worker consistency follow-up，而不是继续泛化 dogfood。