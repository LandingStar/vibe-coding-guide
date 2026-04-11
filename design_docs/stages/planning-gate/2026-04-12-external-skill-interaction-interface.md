# Planning Gate — External Skill Interaction Interface

- Status: `COMPLETED`
- Date: `2026-04-12`
- Owner: `GitHub Copilot`
- Scope: `general external skill interaction contract only`

## 1. Why This Slice Exists

当前仓库已经在 handoff family 上证明了几条关键语义：

- model 可在规则允许的前提下主动触发外部 skill；
- skill 在非 `blocked` 结果下可继续流转；
- slash 入口只是显式路由，不应被视为唯一调用面。

但这些语义目前仍主要散落在 handoff 特化协议、workflow 文档、`.github/skills/`、bootstrap / example 副本与安装产物中。仓库缺少一套与当前项目、单一 skill 实现和当前 handoff family 解耦的通用外部 skill 交互 contract。

用户已经确认：下一步应围绕 H 继续，而且 `authority -> shipped copies` 不应单列成新的主切片，而应作为 H 的 companion mechanism 处理。因此，本切片的目标是把已被 handoff 证明可行的经验提升为一层可复用 contract，并让 handoff family 成为首个 reference implementation。

## 2. Target Outcome

本切片完成后，应满足：

1. 仓库存在一份正式的 `external skill interaction` 最小 contract，明确 invocation、continuation、authority 与 integration 边界。
2. 当前 handoff family 会对齐到这套通用 contract，作为首个 reference implementation，而不是继续单独维护私有调用语义。
3. `authority -> shipped copies` 会以 companion drift-check / distribution rule 的形式落地，只覆盖本轮触达的 authority docs 与 shipped copies。

## 3. In Scope

- 与外部 skill 交互 contract 直接相关的 authority docs / tooling docs
- 必要的 runtime / helper / prompt / instruction surface 调整，用于暴露稳定的 external skill interaction contract
- 当前 handoff family 作为首个 reference implementation 的对齐工作
- companion drift-check / distribution rule，只覆盖本轮触达的 shipped copies
- 对应 targeted tests 与状态文档 write-back

## 4. Out of Scope

- 不实现完整 driver / adapter / 转接层长期架构
- 不一次适配所有外部 skill 家族
- 不进入 marketplace / registry / 远端分发协议
- 不把所有 shipped copies 都立即改成全自动 codegen

## 5. Validation

至少完成以下验证：

1. targeted tests 覆盖 model-initiated invocation、non-blocked continuation、non-slash 唯一入口约束，以及 companion drift-check / distribution rule。
2. authority docs 与本轮触达的 shipped copies 不出现交互 contract 漂移。
3. 相关改动文件无错误。

## 6. Risks

- 若 contract 过度抽象，容易脱离当前 handoff 经验，重新回到宽泛口号。
- 若只是给 handoff 字段换名，容易把 project-local 特例误抬升为平台 contract。
- 若先做分发一致性，再做 contract，本轮会把未稳定语义扩散到更多副本。

## 7. Exit Condition

当通用 external skill interaction contract 已正式落地、handoff family 已对齐为首个 reference implementation、companion drift-check / distribution rule 已覆盖本轮触达的 shipped copies，且 targeted validation 通过时，本切片即可停止。

## 8. Execution Results

- 已新增权威文档 `docs/external-skill-interaction.md`，把 invocation、continuation、authority 与 `authority -> shipped copies` companion mechanism 固定为平台级 contract。
- 已新增 `src/workflow/external_skill_interaction.py`，把 external skill interaction contract、reference implementation family 与 companion drift-check targets 收口为结构化 helper。
- `.codex/packs/project-local.pack.json` 与 bootstrap pack copy 现已声明 `external_skill_interaction` 规则对象；`src/workflow/instructions_generator.py` 也已新增 `External Skill Interaction Contract` section。
- `src/mcp/tools.py` 现会在 `get_info()` 与 `governance_decide()` 的 `pack_info` 中暴露结构化 `external_skill_interaction_contract`。
- official instance 已新增 `doc-loop-vibe-coding/references/external-skill-interaction.md` 并写入 `pack-manifest.json` 的 `always_on`。
- 当前 handoff family 的四个 `SKILL.md` 已统一补入 shared top-level external skill interaction contract，成为首个 reference implementation family。

## 9. Validation Results

- `get_errors`：新增 authority doc、helper、instructions / MCP 改动、pack manifests、tests 均无错误。
- `pytest tests/test_instructions_generator.py tests/test_mcp_tools.py tests/test_external_skill_interaction.py tests/test_external_skill_interaction_contract_surfaces.py tests/test_doc_loop_prompts.py -q`：`54 passed`。
- companion drift-check 已通过 targeted tests 覆盖 authority doc、official instance reference 与 handoff reference implementation files 的 shared markers 一致性。