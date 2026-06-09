# Planning Gate — Dependency Baseline Generator Contract

> 日期: 2026-06-08
> 状态: COMPLETED (docs-only first slice)
> 来源: `baseline_graph.json` 创建/维护提示词与初始化行为补齐后的后续收窄
> 当前不改变 active gate: `design_docs/stages/planning-gate/2026-05-27-knowledge-graph-engine-progress-preview-integration.md`
> 关联运行面: `src/mcp/tools.py`, `tools/dependency_graph/`, `.codex/prompts/doc-loop/05-dependency-baseline.md`

## Why this exists

当前 runtime 已有 `impact_analysis` / `analyze_changes`，并约定从目标工作区读取
`tools/dependency_graph/baseline_graph.json` 作为依赖传播快照。

上一轮已补齐运行语义：

1. 缺少 `baseline_graph.json` 是合法降级状态，不阻塞普通实现任务。
2. agent 不应在普通任务中手写或伪造 baseline。
3. 若项目确实需要结构化影响传播，应通过可复现的工作区本地生成器创建 baseline。
4. bootstrap 默认不创建 baseline。

剩余缺口是：平台尚未定义“可复现 baseline generator”应满足什么合同。若不先定义合同，后续很容易把本仓库历史 prototype `build_baseline.py` 误当成通用标准，或者让不同目标工作区各自输出不兼容的 `baseline_graph.json`。

因此，本 gate 只负责把 dependency baseline generator 的合同与最小 adapter 边界写清。

## Authoritative inputs

- `docs/project-adoption.md`
- `.codex/prompts/doc-loop/05-dependency-baseline.md`
- `doc-loop-vibe-coding/assets/bootstrap/.codex/prompts/doc-loop/05-dependency-baseline.md`
- `doc-loop-vibe-coding/assets/bootstrap/design_docs/tooling/Document-Driven Workflow Standard.md`
- `src/mcp/tools.py`
- `tools/dependency_graph/model.py`
- `tools/dependency_graph/query.py`
- `design_docs/stages/planning-gate/2026-04-15-type-dependency-graph-extraction.md`
- `design_docs/stages/planning-gate/2026-04-15-mcp-impact-coupling-tools.md`

## Current problem

`baseline_graph.json` 当前在运行时层面是可选输入，但产品层缺少一份通用生成器协议：

1. 目标工作区不知道一个合格 baseline generator 应输入什么、输出什么。
2. agent 不知道何时应创建 generator，何时只应报告缺失降级。
3. MCP 缺 baseline 的提示已经指向“工作区自己的可复现生成器”，但该生成器尚无标准合同。
4. 旧的本仓库 Python/Pylance prototype 是重要参考，但不能直接升级成所有 adopted workspace 的强制实现。

## Candidate phase name

- `Dependency Baseline Generator Contract`

## Scope

本 gate 若被激活，第一刀只处理：

1. 定义 baseline generator 的通用合同文档：
   - 输入：workspace root、include/exclude 规则、语言/工具声明、可选 changed scope
   - 输出：`tools/dependency_graph/baseline_graph.json`
   - metadata：generator id/version、created_at、source coverage、toolchain、diagnostics
   - graph shape：节点 id、节点类型、文件路径、行号、边类型、稳定排序、未知/部分覆盖表达
   - refresh trigger：何时需要刷新，何时不应刷新
   - validation：schema/round-trip/query smoke checks
2. 定义最小 adapter 边界：
   - generator 可以是 Python、TypeScript 或外部工具，但必须产出同一 baseline graph contract
   - runtime 只消费 contract，不直接依赖某个语言生成器
   - MCP 层继续保持缺失降级，不自动生成 baseline
3. 为 adopted workspace 写清初始化策略：
   - bootstrap 不创建 baseline
   - 若项目选择启用影响传播，先创建 generator planning doc 或采用已有 generator
4. 将旧 `tools/dependency_graph/build_baseline.py` 重新定位为本仓库参考实现候选，而不是平台默认实现。

## Explicit non-goals

本 gate 第一刀明确不做：

1. 不实现跨语言完整 generator。
2. 不把 Pylance / Python AST / TypeScript compiler API 固定为平台标准。
3. 不在 MCP `impact_analysis` 调用时自动生成或刷新 baseline。
4. 不改变 `DependencyGraph.from_json(...)` 的现有消费路径，除非合同文档发现必须补一个兼容字段说明。
5. 不把 `baseline_graph.json` 纳入 bootstrap 默认产物。
6. 不要求所有 adopted workspace 必须启用 dependency baseline。
7. 不处理 progress graph、knowledge graph engine 或 Local Work Trajectory 的图模型。

## Proposed first slice

第一刀建议为 docs/tests-only 或 contract-first 极小实现：

1. 新增一份权威合同文档，建议路径：
   - `docs/dependency-baseline-generator-contract.md`
2. 若需要机器校验，先新增最小 JSON Schema 或 fixture round-trip 测试；否则只做文档 + prompt/adoption 同步。
3. 在 `docs/project-adoption.md` 中从“baseline 初始化行为”链接到新合同。
4. 在 `05-dependency-baseline.md` 中补一句：创建 generator 前先遵守该合同。
5. 在 `src/mcp/tools.py` 的缺 baseline suggestion 中保留降级提示，不新增自动生成逻辑。

## Acceptance and validation

最小验收标准：

1. 合同文档明确区分：
   - runtime consumer contract
   - workspace-local generator responsibility
   - optional initialization behavior
2. 合同文档说明 `baseline_graph.json` 的最小兼容 shape，并与现有 `tools/dependency_graph/model.py` 消费语义不冲突。
3. 合同文档明确旧 `build_baseline.py` 只是参考实现候选，不是通用标准。
4. adopted workspace 的 agent 能据此判断：
   - 缺 baseline 时如何降级
   - 何时应创建 generator
   - generator 输出如何验证
5. focused validation 至少覆盖：
   - prompt/adoption 文档中能找到合同入口
   - 现有 `impact_analysis` 缺 baseline 行为不变
   - 若新增 schema/fixture，则 round-trip/query smoke test 通过

建议验证命令：

```powershell
python -m pytest tests/test_doc_loop_prompts.py tests/test_mcp_tools.py -q
python doc-loop-vibe-coding/scripts/validate_instance_pack.py --target doc-loop-vibe-coding
python doc-loop-vibe-coding/scripts/validate_doc_loop.py --target doc-loop-vibe-coding/assets/bootstrap
```

## Required document sync

若本 gate 后续被激活并完成第一刀，应同步检查：

- `docs/project-adoption.md`
- `docs/README.md`
- `.codex/prompts/doc-loop/05-dependency-baseline.md`
- `doc-loop-vibe-coding/assets/bootstrap/.codex/prompts/doc-loop/05-dependency-baseline.md`
- `doc-loop-vibe-coding/assets/bootstrap/design_docs/tooling/Document-Driven Workflow Standard.md`
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`

## Subagent split draft

当前不建议委派子 agent。

理由：本 gate 是合同边界收窄，涉及平台/adoption/runtime 三层口径，主 agent 应直接维护权威文档与最终 write-back。

## Stop condition

本 gate 作为候选 planning contract，当前做到以下程度就应停下：

1. generator contract 的问题、范围、非目标和验收门已写清。
2. 第一刀没有滑入真实 generator 实现。
3. 当前 active graph-view/release 语境未被误扩 scope。
4. 后续若用户确认进入实现，可直接按 `Proposed first slice` 开始。

## Current progress

2026-06-08 已完成第一刀：

1. 新增平台合同文档 `docs/dependency-baseline-generator-contract.md`。
2. 合同明确 runtime consumer、workspace-local generator 与 agent 的责任边界。
3. 合同固定 `baseline_graph.json` 的最小兼容 JSON 形状，并保持现有 `DependencyGraph.from_json(...)` 消费路径兼容。
4. 合同明确 bootstrap 不创建 baseline，MCP 工具不在调用时自动生成或刷新 baseline。
5. `docs/README.md`、`docs/project-adoption.md` 与两份 `05-dependency-baseline.md` 已补合同入口。
6. 当前仓库 project-local pack 已将 `docs/dependency-baseline-generator-contract.md` 纳入 on-demand 资源。
7. focused validation 已通过：`tests/test_doc_loop_prompts.py`、`tests/test_mcp_tools.py`、`tests/test_mcp_prompts_resources.py` 共 84 passed；实例/bootstrap 校验通过；当前 baseline round-trip smoke 可加载并输出 summary。

## Next candidate after this gate

若该 gate 第一刀完成，下一条候选主线应是：

- `Python reference dependency baseline generator adapter`

该后续线才考虑把当前仓库已有 `tools/dependency_graph/build_baseline.py` 改造成符合合同的参考实现，并验证它是否可作为 Python 项目的默认 adapter。
