# Planning Gate — Real-Worker Payload Adoption Judgment

## 元信息

| 字段 | 值 |
|------|-----|
| Gate ID | 2026-04-16-real-worker-payload-adoption-judgment |
| Scope | 基于单次成功的 live `LLMWorker` rerun，收口当前 preview / dogfood 口径下 real-worker payload path 的 adoption judgment 边界；只做文档判断与 backlog 记录，不进入新的 runtime 实现 |
| Status | **DONE** |
| 来源 | `design_docs/live-payload-rerun-followup-direction-analysis.md`，`review/live-payload-rerun-verification-2026-04-16.md`，`docs/first-stable-release-boundary.md`，`design_docs/direction-candidates-after-phase-35.md` |
| 前置 | `2026-04-16-live-payload-rerun-verification` 已完成 |
| 测试基线 | 946 passed, 2 skipped |

## 文档定位

本文件用于把 `Live Payload Rerun Verification` 成功后的下一步收敛成一条窄 scope judgement 切片。

目标不是继续追加 `LLMWorker` hardening 代码，也不是马上扩成更多 live 试验，而是回答一个更高层的问题：

1. 当前这一次成功的 real-worker payload rerun，在 preview / dogfood 口径下到底代表什么。

## 当前问题

来自 `review/live-payload-rerun-verification-2026-04-16.md` 与 `design_docs/live-payload-rerun-followup-direction-analysis.md` 的当前事实：

1. 单次受控 live DashScope rerun 已返回合法 `artifact_payloads`，并在临时目录中成功命中 payload-derived writeback。
2. 当前 hardening 至少已在一条受控 real-model path 上得到正向验证。
3. `docs/first-stable-release-boundary.md` 仍要求 real worker adapters 不被轻率表述成默认稳定面。
4. 当前剩余问题不再是明显的 implementation gap，而是 adoption / dogfood judgment 的边界定义。
5. 用户新增要求：把 dogfood 所需的证据收集、问题收集、问题反馈整合能力，明确记录为一个后续组件或 skill backlog，而不是散落在即时流程里。

## 目标

**做**：

1. 明确这次单次 live success 在当前 preview / dogfood 口径下意味着什么。
2. 明确这次成功还不意味着什么，避免把 single-success signal 外推成默认稳定面声明。
3. 定义继续 dogfood 所需的最小额外证据门或判断门。
4. 把“dogfood 证据收集 / 问题收集 / 反馈整合组件或 skill”记录进 backlog，并说明它为何不在本轮直接实现。
5. 在执行 adoption judgment 的 1、2 两步时，同步观察哪些过程值得后续抽象固化为组件或 skill，但本轮只记录，不实现。

**不做**：

1. 不修改 `src/workers/llm_worker.py`。
2. 不修改 `docs/specs/subagent-report.schema.json` 或 `docs/subagent-schemas.md`。
3. 不执行第二次 live rerun。
4. 不修改 `HTTPWorker`。
5. 不在本轮实现 dogfood evidence/issue/feedback 组件或 skill。

## 推荐方案

### 1. 先固定当前证据边界

把当前已拿到的真实证据压缩成三层：

1. raw response 合法。
2. final report 合法且保持 `completed`。
3. payload-derived writeback 真实命中临时目录目标文件。

在这一步里，还要同步观察：哪些证据收集动作是重复且可标准化的，适合作为后续 dogfood 组件或 skill 的抽象候选。

### 2. 再固定 adoption wording

本轮要明确写出：

1. 当前可以安全说“受控 real-worker payload path 已获得一条正向 live signal”。
2. 当前不能直接说“real-worker payload path 已成为默认稳定面”。
3. 后续若继续 dogfood，需要额外满足什么最小证据门。

在这一步里，还要同步观察：哪些问题收集 / 反馈整合动作目前仍依赖人工判断，后续值得抽象固化。

### 3. backlog 单独记账

把以下需求显式记入 backlog，但不在本轮实现：

1. dogfood 证据收集
2. dogfood 问题收集
3. dogfood 问题反馈整合

推荐把它表述为“后续应收口为一个组件或 skill”，避免继续依赖临时人工拼装流程。

## 关键落点

- `design_docs/stages/planning-gate/2026-04-16-real-worker-payload-adoption-judgment.md`
- `design_docs/live-payload-rerun-followup-direction-analysis.md`
- `review/live-payload-rerun-verification-2026-04-16.md`
- `review/real-worker-payload-adoption-judgment-2026-04-16.md`
- `docs/first-stable-release-boundary.md`
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/direction-candidates-after-phase-35.md`

## 验证门

- [x] adoption judgment 明确区分“当前可以说什么”与“当前不能说什么”
- [x] 继续 dogfood 的最小额外证据门已被显式写出
- [x] dogfood evidence / issue / feedback 组件或 skill 需求已被记录进 backlog
- [x] 本轮没有改动 runtime code、schema、`HTTPWorker` 或新增 live rerun

## 执行结果（2026-04-16）

### adoption wording

本轮 judgment 已收口出以下 3 条当前可安全口径：

1. `LLMWorker` real-worker payload path 已有 1 条正向 live signal。
2. 这条 signal 同时成立于 raw response、final report 与 payload-derived writeback 三层。
3. 当前可以继续使用“受控 dogfood 路径”的表述，但不能扩大为默认稳定面承诺。

### 最小额外证据门

若后续想把 wording 扩大到“受控 real-worker payload path 具有可重复 dogfood 能力”，最小额外证据门已被收口为：

1. 在无新 runtime code、schema 或 worker 语义变更前提下，再拿到 1 条独立受控 live success。
2. 新 success 仍需同时满足 raw response、final report 与 payload-derived writeback 三层证据。
3. 若不满足，应先记录为新 dogfood observation，而不是扩大 adoption wording。

### 抽象候选与 backlog

在执行 1、2 两步时，本轮已经识别出 3 类可抽象流程：

1. 证据收集 bundle
2. dogfood 问题分类
3. 反馈整合面

这些已被继续登记为 backlog，但本轮不进入实现。详见：`review/real-worker-payload-adoption-judgment-2026-04-16.md`

## 收口判断

- **为什么这条切片可以单独成立**：它只处理当前正向 real signal 的边界解释，不追加新的实现与试验。
- **做到哪里就应该停**：把 adoption wording、最小额外证据门与 backlog 记录写清楚，即停。
- **下一条候选主线**：当前 adoption judgment 已要求“再拿到 1 条独立受控 live success”才可扩大 wording，因此下一步更自然的主线是 `controlled real-worker payload evidence accumulation`；`HTTPWorker failure fallback schema alignment` 仍是正交备选。

## 审核结果

- 当前 gate 已按“先锁定最小额外证据门，再记录 backlog 抽象候选”的边界执行完成。
- 你新增的两条要求都已纳入结果面：
	1. backlog 先记录
	2. 在 1、2 两步中显式观察可抽象流程，但不把实现混进本轮