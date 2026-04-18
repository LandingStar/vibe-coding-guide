# Contract Dry-Run — Issue Promotion + Feedback Packet

## 目的

用已有 review 文档（`review/controlled-real-worker-payload-evidence-accumulation-2026-04-16.md`、`review/real-worker-payload-adoption-judgment-2026-04-16.md`）作为输入，按 `design_docs/dogfood-evidence-issue-feedback-boundary.md` 中新定义的 contract 做一次完整 dry-run，验证：

1. promotion threshold 的触发/抑制条件能否在真实 evidence 上落地。
2. issue candidate 最小字段集能否从真实 evidence 中完整提取。
3. feedback packet 最小字段集能否稳定组装。
4. contract 是否存在盲区或不可操作的字段。

## 输入 Evidence

| Evidence ID | 来源 | 核心内容 |
|-------------|------|----------|
| E1 | `review/live-payload-rerun-verification-2026-04-16.md` | LLMWorker 首次受控 live rerun 成功，三层证据同时成立 |
| E2 | `review/controlled-real-worker-payload-evidence-accumulation-2026-04-16.md` | LLMWorker 第 2 次受控 live rerun 成功，同一窄验证面 |
| E3 | `review/real-worker-payload-adoption-judgment-2026-04-16.md` | 基于 E1+E2 的 adoption judgment，定义了安全/不安全 wording |

---

## Dry-Run 1：Promotion Threshold 评估

### Symptom A：「受控 path 成功但不能外推」

**触发条件检查：**

| 条件 | 判定 | 理由 |
|------|------|------|
| T1 重复性 | ✅ 命中 | E1 和 E2 两条独立观察都显示同一现象：受控 path 成功，但 adoption judgment (E3) 明确说不能外推 |
| T2 边界影响 | ✅ 命中 | 该判断已直接影响 direction-candidates 的 C 方向（broader repeatability evidence）的优先级 |
| T3 可分类性 | ✅ 命中 | 归入 `wording / adoption boundary` |
| T4 后续切片需求 | ✅ 命中 | 下一条 gate 如果不知道当前 wording 停在哪里，会过早扩大 adoption |

**抑制条件检查：**

| 条件 | 判定 | 理由 |
|------|------|------|
| S1 单次瞬时噪声 | ❌ 不命中 | 跨 2 条独立观察 |
| S2 已被其他 issue 覆盖 | ❌ 不命中 | 当前无既有 issue 覆盖此 symptom |
| S3 缺少可引用 evidence | ❌ 不命中 | 有明确 E1、E2、E3 路径 |

**结论：应晋升为 issue candidate。**

### Symptom B：「HTTPWorker 无同类 live signal」

**触发条件检查：**

| 条件 | 判定 | 理由 |
|------|------|------|
| T1 重复性 | ⚠ 弱命中 | E3 提及不能外推到 HTTPWorker，但只在 1 条 evidence (E3) 中被提出 |
| T2 边界影响 | ✅ 命中 | 直接影响 direction B (HTTPWorker failure fallback schema alignment) |
| T3 可分类性 | ✅ 命中 | 归入 `workflow / state-sync gap` |
| T4 后续切片需求 | ✅ 命中 | 下一条切片如果默认 HTTPWorker 也有同类 signal，会绑定错误假设 |

**抑制条件检查：**

| 条件 | 判定 | 理由 |
|------|------|------|
| S1 单次瞬时噪声 | ❌ 不命中 | 这不是噪声，而是结构性缺失 |
| S2 已被其他 issue 覆盖 | ❌ 不命中 | 无既有 issue |
| S3 缺少可引用 evidence | ❌ 不命中 | E3 有明确段落 |

**结论：应晋升为 issue candidate。**

### Symptom C：「模型生成时间戳不能作为独立执行证明」

**触发条件检查：**

| 条件 | 判定 | 理由 |
|------|------|------|
| T1 重复性 | ❌ 不命中 | 仅在 E2 的 Raw Response 观察中被提到一次 |
| T2 边界影响 | ❌ 不命中 | 不影响下一 gate 边界 |
| T3 可分类性 | ⚠ 弱 | 可归入 `wording / adoption boundary`，但粒度过细 |
| T4 后续切片需求 | ❌ 不命中 | 后续切片不依赖这个具体判断 |

**抑制条件检查：**

| 条件 | 判定 | 理由 |
|------|------|------|
| S1 单次瞬时噪声 | ✅ 命中 | 只出现一次，且已在 E2 中自洽处理 |

**结论：不晋升。留在 review 文档内作为局部 observation。**

---

## Dry-Run 2：Issue Candidate 组装

### Issue Candidate IC-001

| 字段 | 内容 |
|------|------|
| **title** | `wording/adoption: 受控 LLMWorker path 成功不能外推为默认稳定面` |
| **problem_statement** | LLMWorker 受控 payload path 已获得 2 条独立正向 live signal（E1、E2），三层证据同时成立。但 adoption judgment (E3) 明确指出当前 wording 只能停在"最小可重复 dogfood 能力"，不能扩大为"默认稳定面"或"普遍可重复"。若后续 gate 或 direction 忽视这条边界，会过早扩大 adoption。 |
| **category** | `wording / adoption boundary` |
| **impact_layer** | `contract`, `wording` |
| **minimal_reproducer** | 对照 E3 §「当前不能安全表述的判断」第 1-4 点与 §「最小额外证据门」。当前 2 条 signal 仍不满足扩大 wording 的条件。 |
| **expected** | 后续 gate/direction 应延续"最小可重复 dogfood 能力"口径，不跳级。 |
| **actual** | 当前无自动机制阻止 wording 扩大，仅依赖人工判断。 |
| **evidence_refs** | `review/live-payload-rerun-verification-2026-04-16.md`, `review/controlled-real-worker-payload-evidence-accumulation-2026-04-16.md`, `review/real-worker-payload-adoption-judgment-2026-04-16.md` |
| **evidence_excerpt** | > 不能把这 2 条成功 signal 直接外推为默认稳定面。不能把当前结论扩大成"普遍可重复"。 |
| **environment** | 纯 contract/wording 问题；受影响文档面：`docs/first-stable-release-boundary.md`、direction-candidates |
| **promotion_reason** | T1（跨 E1+E2 重复）、T2（影响 direction C 优先级）、T4（下一 gate 需要知道 wording 停点） |
| **root_cause_hypothesis** | — |
| **non_goals** | 不在本 issue 中提出修复方案或新 runtime 改动 |

### Issue Candidate IC-002

| 字段 | 内容 |
|------|------|
| **title** | `workflow/gap: HTTPWorker 无受控 live signal，不能默认同类能力` |
| **problem_statement** | 当前 LLMWorker 已有 2 条正向 live signal，但 HTTPWorker 无任何同类受控 live rerun evidence。E3 明确说不能把 LLMWorker 结果外推到 HTTPWorker。若后续 direction B 或 failure fallback 工作默认 HTTPWorker 也有同类能力，会绑定错误假设。 |
| **category** | `workflow / state-sync gap` |
| **impact_layer** | `workflow`, `contract` |
| **minimal_reproducer** | 搜索所有 `review/*.md`，确认无任何 HTTPWorker 受控 live rerun 记录。 |
| **expected** | HTTPWorker 相关 direction/gate 应从零开始规划受控 live rerun，而非继承 LLMWorker 结论。 |
| **actual** | 当前 direction B 候选描述中未明确声明需要独立 live signal。 |
| **evidence_refs** | `review/real-worker-payload-adoption-judgment-2026-04-16.md` §「当前不能安全表述的判断」第 4 点 |
| **evidence_excerpt** | > 不能据此默认 `HTTPWorker` 也有同类正向 signal。 |
| **environment** | 受影响文档面：`design_docs/direction-candidates-after-phase-35.md` 方向 B、`docs/first-stable-release-boundary.md` |
| **promotion_reason** | T2（影响 direction B 边界）、T4（下一切片需要知道 HTTPWorker 起点是零） |
| **root_cause_hypothesis** | HTTPWorker 一直不在受控 dogfood 路径上，因为 Phase 27-35 focus 在 LLMWorker。basis: Phase Map 记录。confidence: high。 |
| **non_goals** | 不在本 issue 中实施 HTTPWorker live rerun |

---

## Dry-Run 3：Feedback Packet 组装

### Packet FP-2026-04-16-001

| 字段 | 内容 |
|------|------|
| **packet_id** | `fp-2026-04-16-001` |
| **source_issues** | `IC-001`, `IC-002` |
| **source_evidence** | `review/live-payload-rerun-verification-2026-04-16.md`, `review/controlled-real-worker-payload-evidence-accumulation-2026-04-16.md`, `review/real-worker-payload-adoption-judgment-2026-04-16.md` |
| **judgment** | 受控 LLMWorker path 已具备最小可重复 dogfood 能力，但 adoption wording 必须停在此层，不能外推为默认稳定面或跨 worker 能力。 |
| **next_step_implication** | 下一步应优先完成 dogfood evidence/issue/feedback 的 interface draft（当前 docs-only contract 已就位），然后视 direction B (HTTPWorker) 独立规划受控 live rerun。 |
| **affected_docs** | `docs/first-stable-release-boundary.md`, `design_docs/direction-candidates-after-phase-35.md`, `design_docs/Project Master Checklist.md` |
| **affected_layers** | `contract`, `wording`, `workflow` |
| **non_goals** | 扩大 adoption wording、实施 HTTPWorker live rerun、修改 runtime/schema |
| **confidence** | `high` |

---

## Dry-Run 结论

### Contract 可操作性判定

| 验证项 | 结果 | 说明 |
|--------|------|------|
| Promotion threshold 触发条件能否落地 | ✅ 可操作 | T1-T4 能在真实 evidence 上做出清晰判断 |
| Promotion threshold 抑制条件能否落地 | ✅ 可操作 | S1 成功抑制了 Symptom C（模型时间戳），避免过度晋升 |
| Issue candidate 最小字段能否全部填充 | ✅ 可操作 | 12 字段中 11 个完整填充，`root_cause_hypothesis` 为可选（IC-001 无需填，IC-002 有意义地填写） |
| Feedback packet 最小字段能否全部填充 | ✅ 可操作 | 9 个必选字段全部可从 issue + evidence 组合中稳定提取 |
| 消费者边界矩阵是否可执行 | ✅ 可操作 | Checklist 只需 packet_id + judgment 摘要，Phase Map 只需 affected_layers 标签，验证了 pointer-only 原则的实际效果 |

### 发现的盲区

| # | 盲区 | 严重度 | 建议 |
|---|------|--------|------|
| B1 | `environment` 字段对纯 wording/contract 类 issue 的填写指引还可以更简化——当前定义说"只需带受影响文档面与版本边界"，实操中"版本边界"概念对纯文档问题有点多余 | 低 | 后续可在 contract 中增加一句：纯 wording/contract 类 issue 的 environment 只需列出受影响文档面，版本边界可省略 |
| B2 | `packet_id` 格式 `fp-{date}-{seq}` 中的 `{seq}` 在没有持久化计数器时需要人工管理，容易冲突 | 低 | 当前 docs-only 阶段可接受，后续组件化时应自动生成 |
| B3 | Issue candidate 没有 `status` 字段（如 open/acknowledged/resolved），在纯文档场景下暂时不需要，但进入 issues/ 持久面后会需要 | 低 | 记录到 backlog，不在本轮添加 |

### 总结

Contract 在真实 evidence 上可操作。3 个盲区均为低严重度，不阻塞后续 interface draft。
