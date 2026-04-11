# Planning Gate — Conversation Progression Contract Stability

- Status: `COMPLETED`
- Date: `2026-04-12`
- Owner: `GitHub Copilot`
- Scope: `C1/C3 conversation progression scaffolding only`

## 1. Why This Slice Exists

当前仓库已经把“未经用户显式许可不得主动终止对话”与“Phase 完成后应主动推进并提问”写进了权威规则、AGENTS、copilot instructions 与 project-local pack。

但用户刚刚再次明确指出：这条约束仍不能稳定生效，尤其是在需要用户做选择、审批或方向确认时，agent 仍可能退回到普通收尾，而不是用带有自身分析/倾向判断的提问继续推进对话。

已完成的 `2026-04-11-strict-doc-loop-runtime-enforcement.md` 也明确说明：runtime 当前不会自动审查每一轮回复是否满足推进式提问。因此，这一缺口不能再靠“重复写规则文本”解决，而要补一层更稳定的行为支架，把 C1/C3 从散落约束收口为：

- 结构化的 interaction contract
- 可复用的 prompt 操作步骤
- 可生成到 instructions 的专门 section
- MCP next-step 建议中的显式提问契约

## 2. Target Outcome

本切片完成后，应满足：

1. 正式规则明确要求：凡命中用户选择、审批、方向确认或阶段推进，agent 必须先给出分析/推荐，再以提问形式继续交流；需要结构化确认时优先使用 `askQuestions`。
2. 当前仓库与 bootstrap prompt surfaces 不再只讲“完成后 write-back”，而会明确要求“不要以终止式总结收尾，必须转入推进式提问”。
3. 生成的 instructions 不再只罗列 C1/C3 文本，而会把它们整理成独立的 `Conversation Progression Contract` section。
4. MCP `get_next_action()` / `writeback_notify()` 在 `ask_user = true` 时，会返回显式的提问交互契约，避免只给一个模糊 instruction。
5. 官方实例 pack 与回归测试会覆盖这条 conversation progression contract，避免 future drift。

## 3. In Scope

- `design_docs/tooling/Document-Driven Workflow Standard.md`
- `AGENTS.md`
- `.github/copilot-instructions.md`
- `.codex/packs/project-local.pack.json`
- `doc-loop-vibe-coding/assets/bootstrap/.codex/packs/project-local.pack.json`
- `.codex/prompts/doc-loop/*.md`
- `doc-loop-vibe-coding/assets/bootstrap/.codex/prompts/doc-loop/*.md`
- `doc-loop-vibe-coding/pack-manifest.json`
- `doc-loop-vibe-coding/references/`
- `src/workflow/instructions_generator.py`
- `src/mcp/tools.py`
- 对应 targeted tests 与必要的状态文档回写

## 4. Out of Scope

- 不实现完整的“每轮回复自动审查器”或对话内容 lint engine。
- 不修改 `check_constraints()` 的 machine-checked 边界声明。
- 不在本切片内实现 safe-stop writeback bundle。
- 不在本切片内推进通用外部 skill 接口能力或 driver adapter 层。

## 5. Validation

至少完成以下验证：

1. `tests/test_instructions_generator.py`
   - 覆盖 `Conversation Progression Contract` section 的生成。
2. `tests/test_mcp_tools.py`
   - 覆盖 `get_next_action()` / `writeback_notify()` 在 `ask_user = true` 时的 interaction contract 输出。
3. `tests/test_official_instance_e2e.py`
   - 覆盖官方实例 always_on / reference 载体已包含 conversation progression guidance。
4. 若新增或强化 prompt surface 回归，再补一条针对 prompt pack 的 targeted test。
5. 相关改动文件无静态错误。

## 6. Risks

- 若把 contract 设计得过宽，可能再次滑向“完整对话审查器”而失去切片独立性。
- 若只更新提示词不补结构化输出与测试，问题仍会退回到“文案存在但行为不稳定”。
- 若只在当前仓库生效而不补 bootstrap / official-instance 副本，后续 shipped copy 会再次漂移。

## 7. Exit Condition

当以下条件同时满足时，本切片可收口：

- C1/C3 已被收口为显式的 conversation progression contract，而不只是散落描述。
- 本地 prompt 与 bootstrap prompt 都明确要求推进式提问/`askQuestions` 交流模式。
- instructions generator 与 MCP next-step 输出都能提供可直接执行的提问支架。
- targeted tests 能防止这条 contract 在后续演进中静默失效。

## 8. Execution Results

- 已同步正式规则载体：`design_docs/tooling/Document-Driven Workflow Standard.md`、`AGENTS.md`、`.github/copilot-instructions.md` 现在都明确要求：遇到选择、审批、方向确认或下一步取舍时，先给出分析/推荐，再通过提问推进；结构化确认优先使用 `askQuestions`。
- 已同步本地与 bootstrap prompt surfaces：planning-gate / execute-by-doc / write-back 三个 prompt 现在都显式要求推进式提问收尾，而不是停在普通总结。
- 已将 C1/C3 收口为结构化 `conversation_progression` contract，并同步到当前仓库与 bootstrap 的 project-local pack。
- 已为 official-instance 新增 `doc-loop-vibe-coding/references/conversation-progression.md`，并把它加入 `pack-manifest.json` 的 always_on 列表。
- `src/workflow/instructions_generator.py` 现在会生成独立的 `Conversation Progression Contract` section；`src/mcp/tools.py` 的 `get_next_action()` 与 `writeback_notify()` 在 `ask_user = true` 时会返回显式 `interaction_contract` 与 `question_instruction`。
- 已新增/更新 targeted tests，覆盖 instructions、MCP、official-instance always_on 与本地/bootstrap prompt pack。

## 9. Validation Results

- `get_errors`：本切片涉及的 Python、JSON、Markdown 与测试文件均无错误。
- `pytest tests/test_instructions_generator.py tests/test_mcp_tools.py tests/test_doc_loop_prompts.py -q`：`46 passed`。
- 手动 Python 验证：official-instance manifest 与 merged always_on content 均已包含 `references/conversation-progression.md`。
- 未完成验证：`tests/test_official_instance_e2e.py` 在当前 Python 3.14 mingw venv 下因 `jsonschema -> rpds-py` 构建链路失败而无法收集；这是当前环境的既有限制，不是本切片引入的新回归。