# GitHub Bug Issue Quality Benchmark For Dogfood Issue Standard

## 来源

- 仓库 / URL：
  - `cli/cli` issue `#12927` — https://github.com/cli/cli/issues/12927
  - `cli/cli` issue `#13000` — https://github.com/cli/cli/issues/13000
  - `python/cpython` issue `#148615` — https://github.com/python/cpython/issues/148615
  - `python/cpython` issue `#148606` — https://github.com/python/cpython/issues/148606
  - `kubernetes/kubernetes` issue `#138411` — https://github.com/kubernetes/kubernetes/issues/138411
  - `kubernetes/kubernetes` issue `#138391` — https://github.com/kubernetes/kubernetes/issues/138391
- 发现日期：2026-04-16
- 状态：**详细分析完成**

## 项目概述

本次评审不是为了照抄外部 issue 模板，而是为了回答一个更窄的问题：高质量 bug issue 到底提供了哪些最小信息，才能让问题从“单次观察”顺利进入 triage、修复判断与后续状态推进。

本次样本呈现出 3 种稳定风格：

1. `cli/cli`：强调可执行复现路径、受影响版本、期望/实际分离、必要时直接点出相关代码路径。
2. `python/cpython`：强调症状边界、回归范围、最小 reproducer、受影响版本/平台、可选的 root-cause hypothesis。
3. `kubernetes/kubernetes`：强调环境矩阵、操作上下文、配置样例、日志片段与最小复现步骤。

它们共同说明：优质 issue 的核心不是“写得长”，而是把问题压缩成可 triage、可归类、可复现、可引用的最小包。

## 结构化对比

| 维度 | cli/cli | python/cpython | kubernetes/kubernetes | 对本项目的含义 |
|------|---------|----------------|-----------------------|----------------|
| 标题质量 | 标题直接编码命令、症状、触发条件与后果 | 标题直接编码 API/模块与具体行为偏差 | 标题直接编码系统对象与失败结果 | issue 标题必须能让人不进正文也知道 surface + symptom |
| 问题陈述 | 先用 1 段话说明 bug 如何发生与为何危险 | 先说明行为偏差，再指出回归或语义冲突 | 先说明系统行为和恢复/重试缺失 | issue 开头必须是问题陈述，不是日志堆砌 |
| 最小复现 | 命令序列清晰，能直接复制 | bash/python reproducer 极小且自洽 | YAML、操作步骤、命令、日志组合 | issue 必须提供最小复现，不接受只给现象 |
| Expected vs Actual | 单独分节，判断门清楚 | 明确分开，避免争议 | `What happened` / `What did you expect` 模板化 | 期望/实际必须拆开，不能混写在 narrative 中 |
| 环境信息 | 只给受影响版本，保持紧凑 | 给受影响 Python 版本与 OS | 给版本、OS、CRI、插件等完整矩阵 | 环境字段应按问题类型分层，既不能缺，也不能一刀切全塞 |
| 证据使用 | 用最小代码片段和命令输出支撑论点 | 用最小 POC、错误输出、源码分支说明支撑 | 用日志、YAML、系统版本证明上下文 | issue 应引用 evidence，但不应复制完整原始证据正文 |
| 根因假设 | 可选；点到相关函数/命令路径 | 常含明确的 regression / root cause hypothesis | 偶尔弱一些，更偏 incident 描述 | 根因假设应允许但必须标注为 hypothesis，不应伪装成事实 |
| triage 友好性 | maintainer 很快能确认复现与修复方向 | maintainer 很快能确认回归窗口 | triage bot 和 SIG 依赖环境字段与分类线索 | issue 应支持分类、归属和后续动作，而不只是存档 |
| 状态推进价值 | issue 本身足以承接修复 PR | issue 本身足以承接修复讨论 | issue 本身足以承接 triage / acceptance | 我们的 issue 还必须额外服务于 feedback packet 和下一条 gate |

## 借鉴点

#### 标题必须编码问题边界

- **外部实现**：三个项目的优质 issue 标题都至少同时包含 surface 和 symptom，CLI 甚至包含触发条件与后果，如 worktree corruption。
- **本平台现状**：当前 dogfood 结果多沉淀在 review 文档，若单独提升为 issue，标题格式还没有固定。
- **差异**：我们已有文档上下文，但缺少“离开上下文仍可 triage”的标题约束。
- **可操作性**：✅ 可直接采纳
- **采纳建议**：未来 dogfood issue 标题至少采用 `surface: symptom under condition` 或 `surface — symptom` 结构，禁止“有问题了”“失败了”这类泛标题。

#### 问题陈述应先于证据堆叠

- **外部实现**：CLI、CPython、Kubernetes 都先用自然语言说明 bug 是什么、为什么是 bug，再贴命令、日志或代码片段。
- **本平台现状**：当前 review 文档里常先给 preflight / raw response / writeback，再在结尾提升判断。
- **差异**：issue 不是 review 的缩写版，它需要先给 triage-friendly problem statement。
- **可操作性**：✅ 可直接采纳
- **采纳建议**：future issue 标准里把“问题陈述”设为第一强制段，要求 3-6 句内回答症状、影响面、触发条件、当前风险。

#### 最小复现必须和 narrative 分离

- **外部实现**：CLI 用命令序列；CPython 用最小 bash/python reproducer；Kubernetes 用 YAML + 操作步骤。
- **本平台现状**：当前复现通常散落在 review 文档的执行方式和结果段。
- **差异**：我们缺少 issue 级别的“可复制最小复现”段落规范。
- **可操作性**：✅ 可直接采纳
- **采纳建议**：future issue 里要求单独 `Minimal Reproducer` 段；若问题不可直接复现，也必须说明为何暂时不可复现，以及可替代的证据路径。

#### Expected / Actual 必须硬分离

- **外部实现**：CLI 与 Kubernetes 模板化地分开期望/实际；CPython 也显式分开 expected behavior 与 actual behavior。
- **本平台现状**：当前 adoption / evidence 文档里有时通过结论段隐含 expected/actual 差异。
- **差异**：对 issue 而言，期望/实际不分离会让争议落在事实层。
- **可操作性**：✅ 可直接采纳
- **采纳建议**：future issue 标准里设为强制字段，且要求 expected 描述的是 contract / behavior，不是修复建议。

#### 环境信息应按问题类型最小化，而不是模板化堆满

- **外部实现**：CLI 只给受影响版本；CPython 给版本和 OS；Kubernetes 给完整环境矩阵，因为问题本身就是系统行为 bug。
- **本平台现状**：我们还没有 issue 级别的环境字段裁剪规则。
- **差异**：若一律要求全量环境矩阵，会让 doc-only 问题变噪；若完全不要，又会让 runtime 问题难 triage。
- **可操作性**：⚠ 需适配
- **采纳建议**：future issue 标准按类别要求环境字段：runtime / worker / transport 类问题必须带版本与执行环境；纯文档 / contract 问题只需带受影响文档面与版本边界。

#### 证据应该被引用和摘录，不该整段复制

- **外部实现**：优质 issue 只贴最小必要日志、代码分支或命令输出，而不是完整转储。
- **本平台现状**：我们已经有 review 文档保存 evidence，本身比 issue 更适合容纳完整证据。
- **差异**：如果 issue 再复制整份 review，就会把 evidence 和 issue 边界重新混掉。
- **可操作性**：✅ 可直接采纳
- **采纳建议**：future issue 必须区分 `evidence_refs` 与 `evidence_excerpt`；正文只保留最小摘录，完整证据仍放在 review 文档。

#### 根因假设应允许出现，但必须降级为可证伪假设

- **外部实现**：CLI 和 CPython 的高质量 issue 常直接指出相关函数、代码分支或回归来源，但都把它当作 fix direction / hypothesis，而不是事实结论。
- **本平台现状**：当前结论文档中偶尔混入根因判断，但没有 issue 级别的信心标记。
- **差异**：缺少 confidence 标识时，issue 容易把推测写成事实。
- **可操作性**：✅ 可直接采纳
- **采纳建议**：future issue 可选 `root_cause_hypothesis` 字段，并要求附 `basis` 或 `confidence`，禁止无依据断言。

## 差异分析

### 外部项目缺失清单

1. 外部项目的 issue 很强于 intake 和 triage，但通常不直接服务于 doc-loop、planning-gate、checkpoint 或 handoff。
2. 它们很少区分 evidence / issue / feedback 三层对象，更多是把三者压在同一 issue 中。
3. 它们不需要像本平台这样，把单个 issue 同时作为后续 direction 和状态写回的输入。

### 本平台缺失清单

1. 还没有 dogfood issue 的最小格式标准。
2. 还没有 evidence -> issue promotion threshold 的书面 contract。
3. 还没有 feedback packet 最小字段规范，导致状态面消费边界仍靠人工把握。
4. 还没有 issue 级别的标题约束、最小复现约束、期望/实际分离约束。

### 交叉验证结论

外部仓库验证了一个关键事实：优质 issue 之所以有效，不是因为它有统一模板，而是因为它稳定满足 4 个 triage 条件：

1. 能被快速归类
2. 能被快速复现或验证
3. 能被快速判断影响边界
4. 能被快速接到后续动作

对本平台而言，这 4 条还不够。我们还需要第 5 条：

5. 能被压缩成 feedback packet，供 direction-candidates、Checklist、Phase Map、checkpoint、handoff 消费。

因此，我们未来的 dogfood issue 标准不应照搬外部 issue 模板，而应在“外部 triage 友好性”之上，再加一层“doc-loop 可消费性”。

## 对未来 dogfood issue 标准的要求

基于本次样本，未来 issue 标准至少应提出以下要求：

1. **标题要求**：标题必须编码 surface + symptom；必要时再编码 trigger 或 consequence。
2. **问题陈述要求**：正文首段必须用简短 prose 说明 bug 是什么、影响什么、为什么值得提升为 issue。
3. **最小复现要求**：必须存在单独的最小复现段；若不能复现，必须说明不可复现原因与替代证据。
4. **Expected / Actual 要求**：两者必须单独成段，且 expected 描述行为 contract，不混修复建议。
5. **环境裁剪要求**：环境字段按 issue 类型分层，runtime 类问题强制带版本/环境，纯文档类问题禁止堆无关环境矩阵。
6. **证据引用要求**：必须给 `evidence_refs`，正文只允许最小摘录，不复制整份 review。
7. **分类要求**：issue 必须落到受控分类，如 transport / credential、contract drift、guard rejection、writeback boundary、wording / adoption boundary、workflow / state-sync gap。
8. **promotion 要求**：issue 必须说明为什么单条 observation 已经值得从 review 晋升出来。
9. **影响面要求**：必须说明影响的是哪一层，至少区分 runtime、contract、workflow、state-sync、wording。
10. **反馈包预留要求**：issue 必须预留能生成 feedback packet 的字段，例如 next-step implication、affected docs、non-goals。
11. **根因假设要求**：允许提供 root_cause_hypothesis，但必须标明其依据和置信度，不得伪装成事实。
12. **非目标要求**：issue 必须显式声明当前不处理什么，避免把修复切片拉宽。

## 行动项决策汇总

| # | 建议 | 决策 | 理由 | 优先级 |
|---|------|------|------|--------|
| A1 | 在当前 planning-gate 中定义 dogfood issue 的标题标准与首段问题陈述要求 | ✅ 采纳 | 这是 triage 友好性的最低门槛 | 高 |
| A2 | 在当前 planning-gate 中定义 `Minimal Reproducer` 与 `Expected vs Actual` 为 issue 强制字段 | ✅ 采纳 | 外部优质 issue 的共同核心，且直接提升 promotion 质量 | 高 |
| A3 | 在当前 planning-gate 中定义 `evidence_refs` 与 `evidence_excerpt` 分离 | ✅ 采纳 | 直接对应本平台 evidence / issue 分层需求 | 高 |
| A4 | 在当前 planning-gate 中定义 issue 分类与影响层字段 | ✅ 采纳 | 没有分类，feedback packet 很难稳定消费 | 高 |
| A5 | 在当前 planning-gate 中定义 `next-step implication`、`affected docs`、`non-goals` 三类 feedback-packet 预留字段 | ✅ 采纳 | 这是本平台相对外部 issue 模式新增的必要要求 | 高 |
| A6 | 允许 `root_cause_hypothesis`，但附 `basis` 或 `confidence` 约束 | ✅ 采纳 | 能保留高价值技术判断，同时避免把猜测写成事实 | 中 |
| A7 | 直接照搬 Kubernetes 式全量环境矩阵到所有 issue | ❌ 不采纳 | 对 doc-only / contract 类问题噪声过大，不适合本平台 | 中 |
| A8 | 在 issue 标准中引入长期持久化或外部 tracker 结构 | 📋 记录 | 当前应先收口 promotion 和 packet contract，持久面仍超 scope | 未来 |

## 当前结论

本次外部样本评审得出的最重要结论是：未来 dogfood issue 标准不应被设计成“review 的缩写版”，而应被设计成“从 observation 进入 triage 和 feedback packet 的最小问题包”。

换句话说，issue 的核心职责应是：

1. 把问题说清楚
2. 把复现和证据指针压缩清楚
3. 把影响边界和后续动作说清楚

而不是重复承载完整 evidence 正文或提前写成修复方案。