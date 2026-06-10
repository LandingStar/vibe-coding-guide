# Planning Gate — Python Reference Dependency Baseline Generator Adapter

> 日期: 2026-06-09
> 状态: COMPLETED
> 来源: `design_docs/stages/planning-gate/2026-06-08-dependency-baseline-generator-contract.md`
> 当前不改变 active gate: `design_docs/stages/planning-gate/2026-05-27-knowledge-graph-engine-progress-preview-integration.md`
> 关联权威合同: `docs/dependency-baseline-generator-contract.md`
> 关联候选实现: `tools/dependency_graph/build_baseline.py`

## Why this exists

`docs/dependency-baseline-generator-contract.md` 已经定义 adopted workspace 若选择启用
dependency impact propagation，应如何创建和维护
`tools/dependency_graph/baseline_graph.json`。

该合同故意不绑定某一种语言或工具链。它只要求 generator 可复现地产出 runtime consumer
能读取的 `nodes` / `edges`，并用 metadata 说明覆盖范围、工具链和诊断。

当前仓库已有历史 prototype：

- `tools/dependency_graph/build_baseline.py`

它能组合 AST-discovered symbols 与少量 Pylance usage 样本，产出当前仓库自己的
`baseline_graph.json`。但它仍包含几个不能直接作为参考 adapter 发布的特征：

1. `PROJECT_ROOT` 与 `URI_PREFIX` 绑定当前开发仓库。
2. Pylance usage 数据是手写样本，不是可复现采集接口。
3. include/exclude 范围只隐含为当前仓库的 `src/`。
4. 输出缺少合同推荐的 metadata、coverage、toolchain 与 diagnostics。
5. 验证门尚未固定为 adopted workspace 可执行的 smoke / fixture。

因此，本 gate 只负责把该 prototype 改造为 Python 项目的参考 adapter 之前，先收窄实现边界。

2026-06-10 用户进一步扩张目标：reference adapter 不应只覆盖“创建 baseline”，还应补齐维护、回退、修正、扩张、打包纳入等全周期内容，并在此基础上扩张至 JavaScript 语言支持。随后用户补充：Python 侧应充分利用已有 Pylance；所有操作都应配备提示词与维护指导。

因此，本 gate 现在承担一条更完整但仍窄 scope 的 adapter lifecycle foundation：

1. 先把参考 adapter 做成可被 adopted workspace 显式调用的生命周期工具。
2. 保持 MCP runtime consumer 不自动生成 baseline。
3. 让 Python 与 JavaScript 都能产出合同兼容的保守 baseline。
4. Python 侧以 AST 做符号骨架，以 Pylance usage fixture 做关系增强优先输入。
5. 将打包纳入验证，确保 adapter 随 runtime wheel 发布。
6. 将 create / refresh / validate / repair / rollback / language expansion 的提示词与维护指导纳入交付。

## Authoritative inputs

- `docs/dependency-baseline-generator-contract.md`
- `design_docs/stages/planning-gate/2026-06-08-dependency-baseline-generator-contract.md`
- `tools/dependency_graph/model.py`
- `tools/dependency_graph/query.py`
- `tools/dependency_graph/discovery.py`
- `tools/dependency_graph/aggregator.py`
- `tools/dependency_graph/build_baseline.py`
- `src/mcp/tools.py`
- `.codex/prompts/doc-loop/05-dependency-baseline.md`

## Current problem

缺少一条可执行但仍保守的 Python reference adapter 路径：

1. adopted workspace 现在知道 baseline generator 应满足什么合同，但没有最小参考实现可照着落地。
2. 当前 prototype 能证明模型可行，但它混合了“真实符号发现”和“当前仓库手写 usage 样本”，可复现性不足。
3. 如果直接把 prototype 当成标准，会把本机路径、当前仓库结构和 Pylance 手工记录一起泄漏到参考实现语义里。
4. 如果立即追求完整 Python 静态分析或语言服务器自动采集，又会把 scope 扩成大型 generator 项目。

本 gate 的第一刀应在这两者之间取窄线：先把 prototype 整理成可配置、可验证、合同兼容的 Python reference adapter。

## Candidate phase name

- `Reference Dependency Baseline Adapter Lifecycle And JavaScript Expansion`

## Scope

本 gate 第一刀处理 reference adapter 的生命周期 foundation：

1. 将当前 `build_baseline.py` 从当前仓库硬编码脚本改为薄兼容入口，并新增真实 reference adapter：
   - `--project-root`
   - `--source-root` 或可重复的 `--include`
   - `--exclude`
   - `--output`
   - 可选 `--usage-fixture`
   - `create`
   - `refresh`
   - `generate`
   - `validate`
   - `repair`
   - `rollback`
2. 输出继续兼容当前 runtime consumer：
   - 顶层必须包含 `nodes`
   - 顶层必须包含 `edges`
   - `DependencyGraph.from_json(...)` 必须可加载
3. 增加合同推荐的可选 metadata：
   - `contract`
   - `contract_version`
   - `generator_id`
   - `generator_version`
   - `created_at`
   - `workspace_root_policy`
   - `source_coverage`
   - `toolchain`
   - `diagnostics`
4. 把 Pylance usage 作为 Python reference adapter 的优先增强输入：
   - reference adapter 可以读取 `vscode_listCodeUsages`-compatible fixture
   - 没有 Pylance fixture 时仍可只产出 AST symbol nodes 与可可靠发现的基础关系
   - 无 Pylance fixture 的 Python baseline 必须在 diagnostics 中标记为关系覆盖不完整
   - 不把手写 usage 样本继续写死在 generator 主体中
5. 增加 JavaScript 保守扫描：
   - `.js` / `.mjs` / `.cjs` / `.jsx`
   - module node
   - class/function node
   - `import` / `require` module edge
   - simple `extends` inheritance edge
   - 明确不声明完整 JS/TS 调用图
6. 增加最小验证：
   - fixture workspace 或当前仓库 smoke
   - round-trip load by `DependencyGraph.from_json(...)`
   - `graph.summary()` 非异常
   - 输出不包含绝对本机路径、`.venv/`、`build/`、`node_modules/`
7. 文档化 adapter 的能力边界：
   - 它是 Python reference adapter
   - 它现在同时提供 JavaScript conservative reference support
   - 它不是跨语言标准
   - 它不保证完整调用图
   - 它不由 MCP 自动调用
8. 提供操作提示词与维护指导：
   - create
   - refresh
   - validate
   - repair
   - rollback
   - JavaScript coverage expansion

## Explicit non-goals

本 gate 第一刀明确不做：

1. 不实现跨语言 generator。
2. 不把 Pylance、Pyright、Jedi 或 Python AST 固定为平台标准。
3. 不要求 adopted workspace 默认生成 baseline。
4. 不在 `impact_analysis` / `analyze_changes` 调用时自动刷新 baseline。
5. 不追求完整 Python call graph、dynamic import、runtime monkey patch 或 decorator 语义解析。
6. 不把当前仓库已有手工 usage 样本继续作为 generator 主体的一部分。
7. 不改变 `DependencyGraph.from_json(...)` 的最小消费合同。
8. 不处理 progress graph、knowledge graph engine、Local Work Trajectory 或 VS Code preview UI。
9. 不把 JavaScript reference support 扩张成 TypeScript compiler API、Babel、SWC 或 language server integration。

## Proposed first slice

第一刀建议为 `adapter lifecycle foundation + JS conservative support`：

1. 新增 `tools/dependency_graph/reference_adapter.py` 作为真实入口。
2. 将 `tools/dependency_graph/build_baseline.py` 改为兼容 wrapper。
2. 从主脚本移除当前仓库绝对 URI 前缀。
3. 将 Pylance usage 样本移动为可选 fixture 输入，不保留在 generator 主体中。
4. 输出 metadata，但保持 `nodes` / `edges` 仍是 runtime 可消费的主体。
5. 为 reference adapter 增加 lifecycle CLI：
   - `create`
   - `refresh`
   - `generate`
   - `validate`
   - `repair`
   - `rollback`
6. 增加 JavaScript conservative scanner。
7. 为 reference adapter 增加 focused tests：
   - 参数化输出路径
   - fixture round-trip
   - metadata presence
   - path hygiene
   - no fixture graceful degradation
   - refresh backup / rollback
   - repair
   - JavaScript import / extends
8. 在 `docs/dependency-baseline-generator-contract.md` 增加 reference adapter 生命周期说明。
9. 新增 `docs/dependency-baseline-maintenance-guide.md`。
10. 新增 dependency baseline maintenance prompt，并同步 bootstrap prompt surface。
11. 在 build wheel verification 中检查 reference adapter 模块随 runtime wheel 发布。
12. 只在实现完成后再考虑是否把 reference adapter 纳入 bootstrap prompt 的可选建议，不作为默认初始化行为。

## Acceptance and validation

最小验收标准：

1. adapter 可以在非当前仓库路径下运行，至少 fixture workspace 不依赖本机绝对路径。
2. adapter 输出的 JSON 满足 `docs/dependency-baseline-generator-contract.md` 的最小 shape。
3. `DependencyGraph.from_json(...)` 可加载 adapter 输出。
4. 输出 metadata 能说明：
   - generator identity
   - include/exclude
   - source coverage
   - toolchain
   - diagnostics
5. 没有 usage fixture 时，adapter 不应失败；应输出降级 baseline 与 diagnostics。
6. 有 usage fixture 时，adapter 能产生至少一条 `references` 或等价边，并通过 smoke query。
7. 输出不得包含本机绝对路径或当前开发者私有目录。
8. MCP 缺 baseline 降级行为不变，不自动调用 adapter。
9. `create` 不覆盖已有 baseline，`refresh` 默认备份旧 baseline，`rollback` 可恢复备份。
10. `repair` 能修正路径归一化并删除缺 endpoint 的边。
11. JavaScript reference support 至少覆盖 module/class/function/import/require/simple extends。
12. Python enhanced path 应支持 `vscode_listCodeUsages`-compatible Pylance fixture，并在 metadata.toolchain 记录 `pylance-usage-fixture`。
13. baseline operations 有对应提示词和维护指导。
14. runtime wheel verification 覆盖 adapter 模块存在。

建议验证命令：

```powershell
python -m pytest tests/test_dependency_graph*.py tests/test_mcp_tools.py -q
python -m pytest tests/test_doc_loop_prompts.py -q
```

若新增独立 fixture 测试文件，应在完成后把精确命令回写到本 gate。

## Required document sync

若本 gate 第一刀进入实现并完成，应同步检查：

- `docs/dependency-baseline-generator-contract.md`
- `docs/project-adoption.md`
- `docs/README.md`
- `.codex/prompts/doc-loop/05-dependency-baseline.md`
- `doc-loop-vibe-coding/assets/bootstrap/.codex/prompts/doc-loop/05-dependency-baseline.md`
- `design_docs/stages/planning-gate/2026-06-08-dependency-baseline-generator-contract.md`
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`

## Subagent split draft

当前不建议委派子 agent。

理由：本 gate 的第一刀会触碰 generator 合同、当前 prototype 与 MCP 降级边界。主 agent 应直接维护边界，防止 reference adapter 被误扩成默认 runtime 行为。

若后续需要扩大到多语言 generator，可以另起子线；那时才适合让子 agent 分别调研 TypeScript / Python / language-server 方案。

## Stop condition

本 gate 作为 adapter lifecycle foundation，当前做到以下程度就应停下：

1. Reference adapter 的输入、输出、生命周期命令、非目标和验收门已写清。
2. 已明确旧 `build_baseline.py` 是兼容 wrapper，不再承载硬编码 prototype。
3. Python 与 JavaScript conservative support 已有 focused validation。
4. 当前 active Knowledge Graph Engine gate 未被切换或覆盖。

## Current progress

2026-06-10 已进入第一刀实现：

1. 新增 `tools/dependency_graph/reference_adapter.py`，提供 `create` / `refresh` / `generate` / `validate` / `repair` / `rollback` 生命周期 CLI。
2. `build_baseline.py` 已改为兼容 wrapper，默认委派到 `reference_adapter generate`。
3. Python support 采用 stdlib AST 保守扫描 module/class/function/Protocol/import/simple inheritance。
4. JavaScript support 采用保守 scanner 覆盖 `.js` / `.mjs` / `.cjs` / `.jsx` 的 module/class/function/import/require/simple extends。
5. Pylance usage fixture 变为 Python 关系增强优先输入；没有 fixture 时产出部分 baseline 并写入 diagnostics。
6. `docs/dependency-baseline-generator-contract.md` 已补 reference adapter 生命周期说明，并强调 Python 侧 Pylance-first relation enhancement。
7. 新增 `docs/dependency-baseline-maintenance-guide.md`，覆盖创建、刷新、验证、修正、回退、JavaScript 扩张与 write-back 要求。
8. 新增 `.codex/prompts/doc-loop/06-dependency-baseline-maintenance.md` 与 bootstrap 副本，覆盖 baseline lifecycle 操作提示词。
9. `tests/test_dependency_graph.py` 已覆盖 Python metadata、Pylance usage fixture、`vscode_listCodeUsages` fixture、JavaScript import/extends、create/refresh/generate/validate/rollback、repair 与 round-trip。
10. 已补齐 `generate` 的低层脚本命令定位，并将 create / refresh / generate / validate / repair / rollback / JavaScript expansion / Pylance fixture collection 全部纳入 prompt 与维护指导验证面。

2026-06-10 最终验证与收口：

1. `python -m pytest tests/test_dependency_graph.py tests/test_doc_loop_prompts.py tests/test_impact_coupling.py tests/test_mcp_tools.py tests/test_mcp_prompts_resources.py -q` 通过，结果为 `146 passed`。
2. `python scripts/build.py --no-isolation --skip-checks` 通过，runtime wheel verification 明确包含 `tools/dependency_graph/reference_adapter.py`。
3. `python doc-loop-vibe-coding/scripts/validate_instance_pack.py --target doc-loop-vibe-coding` 通过。
4. `python doc-loop-vibe-coding/scripts/validate_doc_loop.py --target doc-loop-vibe-coding/assets/bootstrap` 通过。
5. `pack_lock` / `pack_verify` 通过，两个 pack 均为 `ok`。
6. `git diff --check` 未发现 whitespace error，仅有 Windows LF/CRLF 提示。

本 gate 第一刀完成：reference adapter lifecycle、Python + Pylance fixture 增强路径、JavaScript conservative support、提示词/维护指导和打包纳入均已落地。后续若要继续增强，应另起窄 planning-gate，例如自动采集 Pylance usage、TypeScript/JS 语义级 adapter，或 language-neutral adapter registry。

## Next candidate after this gate

若本 gate 第一刀完成，下一条候选方向应在实现结果之后再判断：

- 若 adapter 输出稳定：将它作为可选 reference generator 写入 adoption/prompt surface。
- 若 adapter 仍依赖手工 usage fixture：继续收窄为 `Python usage fixture collection contract`，而不是直接宣称完整自动 generator。
- 若用户需要跨语言支持：另起 `Language-neutral baseline generator adapter registry`，不要在 Python reference gate 内扩 scope。
