# Direction Analysis — Dogfood Evidence / Issue / Feedback Integration

## 背景

`Controlled Real-Worker Payload Evidence Accumulation` 已完成，当前仓库已经把 `LLMWorker` 受控 payload path 的权威口径收紧到：

1. 已有 2 条独立正向 live signals。
2. raw response、final report 与 payload-derived writeback 三层证据再次同时成立。
3. 当前可以安全表述为：`受控 real-worker payload path 已具备最小可重复 dogfood 能力`。

这使下一步默认不再是继续追打同类 live rerun，而是回到更高价值的问题：此前几条 dogfood 切片里反复出现的“证据收集 → 问题归类 → 反馈整合”人工流程，是否应该先被单独抽象成一个明确方向。

同时，这个方向也直接承接了用户此前明确提出的要求：后续应把 dogfood 相关的证据收集、问题收集与问题反馈整合成一个组件或 skill，但当前应先记录并收口边界，而不是直接动手实现。

## 当前判断

当前最有价值的新工作不是继续扩大 real-worker 证据量，而是把已经重复暴露出的人工流程边界说清楚：

1. 证据收集目前散落在 review 文档、planning-gate closeout、stable-boundary wording 与 handoff/state surfaces 中。
2. 问题收集目前仍依赖人工在不同切片中提炼“是 transport 问题、contract drift、guard rejection，还是 writeback boundary failure”。
3. 反馈整合目前仍由人工把“单次 signal 的结果、下一方向候选、以及 backlog 抽象需求”重新汇总到 direction-candidates 与状态板。

因此，下一步更适合先起一条**文档边界收口**切片，而不是立即进入 skill 或组件实现。

## 候选方向

### A. doc-first boundary consolidation

做什么：

1. 先把 dogfood evidence、issue、feedback 三类对象的最小边界写清楚。
2. 明确它们分别来自哪些现有文档面，以及后续若要组件化/skill 化，最小输入输出应是什么。
3. 只定义流程抽象与边界，不直接实现新 runtime 组件、skill 或持久化结构。

为什么是现在：

1. 当前已经至少有三条连续切片暴露出这套重复人工流程：`Live Payload Rerun Verification`、`Real-Worker Payload Adoption Judgment`、`Controlled Real-Worker Payload Evidence Accumulation`。
2. 用户已经明确提出这个抽象方向，但当前还没有一份专门文档把它收口成下一条窄 gate 的边界。
3. 先做文档收口，可以避免把 skill 设计、runtime 接线、问题跟踪模型与 UI/交互方式一次性绑死。

依据：

- `review/real-worker-payload-adoption-judgment-2026-04-16.md`
- `review/controlled-real-worker-payload-evidence-accumulation-2026-04-16.md`
- `design_docs/direction-candidates-after-phase-35.md`
- `review/research-compass.md`

风险：低。

### B. component/skill interface draft directly

做什么：

1. 直接草拟一个 dogfood evidence / issue / feedback integration 组件或 skill 的接口草案。
2. 预定义输入、输出、挂接位置与最小调用方式。

为什么仍可做：

1. 它能更快把后续 planning-gate 推到“可实现”状态。
2. 若当前边界已经足够清楚，接口草案会加速后续实现切片。

为什么不应默认优先：

1. 当前还没有先把证据对象、问题对象、反馈对象与 authority docs 的关系分开。
2. 过早起接口草案，容易把设计直接锁进某一种 skill/runtime 形态。
3. 这一步很容易从“方向分析”滑向“半实现设计”，触发 scope creep。

依据：

- `design_docs/direction-candidates-after-phase-35.md`
- `review/research-compass.md`
- `design_docs/Project Master Checklist.md`

风险：中。

### C. immediate implementation slice

做什么：

1. 直接进入新组件或 skill 的实现。
2. 把 evidence capture、issue collection、feedback synthesis 接到现有运行时或工作流文档面上。

为什么当前不适合：

1. 还没有单独确认这三类对象的最小边界与 ownership。
2. 当前既可能牵扯 `review/` 文档面，也可能牵扯 `checkpoint`、`handoff`、甚至未来 issue surface；直接实现很容易过宽。
3. 这会把“方向选择”直接跳成“实现切片”，不符合当前阶段应先让用户审核设计节点的约束。

依据：

- `review/controlled-real-worker-payload-evidence-accumulation-2026-04-16.md`
- `review/research-compass.md`
- `docs/first-stable-release-boundary.md`

风险：高。

## 当前推荐

我当前倾向于优先进入 **A. doc-first boundary consolidation**。

原因：

1. 用户明确要的是“后续把这套流程收口成组件或 skill”，而不是马上绑定某个实现形态。
2. 当前最缺的是边界与对象模型，而不是代码骨架。
3. 先做文档边界收口，能把后续 planning-gate 稳定在一个很窄的设计 slice：定义 evidence / issue / feedback 的最小模型与现有文档映射。
4. 这比继续追更多同类 live rerun，更能提高后续 dogfood 的复用价值。

## 若进入下一条 planning-gate，建议边界

若你认可当前方向，下一条 planning-gate 建议只做：

1. 定义 `dogfood evidence`、`dogfood issue`、`dogfood feedback` 三类最小对象的边界与区分标准。
2. 映射它们分别落在哪些现有文档面上，哪些内容继续保留在人工文档闭环中。
3. 明确后续若组件化或 skill 化，最小输入、输出与非目标是什么。

下一条 planning-gate 明确不做：

1. 不直接实现组件或 skill。
2. 不修改 runtime 执行链。
3. 不引入新的 issue persistence 或 UI 面。
4. 不把 `HTTPWorker`、更宽 real-worker repeatability、或 stable-boundary 扩张混入同一切片。