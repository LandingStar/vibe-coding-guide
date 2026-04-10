# Doc-Loop Prototype Authority Rereview

## 文档定位

本文件记录 `doc-loop-vibe-coding/` 相对于当前仓库权威文档的结构化 rereview 结论。

它的目标不是直接重构 prototype，而是回答：

- 当前 prototype 哪些部分已经与平台权威文档对齐
- 哪些部分仍需收紧
- 哪些部分只是 prototype choice，暂时不必上升为平台结论
- 下一条实现切片更适合落在哪个方向

本文件属于重要设计节点，结论收口前应先交由用户审核。

## 权威输入

- `docs/README.md`
- `docs/core-model.md`
- `docs/plugin-model.md`
- `docs/pack-manifest.md`
- `docs/governance-flow.md`
- `docs/review-state-machine.md`
- `docs/subagent-management.md`
- `docs/subagent-schemas.md`
- `docs/official-instance-doc-loop.md`
- `docs/project-adoption.md`
- `docs/current-prototype-status.md`
- `design_docs/stages/planning-gate/2026-04-08-doc-loop-prototype-authority-rereview.md`

## Primary Findings

### 1. 当前 prototype 最大的剩余偏差，不是对象缺失，而是实例指导文本仍偏“前平台化”

`doc-loop-vibe-coding` 已经具备：

- `Pack Manifest`
- project-local overlay pack 示例
- `Subagent Contract / Report / Handoff` 示例
- bootstrap scaffold
- validator / script

也就是说，平台对象层面已经基本接上。

当前更明显的偏差在于：

- `SKILL.md`
- `references/workflow.md`
- `references/subagent-delegation.md`
- bootstrap scaffold 中的长期说明文档

这些文本虽然已经体现 doc loop 的核心闭环，但仍主要把自己写成一套“独立工作流说明”，而不是明确站在当前平台对象之上组织实例行为。

### 2. bootstrap 与 validator 已经自洽，但它们明显编码了一套 canonical scaffold 假设

脚本层目前的特点是：

- bootstrap 能稳定产出一套统一 scaffold
- validator 能稳定验证这套 scaffold
- instance manifest、example pack 和 bootstrap pack template 已能相互校验

这说明 prototype 的实例化闭环是成立的。

但与此同时，它也意味着：

- bootstrap 是 copy-oriented，而不是 adopt-aware
- validator 验证的是“这套 canonical scaffold 是否齐全”
- 对复杂仓库或已有文档体系的 repo，仍需要 post-bootstrap alignment

这一点不是 bug，但它是明确的 prototype choice。

### 3. 当前没有发现“必须立即上升为平台核心”的高置信度原型资产

本轮没有发现哪一组 prototype 资产明显应该立刻回写到 `docs/` 成为平台核心结论。

更准确的判断是：

- 平台对象已经在 `docs/` 固定
- prototype 主要还在承担“官方实例的具体化载体”角色
- 眼下更需要的是 instance-level cleanup，而不是继续从 prototype 中抽平台结论

### 4. 子 agent 现在仍不值得引入

本轮 rereview 的阻塞点仍是：

- 复审框架归纳
- 层级判断
- 结论收口

这三件事都要求主 agent 统一裁决。

在还没有把后续 cleanup 切成独立 write scope 之前，引入子 agent 的收益不高，反而会增加结论回收成本。

## Per-Group Review

## 1. Instance Manifest And Examples

### 当前判断

- 总体状态：`已对齐，但有局部待收紧`

### 已对齐

- `pack-manifest.json`
  - 已明确声明 `official-instance`
  - 已使用 `always_on` / `on_demand`
  - 已声明 `document_types`、`intents`、`gates`、`prompts`、`validators`、`scripts`
- `examples/project-local.pack.json`
  - 已体现 project-local overlay pack 形状
- `examples/subagent-contract.worker.json`
  - 已对应 `Subagent Contract`
- `examples/subagent-report.worker.json`
  - 已对应 `Subagent Report`
- `examples/handoff.phase-close.json`
  - 已对应 `Handoff`，并显式携带 `current_gate_state`

### 待收紧

- `examples/handoff.phase-close.json`
  - 当前示例引用 `design_docs/stages/current-phase.md`
  - 但 bootstrap scaffold 并没有定义一个固定叫 `current-phase.md` 的 canonical phase 文档路径
  - 这会让 handoff 示例看起来比当前 scaffold 更“硬编码”
- 示例层目前还没有体现更明确的 `review / approve / escalation` 场景分化
  - 平台对象层已经有这些概念
  - 但实例示例仍主要覆盖最小合同面

### 层级判断

- 这一组内容应继续留在 official instance
- 目前不建议把这些 JSON 示例直接上升为平台强制格式

## 2. Bootstrap Scaffold

### 当前判断

- 总体状态：`可用的 prototype choice，仍需收紧`

### 已对齐

- scaffold 已包含：
  - `AGENTS.md`
  - 状态板与阶段图
  - `design_docs/stages/`
  - `design_docs/tooling/`
  - prompt pack
  - contract templates
  - project-local pack template
- 这与 `project-adoption.md` 中“官方实例 + 项目级 overlay pack”的采用形状是兼容的

### 待收紧

- scaffold 里的长期说明文档仍主要围绕 doc loop 自身展开
  - 对 `review-state-machine`
  - `inform / review / approve`
  - `Project Adoption`
  - escalation
  的显式表述还偏少
- bootstrap 是“复制一套默认形状”，不是“吸收目标仓库现实后生成最佳入口”
  - 本仓库本身就是一个例子
  - bootstrap 后还需要手动做 repo-local adoption alignment

### Prototype Choice

- 对于新仓库先给一套小而稳的 canonical scaffold，这个方向本身可以保留
- 但应明确承认它是 starting shape，不是 final adopted shape

### 层级判断

- 这一组应继续留在 official instance
- 不应被误认为平台级强制目录标准

## 3. Prompts / References / Skill Text

### 当前判断

- 总体状态：`需要优先收紧`

### 已对齐

- `SKILL.md` 已明确承认根目录 `docs/` 才是平台级权威来源
- `references/workflow.md` 已稳定表达：
  - doc as control surface
  - narrow planning
  - verification
  - write-back
- `references/subagent-delegation.md` 已稳定表达：
  - supervisor owns authority
  - subagent owns bounded slice
  - result must come back as structured report
- prompt pack 已稳定体现 planning -> execute -> write-back -> subagent contract 的基本顺序

### 待收紧

- 这组文本整体仍偏“前平台化”
  - 更像独立 skill 手册
  - 而不是明确站在 pack / adoption / review-state 之上的实例指导
- 当前文本里对以下平台对象的显式连接仍不足：
  - `Project Adoption`
  - `Review State Machine`
  - `inform / review / approve`
  - escalation
  - 重要设计节点需人工审核
- 这意味着：
  - 对话层面我们已经在按更高标准工作
  - 但 instance guidance 文字层还没有完全吸收这些治理语义

### 层级判断

- 这一组仍属于 official instance
- 但在下一条 cleanup 切片里，应优先作为“文本对齐清理”的目标

## 4. Validators And Scripts

### 当前判断

- 总体状态：`一致、可用，但有意保持实例级刚性`

### 已对齐

- `bootstrap_doc_loop.py`
  - 与 bootstrap assets 一致
- `validate_doc_loop.py`
  - 已能验证 target repo scaffold 与 project-local overlay pack 的基本接线
- `validate_instance_pack.py`
  - 已能验证 instance manifest、example pack 与 bootstrap template 之间的一致性

### 待收紧

- validator 目前验证的是：
  - scaffold 是否齐全
  - manifest / example / template 是否一致
- 它们还不验证：
  - review-state 的实际落地
  - 哪些动作应进入 `review` 或 `approve`
  - 重要设计节点的审核门
- 这不是实现错误，但意味着当前脚本更偏结构一致性，而非治理一致性

### Prototype Choice

- 当前脚本显式编码 canonical scaffold，这是可以接受的 prototype 选择
- 只要我们清楚它是“instance validator”，不是“platform validator”，这层边界就是清楚的

### 层级判断

- 这一组应留在 official instance implementation
- 当前不应回写进平台核心文档层

## 5. Auxiliary Metadata

### 当前判断

- 总体状态：`暂可保留为 prototype packaging`

### 说明

- `agents/openai.yaml`
  - 更接近载体层元数据
  - 它不参与平台核心对象定义
  - 也不构成当前 rereview 的主要风险点

## Cross-Cutting Conclusion

当前 `doc-loop-vibe-coding` prototype 的整体状态可以概括为：

- 对象层：大体已对齐
- 实例化层：可用且自洽
- 文本指导层：仍有明显的前平台化残留
- 脚本层：稳定，但仍是 prototype-shaped

因此，本轮更合理的后续方向不是继续抽平台对象，而是二选一：

1. `prototype cleanup`
   - 先把 prompts / references / bootstrap docs 的实例指导文字对齐到当前平台治理语义
2. `runtime/spec formalization`
   - 若更关心平台实现路径，则开始把 runtime-facing objects 继续规格化

基于本轮 rereview，我当前更偏向：

- 先做 `prototype cleanup`

原因是：

- 平台对象层已经够稳
- prototype 的剩余问题更像 guidance drift，而不是 core model 缺口
- cleanup 后再谈 runtime，会减少“实例文字层”和“平台语义层”之间的双重漂移

## 需要你审核的节点

本文件希望你重点审核：

1. 我把问题重心判断为“指导文本滞后于平台语义”，而不是“对象模型仍未成型”，这个判断是否成立
2. 我把 bootstrap/validator 判为“可保留的 prototype choice”，这个判断是否成立
3. 我建议下一条主线优先走 `prototype cleanup`，而不是 `runtime/spec formalization`，这个排序是否成立
4. 我继续判断当前还不值得引入子 agent，这个判断是否成立

## 审核记录

- 审核日期：`2026-04-09`
- 审核人：用户
- 判断 1（问题重心是指导文本滞后而非对象模型未成型）：✅ 同意
- 判断 2（bootstrap/validator 为可保留的 prototype choice）：✅ 同意
- 判断 3（下一条主线优先 prototype cleanup）：✅ 同意
- 判断 4（当前不引入子 agent）：✅ 同意

## 当前状态

- `approved`
