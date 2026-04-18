# Dogfood Evidence / Issue / Feedback Boundary

## 文档定位

本文件收口 `dogfood evidence / issue / feedback integration` 这条 docs-only planning-gate 的核心设计产物。

它只回答 3 个问题：

1. `dogfood evidence`、`dogfood issue`、`dogfood feedback` 三类对象的最小边界分别是什么。
2. 它们当前分别落在哪些现有文档面上，哪些内容不应继续混写。
3. 若后续要把这条流程收口成组件或 skill，最小输入、输出与非目标是什么。

此外，本文件还承载了以下 contract 层（2026-04-16 追加）：

4. evidence 何时晋升为 issue 的 promotion threshold contract。
5. issue candidate 的最小字段集。
6. feedback packet 的最小字段集、消费者边界与消费原则。

本文件不是实现方案，也不是新的 workflow protocol；它只给后续实现型 planning-gate 提供边界基线。

## 核心判断

当前 dogfood 闭环里反复出现的人工流程，本质上应拆成 3 层，而不是继续混成一份“大而全的 review 结论”：

1. `dogfood evidence` 是事实层，只承载一次 dogfood 观察真正发生了什么。
2. `dogfood issue` 是问题层，只承载由一条或多条 evidence 提升出来、可复用的问题陈述。
3. `dogfood feedback` 是决策层，只承载 evidence / issue 对下一步方向、backlog 与状态面的影响。

因此：

1. `review/*.md` 应继续作为 evidence 的主落点。
2. 方向分析、direction-candidates、planning-gate 应主要消费 feedback，而不是重复携带 evidence 本体。
3. Checklist / Phase Map / checkpoint / handoff 应只保留 state、pointer、decision 层，不承载 evidence 本体。

## 1. Dogfood Evidence

### 定义

`dogfood evidence` 是一次受控 dogfood 观察里的原始事实集合，用来回答：

1. preflight 条件是什么。
2. raw signal 实际返回了什么。
3. final report / validation 结果是什么。
4. writeback、guard 或 blocked outcome 最终发生了什么。

它的单位默认是单次观察，而不是跨切片判断。

### 必含内容

一个最小 evidence 对象至少应能回溯以下事实：

1. 观察边界：endpoint、model、allowed_artifacts、运行目录、停止条件等。
2. 原始信号：raw response、error、blocked reason 或其他一手输出。
3. 结果信号：final report / validation / review_state / execution_status。
4. 写回信号：writeback outcome、目标路径、是否命中允许边界。
5. 对照上下文：它承接哪条 planning-gate、与哪条上一观察对照。

### 不应混入的内容

以下内容不属于 evidence 本体：

1. adoption wording 或 stable-boundary judgment。
2. 下一方向推荐。
3. backlog 优先级判断。
4. 跨切片的状态板写回文案。

这些属于 feedback，而不是 evidence。

### 当前主落点

当前 evidence 的主落点应保持为 `review/*.md`，例如：

1. `review/live-payload-rerun-verification-2026-04-16.md`
2. `review/controlled-real-worker-payload-evidence-accumulation-2026-04-16.md`

这些文档可以附带少量本地结论，但它们的首要职责仍是保存单次 dogfood 观察的事实层。

## 2. Dogfood Issue

### 定义

`dogfood issue` 是从一条或多条 evidence 中提升出来的、具有可复用行动意义的问题陈述。

它不再回答“这次发生了什么”，而是回答：

1. 当前暴露的是哪一类问题。
2. 这类问题对后续 direction / planning-gate 是否有稳定影响。
3. 它当前只需留在 review 文档，还是应升级为 backlog、direction 候选或专门 issue surface。

### 晋升条件

evidence 只有在满足下列至少一项时，才应晋升为 issue：

1. 同类问题跨不止一条观察重复出现。
2. 问题已经足以改变下一条切片的边界。
3. 问题不再只是一次性噪声，而是可复用分类。
4. 问题需要进入 backlog、direction-candidates 或独立 planning-gate 才能处理。

### Issue Promotion Threshold Contract

> 来源：`review/github-issue-quality/2026-04-16-dogfood-issue-standard-benchmark.md` 与本平台 doc-loop 消费性要求。

#### 触发条件（至少满足一条）

| # | 条件 | 说明 |
|---|------|------|
| T1 | **重复性** | 同类 symptom 在 ≥2 条独立 evidence 中出现，且不是同一观察的重复日志 |
| T2 | **边界影响** | 单条 evidence 已足以改变下一 planning-gate 或 direction 的边界假设 |
| T3 | **可分类性** | symptom 能被归入当前最小分类（见下方），而不是无法归类的随机噪声 |
| T4 | **后续切片需求** | 下一条切片如果不知道这个问题，会过早绑定错误假设或跳过必要验证 |

#### 抑制条件（命中任一条时不应晋升）

| # | 条件 | 说明 |
|---|------|------|
| S1 | **单次瞬时噪声** | 只在一次观察中出现过，且后续观察未复现，也无法稳定归因 |
| S2 | **已被其他 issue 覆盖** | 现有 issue candidate 已完整覆盖同一 symptom + 同一影响面 |
| S3 | **缺少可引用 evidence** | 无法指向至少一条 `review/*.md` 里的具体 evidence 段落 |

#### 晋升判断流程

```
evidence 出现 symptom
  ├─ 命中任一 S1-S3 → 留在 review/*.md，不晋升
  └─ 不命中 S1-S3，且命中至少一条 T1-T4
       └─ 晋升为 issue candidate → 填写 issue 最小字段（见下方）
```

### Issue Candidate 最小字段

一个被晋升的 issue candidate 至少应包含以下字段才可被后续 direction / gate / state-sync 消费：

| 字段 | 要求 | 来源 |
|------|------|------|
| **title** | `surface: symptom [under condition]` 格式；离开上下文仍可 triage | benchmark A1 |
| **problem_statement** | 3-6 句话回答：症状、影响面、触发条件、当前风险；必须是正文首段 | benchmark A1 |
| **category** | 必须落入当前最小分类之一（见下方） | benchmark A4 |
| **impact_layer** | 至少标明影响的是 runtime / contract / workflow / state-sync / wording 中的哪一层 | benchmark A4 |
| **minimal_reproducer** | 独立段落，给出可复制的最小复现步骤；若不可复现，说明原因与替代证据路径 | benchmark A2 |
| **expected** | 描述 contract / behavior 层面应该发生什么，不混修复建议 | benchmark A2 |
| **actual** | 描述实际发生了什么，不混诊断推测 | benchmark A2 |
| **evidence_refs** | 引用至少一条 `review/*.md` 中的具体 evidence 段落路径 | benchmark A3 |
| **evidence_excerpt** | 正文内仅保留最小摘录（≤10 行），完整证据仍在 review 文档 | benchmark A3 |
| **environment** | 按类型分层：runtime/worker/transport 类问题必须带版本与执行环境；纯文档/contract/wording 类只需列出受影响文档面，版本边界可省略 | benchmark A5 |
| **promotion_reason** | 说明命中了哪条 T1-T4 触发条件 | 本 contract |
| **root_cause_hypothesis** | （可选）必须标注 `basis` 与 `confidence`（high/medium/low），禁止无依据断言 | benchmark A6 |
| **non_goals** | 显式声明当前不处理什么，防止把修复切片拉宽 | benchmark A5 |

### 当前最小分类

当前 dogfood issue 的最小分类至少应覆盖：

1. transport / credential / endpoint
2. contract drift / schema drift
3. output guard rejection
4. writeback boundary
5. wording / adoption boundary
6. workflow / state-sync gap

### 不应混入的内容

以下内容不应直接写成 issue 本体：

1. 完整 raw response 或完整运行 transcript
2. 尚未经过复核的瞬时猜测
3. 只描述“这次成功了/失败了”的 observation 本身

这些仍应留在 evidence 层。

### 当前落点规则

当前 issue 的落点应分层处理：

1. 单次观察内的局部问题，可先留在对应 `review/*.md` 中作为 issue candidate。
2. 已确认会影响下一方向的问题，应升级到 `design_docs/direction-candidates-after-phase-35.md`、方向分析文档或 Checklist backlog。
3. 只有当问题需要长期跟踪时，才应考虑进入 `issues/` 或未来组件化持久面。

## 3. Dogfood Feedback

### 定义

`dogfood feedback` 是 evidence / issue 被消化后的决策输出，用来回答：

1. 当前安全可以说什么，不能说什么。
2. 下一条 direction / planning-gate 应该往哪里走。
3. 哪些状态面需要同步，哪些 backlog 需要激活或继续保留。

它不是原始事实，而是带引用的判断结果。

### 最小输入

一个最小 feedback 对象至少应引用：

1. 相关 evidence refs
2. 已晋升 issue refs，或“当前尚无 issue promotion”的明确说明
3. 当前受影响的 authority docs 或状态面

### 最小输出

一个最小 feedback 对象至少应给出：

1. 当前 judgment wording
2. 下一方向或下一 gate 推荐
3. 需要更新的文档面
4. 明确 non-goals / do-not-mix 边界
### Feedback Packet Minimum Field Set Contract

> 来源：`review/github-issue-quality/2026-04-16-dogfood-issue-standard-benchmark.md` A5、`design_docs/dogfood-issue-promotion-feedback-packet-direction-analysis.md`。

#### Packet 最小字段

一个 feedback packet 至少应包含以下字段，才能被 direction / gate / state-sync 稳定消费：

| 字段 | 类型 | 要求 |
|------|------|------|
| **packet_id** | string | 唯一标识，格式 `fp-{date}-{seq}`；用于跨文档引用 |
| **source_issues** | list[string] | 引用产出该 packet 的 issue candidate ID / 路径；至少一条 |
| **source_evidence** | list[string] | 引用直接相关的 evidence 路径（review/*.md#section）；至少一条 |
| **judgment** | string | 当前可以安全声明的判断 wording（≤3 句话） |
| **next_step_implication** | string | 对下一方向或下一 gate 的影响陈述；必须是可操作的前进建议，不是开放疑问 |
| **affected_docs** | list[string] | 需要更新的文档面路径列表 |
| **affected_layers** | list[enum] | 受影响层：`runtime` / `contract` / `workflow` / `state-sync` / `wording` |
| **non_goals** | list[string] | 显式声明本 packet 不打算解决的内容 |
| **confidence** | enum | `high` / `medium` / `low`；标明 judgment 的置信度 |

#### 可选字段

| 字段 | 类型 | 说明 |
|------|------|------|
| **supersedes** | string | 若本 packet 替代了上一条 packet，给出被替代 packet_id |
| **blocking_issues** | list[string] | 若存在阻塞后续推进的 issue，列出其 ID |
| **raw_data_pointers** | list[string] | 完整原始数据路径（日志、transcript 等），packet 正文不应内联这些内容 |

#### Packet 非目标

以下内容不应出现在 feedback packet 中：

1. 完整 evidence 正文或完整 review 文档内容
2. 实现方案或代码片段
3. 修复建议（属于 planning-gate 或 direction 的职责）
4. 跨越多个切片的综合判断（应拆分为多个独立 packet）

### 消费者边界 Contract

> 来源：`design_docs/stages/planning-gate/2026-04-16-dogfood-issue-promotion-feedback-packet-contract.md` 目标 §4。

状态面只应消费 feedback packet 的特定层，不得向上穿透到 issue 本体或 evidence 正文：

| 消费者 | 允许消费的字段 | 禁止消费的内容 |
|--------|---------------|---------------|
| **direction-candidates** | `judgment`、`next_step_implication`、`affected_layers`、`source_issues`（仅 ID） | evidence 正文、完整 issue 描述、raw data |
| **Project Master Checklist** | `packet_id`、`judgment`（≤1 句摘要）、`affected_docs` | issue 详情、evidence 段落、任何 >2 行的 wording |
| **Global Phase Map** | `packet_id`、`affected_layers`（仅层标签） | judgment 正文、evidence、issue 内容 |
| **checkpoint (latest.md)** | `packet_id`、`judgment`、`next_step_implication`、`confidence` | evidence 正文、完整 issue 字段、raw data |
| **handoff (CURRENT.md)** | `packet_id`、`judgment`、`next_step_implication`、`affected_docs`、`non_goals` | evidence 正文、raw data、完整 issue 描述 |
| **planning-gate** | 全部 packet 字段（gate 是 packet 的主要消费者） | evidence 正文仍应通过 `source_evidence` 链接访问，不内联 |

#### 消费原则

1. **pointer-only 原则**：状态面对 evidence 和 issue 只保留 pointer（路径/ID），不复制正文。
2. **单层消费原则**：每个消费者只取 packet 的指定字段，不向上穿透到 issue 或 evidence 层获取额外信息。
3. **packet 不可变原则**：一旦 packet 写入，不可修改；若判断变化，应写新 packet 并设置 `supersedes`。
### 不应混入的内容

以下内容不应由 feedback 重复承载：

1. 完整 raw evidence 正文
2. 长篇运行日志
3. 未经过 evidence 支撑的主观建议

### 当前主落点

当前 feedback 的主要落点应为：

1. `design_docs/direction-candidates-after-phase-35.md`
2. 方向分析文档
3. planning-gate 文档
4. `design_docs/Project Master Checklist.md`
5. `design_docs/Global Phase Map and Current Position.md`
6. `.codex/checkpoints/latest.md`
7. `.codex/handoffs/*.md`

但这些文档只应保存 feedback 的摘要与 pointer，不应复制 evidence 正文。

## 4. 三类对象的关系

当前建议固定为以下单向流：

1. 先在 `review/*.md` 记录单次 dogfood observation，形成 evidence。
2. 再判断 evidence 是否足以晋升为 issue candidate。
3. 最后由 feedback 消费 evidence refs 与 issue refs，生成 direction / gate / state-sync 判断。
4. Checklist / Phase Map / checkpoint / handoff 只接 feedback 结果与引用，不回灌 evidence 正文。

若跳过这个分层，最容易出现的后果是：

1. review 文档同时承担事实、问题、决策三层，导致难以复用。
2. 状态板重复拷贝 evidence 细节，造成 authority doc 漂移。
3. 后续组件或 skill 被迫同时承担观察、问题管理、状态写回三种职责，边界过宽。

## 5. 当前文档面映射

| 文档面 | 应承载对象 | 当前职责 | 明确不承载 |
|------|-----------|----------|------------|
| `review/*.md` | Evidence 为主，Issue candidate 为辅 | 归档单次观察的事实层；可附局部问题与局部结论 | 不做全局状态板写回 |
| `design_docs/direction-candidates-after-phase-35.md` | Feedback 为主 | 汇总下一方向候选与推荐 | 不复制 raw evidence 正文 |
| 方向分析文档 | Feedback 为主，Issue 为辅 | 收口某一方向的判断、边界与风险 | 不承载单次运行证据正文 |
| planning-gate 文档 | Feedback 为主 | 把方向判断转成执行 contract | 不承载完整 raw response / writeback transcript |
| Checklist / Phase Map / checkpoint | Feedback 摘要 + pointer | 同步当前阶段、active slice、待决问题 | 不承载 evidence 本体 |
| handoff | Feedback 摘要 + pointer | 记录 safe stop、next-step contract、关键 refs | 不承载 evidence 本体或完整 issue taxonomy |
| `issues/` 或未来持久面 | Promoted issue | 长期跟踪跨切片问题 | 不承载单次观察正文 |

## 6. 未来组件或 Skill 的最小 I/O Ceiling

### 最小输入

后续若要进入组件或 skill 设计，最小输入应限定为：

1. 一条或多条 evidence refs，或其结构化摘要
2. 可选的 promoted issue refs
3. 当前 direction / gate 上下文
4. 目标输出面列表，例如 review summary、issue candidates、feedback packet

### 最小输出

最小输出应限定为 3 类：

1. `evidence bundle summary`
   - 对单次或少量观察的统一摘要，不替代 review 正文
2. `issue candidates`
   - 分类、引用 evidence refs、说明是否应 promotion
3. `feedback packet`
   - judgment、next-step recommendation、affected docs、non-goals

### 明确非目标

后续组件或 skill 明确不应默认承担：

1. 发起新的 runtime 执行或 live rerun
2. 自动修改 runtime、schema、validator 或 workflow protocol
3. 自动把全局状态板改写成 authority source
4. 取代用户在重要设计节点上的审核责任
5. 变成通用 issue tracker、数据库或 UI 系统

## 7. 当前收口判断

基于当前已经完成的 3 条相关切片，可以把现有文档角色明确区分为：

1. `review/live-payload-rerun-verification-2026-04-16.md`：evidence-heavy
2. `review/real-worker-payload-adoption-judgment-2026-04-16.md`：issue / feedback-heavy
3. `review/controlled-real-worker-payload-evidence-accumulation-2026-04-16.md`：evidence + wording feedback

本文件的作用，就是把这种“实际已经发生的角色分化”变成显式边界，为后续实现型 planning-gate 提供稳定输入。

## 8. 下一步约束

基于本文件，后续若进入新的 planning-gate，应优先只讨论：

1. 是先起 component / skill interface draft，还是先起更窄的 issue-promotion / feedback-packet contract。
2. 哪些输出仍必须保持 doc-first，而不是被自动化直接吞并。

后续明确不应直接做：

1. 把 evidence / issue / feedback 一次性做成全能组件
2. 把 review、Checklist、handoff、checkpoint 的职责混为一层
3. 在没有进一步审核前直接进入实现