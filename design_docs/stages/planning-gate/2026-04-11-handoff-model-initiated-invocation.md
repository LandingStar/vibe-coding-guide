# Planning Gate — Handoff Model-Initiated Invocation

- Status: `COMPLETED`
- Date: `2026-04-11`
- Owner: `GitHub Copilot`
- Scope: `handoff workflow invocation semantics only`

## 1. Why This Slice Exists

当前仓库已经回到 post-v1.0 安全停点，下一步本来应直接生成 handoff。

但用户新增了一条更窄、且直接影响 handoff 执行语义的要求：

- handoff 的构建应当可以由 model 主动调用
- 其他 handoff 指令在不抛 `blocked` 的前提下，也应当可以由 model 执行

这意味着在真正生成 handoff 前，需要先把 handoff 协议、workflow 文档与 skill invocation contract 收口到同一口径，避免继续保留“只有显式 slash 才能执行”的旧约束。

## 2. Target Outcome

本切片完成后，应满足：

1. 权威 handoff 协议明确：安全停点下，model 可以主动进入 handoff 分支。
2. handoff 分支中的 `generate / accept / refresh current / rebuild` 语义明确：只有 `blocked` 是自动停止条件。
3. 当前仓库的 handoff-system 文档与实际 skill 文本不再要求“必须显式 slash 调用”。
4. 官方实例 bootstrap 与 example 副本不继续携带旧语义。

## 3. In Scope

- `design_docs/tooling/Session Handoff Standard.md`
- `design_docs/tooling/Document-Driven Workflow Standard.md`
- `AGENTS.md`
- `.github/copilot-instructions.md`
- `.codex/handoff-system/docs/`
- `.github/skills/project-handoff-*/`
- `.codex/handoff-system/skill/project-handoff-*/`
- 对应 bootstrap / example 副本的同步更新

## 4. Out of Scope

- 不改 handoff Python 脚本的结果结构或校验逻辑
- 不改 `blocked` 的判定标准
- 不在本切片内真正生成或轮转新的 handoff
- 不扩展到非 handoff skill 的通用自动执行框架

## 5. Validation

至少完成以下验证：

1. 核对改动后的权威协议与 skill contract 文本，确认不再保留“显式 slash 才能执行”的硬性要求。
2. 核对 workflow 文档，确认“只有 blocked 才停止”已经落到规则层。
3. 核对 bootstrap / example 副本，确认不再与权威文档冲突。

## 6. Risks

- 若表述过宽，可能让 model 绕过“安全停点”与“目标明确”前置条件。
- 若表述过窄，则仍会保留“必须显式 slash”旧语义，无法满足用户要求。

## 7. Exit Condition

当权威协议、workflow 文档、active skill 文本与 shipped 副本全部对齐到以下口径时，本切片可以收口：

- 安全停点下 handoff 可由 model 主动发起
- handoff 分支内非 `blocked` 结果允许继续执行下一步
- `blocked` 仍然是必须上抛的停止信号

## 8. Execution Results

- 已对齐权威协议、workflow 文档、active skill 文本与 shipped 副本：`design_docs/tooling/Session Handoff Standard.md`、`design_docs/tooling/Document-Driven Workflow Standard.md`、`AGENTS.md`、`.github/copilot-instructions.md`、`.codex/handoff-system/docs/`、`.github/skills/project-handoff-*/`、`.codex/handoff-system/skill/project-handoff-*/`、bootstrap / example 副本现在都使用同一口径。
- 统一后的规则为：安全停点下 model 可主动进入 handoff 分支；`generate / accept / refresh current / rebuild` 中只有 `blocked` 是停止信号；非 `blocked` 结果允许继续执行下一条直接相关步骤。
- 为保留显式入口的可发现性，skill 文本继续保留 `/project-handoff-*` 作为显式调用示例，但不再把 slash 视为唯一触发条件。

## 9. Validation Results

- 已复核关键旧表述，当前不再存在 active rule 层的“必须显式 slash 才能执行”约束；残余匹配仅是历史说明或示例性文字。
- 代表性协议文档与 skill 文本经诊断检查后无新增错误。
- `pytest .codex/handoff-system/tests/test_install_portable_handoff_kit.py -q` 已通过，确认 portable handoff kit 复制后的 shipped skill 仍保持可安装、可发现，并与新语义一致。