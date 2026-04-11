# Phase 35 后续方向分析：通用外部 Skill 交互接口能力

- Date: 2026-04-12
- Baseline: Phase 35 已完成；`J. Conversation Progression Contract Stability` 与 `I. Safe-Stop Writeback Bundle` 已完成；当前仓库处于无 active planning-gate 的 safe stop。
- Trigger: 用户已确认下一主题应围绕 `H. 通用外部 Skill 交互接口能力 Slice`，但要求先做方向分析，不立即起 planning-gate。

## 1. 这份分析要回答什么

当前仓库已经证明：

- model 可以在规则允许的前提下主动触发外部 skill；
- handoff skill 在非 `blocked` 结果下可以继续流转；
- 显式 slash 入口可以保留，但它不应是唯一调用面。

这些经验已经在 handoff 相关切片中被证明可行，但它们仍主要散落在 handoff 特化协议、workflow 文档、`.github/skills/`、bootstrap / example 副本以及安装产物中，尚未收口为与当前项目、单一 skill 实现解耦的通用接口能力。

因此，这份分析的目标不是直接设计一个“万能 skill 平台”，而是把下一条窄 planning-gate 的边界压缩到足够小、足够稳：先定义一套最小的外部 skill 交互 contract，并以当前 handoff skill 族作为首个证明面。

## 2. H 真正要解决的问题

根据 [docs/plugin-model.md](docs/plugin-model.md)、[docs/subagent-management.md](docs/subagent-management.md)、[docs/subagent-schemas.md](docs/subagent-schemas.md) 与 [docs/official-instance-doc-loop.md](docs/official-instance-doc-loop.md)，H 更像是在平台层补一块“driver 与外部 skill 的交互 contract”，而不是继续追加 handoff 特例。

最小应解决 4 个问题：

1. 调用语义：何时允许 model 主动触发外部 skill，何时仍必须停在 review / approve / blocked 边界。
2. 流转语义：外部 skill 返回什么样的顶层 continuation signal，主 agent 才能知道“继续 / 停止 / 升级”。
3. authority 边界：外部 skill 可以建议什么，不能隐式扩大什么写权限、控制权与文档 owner 边界。
4. 集成语义：driver 如何以稳定方式消费外部 skill 的结果，而不把当前 handoff family 的私有字段硬编码成平台默认接口。

如果这 4 个问题不先抽象出来，后续任何新的外部 skill 都会再次复制“先在某个 skill 里特化跑通，再到处补说明”的路径，导致平台抽象持续落后于已发生的经验。

## 3. 推荐的最小 contract 形状

下一条 planning-gate 更适合把 contract 压到下面这组最小公共面，而不是一次做满 registry / adapter / marketplace：

### 3.1 Invocation Contract

- 明确 model-initiated invocation 何时允许。
- 明确 slash / 路由命令只是显式入口，不是唯一入口。
- 明确触发前置条件来自 authority docs / pack rules，而不是 skill 自己临场扩权。

### 3.2 Continuation Contract

- skill 输出应先映射成一个小而稳定的顶层 continuation signal，例如：`continue`、`blocked`、`handoff-required`、`complete` 这一类控制语义。
- skill 自身仍可保留领域化 payload，但 driver 不应依赖其私有细节来决定是否继续流转。

### 3.3 Authority Contract

- 外部 skill 的结果不能隐式改写权威文档 owner、全局状态板 owner 或 active handoff owner。
- 若需要 authority 转移，必须走 handoff / escalation 等已定义原语，而不是让普通 skill 返回值越权带走控制面。

### 3.4 Integration Contract

- 平台应有一个项目无关的 skill interaction surface；handoff family 只是首个 adapter / proof point。
- 该 surface 应允许后续 skill 提供自己的 payload schema，但共享同一套顶层 continuation / authority 边界。

## 4. 为什么 authority -> shipped copies 只能做 companion mechanism

当前用户特别要求先解释 `authority -> shipped copies` 的单源编译 / 漂移检查问题。基于当前仓库状态，我倾向把它视为 H 的 companion mechanism，而不是独立主切片，原因是：

1. 它解决的是“一致性分发”问题，不是“交互语义”问题。真正要先被固定的是通用外部 skill 交互 contract 本身。
2. 在 contract 尚未稳定前，单独做单源生成或漂移检查，只会把当前仍在变化的特化语义更快复制到更多副本上。
3. 当前已知会受 H 影响的 shipped copies 包括 authority docs 之外的 skill 文本、bootstrap / example 副本，以及安装产物；这些都应该从 H 的正式 contract 派生，而不是反过来决定 H 的边界。
4. 把 drift-check 作为 H 的 acceptance / validation 一部分更稳：它天然只校验“正式 contract 是否被正确分发”，不会把分发机制误当成平台主能力。

换句话说，`authority -> shipped copies` 更像 H 的质量护栏，而不是 H 的替代品。

## 5. 建议的下一条窄 planning-gate 边界

如果用户确认继续，下一条 planning-gate 建议只做以下范围：

1. 固定一份平台级 `external skill interaction` 最小 contract 文档。
2. 让当前 handoff family 成为该 contract 的首个 reference implementation，而不是继续单独维护特例语义。
3. 明确 driver 侧消费的顶层 continuation / authority 语义，不一次做满所有 adapter。
4. 把 `authority -> shipped copies` 收口为 companion drift-check / distribution rule，只覆盖本轮触达的 authority docs 与 shipped copies。
5. 增加 targeted tests，至少覆盖 model-initiated、blocked-only stop、非 slash 唯一路径、以及 shipped copy 与 authority contract 的一致性。

## 6. 明确不应并入本轮的内容

以下内容应继续留在 H 之外，避免 planning-gate 膨胀：

- driver / adapter / 转接层的完整长期架构
- 通用 marketplace / registry / 远端分发协议
- 所有外部 skill 家族一次性适配
- 对 runtime collaboration mode 的重新设计
- 把所有 shipped copies 都改成全自动 codegen，如果本轮还没有稳定的 authority model

## 7. 风险与设计判断

主要风险有 3 个：

1. 过度抽象：如果过早追求一个覆盖所有 skill 的“大接口”，很容易脱离当前 handoff 经验，重新回到口号式设计。
2. 特例上升：如果只把 handoff 字段换个名字就宣称“已通用化”，实际上仍是在把项目私有语义冒充平台 contract。
3. 分发先行：如果先做 drift-check / codegen，再补 contract，会把未定稿语义扩散到更多 shipped copies。

所以更稳妥的顺序应是：先定最小 contract，再定 reference implementation，最后再补 companion drift-check。

## 8. 推荐结论

基于当前仓库事实，下一步最合理的动作不是直接大规模实现，而是按这份分析起一条更窄的 H planning-gate：

- 主目标：`通用外部 Skill 交互接口能力`
- 首个证明面：当前 handoff family
- 配套机制：`authority -> shipped copies` drift-check / distribution rule
- 明确不做：driver / adapter 长期架构与全 skill 泛化

这个边界既承接了用户此前对 H 的要求，也能避免把“分发一致性”误写成另一条主实现线。

## 9. 依据文档

- [design_docs/direction-candidates-after-phase-35.md](design_docs/direction-candidates-after-phase-35.md)
- [docs/plugin-model.md](docs/plugin-model.md)
- [docs/subagent-management.md](docs/subagent-management.md)
- [docs/subagent-schemas.md](docs/subagent-schemas.md)
- [docs/official-instance-doc-loop.md](docs/official-instance-doc-loop.md)
- [review/research-compass.md](review/research-compass.md)