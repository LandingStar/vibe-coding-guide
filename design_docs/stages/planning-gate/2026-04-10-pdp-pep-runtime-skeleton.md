# Planning Gate — PDP/PEP Runtime 骨架实现

- Status: **CLOSED**
- Phase: 6
- Date: 2026-04-10

## 问题陈述

平台已完成 9 个 JSON Schema 的规格化（6 个 PDP 子决策 + 3 个 Subagent 对象），但目前：

1. 没有任何可运行的代码来驱动治理流。
2. PDP（Policy Decision Point）和 PEP（Policy Enforcement Point）只存在于文档描述。
3. 无法验证 schema 在实际流转中是否可用。
4. 端到端链路（用户输入 → intent → gate → delegation → contract → report → writeback）尚不可测试。

## 目标

实现一个最小可运行的 PDP/PEP Python 骨架，能：

- 接收结构化输入
- 产出符合 `pdp-decision-envelope.schema.json` 的决策 envelope
- 通过 PEP 执行最小动作（目前为 dry-run / log）
- 所有 I/O 均可被 JSON Schema 校验

## 技术选型

- 语言：Python 3.10+
- 依赖：仅标准库 + `jsonschema`（用于 runtime schema 校验）
- 目录：`src/` 下的平台 runtime 代码
- 测试：`tests/` 下的 pytest 用例

## 切片计划

### Slice A — PDP 核心 + Decision Envelope 输出

**范围：**
- 创建 `src/pdp/` 包
- `src/pdp/intent_classifier.py` — 最小 intent 分类器（基于规则匹配，输出符合 `intent-classification-result.schema.json`）
- `src/pdp/gate_resolver.py` — 最小 gate 决策器（基于 intent impact level，输出符合 `gate-decision-result.schema.json`）
- `src/pdp/decision_envelope.py` — envelope 组装器（将各子决策组装成符合 `pdp-decision-envelope.schema.json` 的完整 envelope）
- `tests/test_pdp_basic.py` — 基础测试：输入 → intent → gate → envelope，校验输出符合 schema
- 不实现 delegation / escalation / precedence 的 runtime（留给后续切片）

**不做：**
- 不实现 PEP 执行层（留给 Slice B）
- 不实现 delegation/escalation/precedence resolver
- 不创建 CLI 或 web 接口
- 不引入 LLM 依赖

### Slice B — PEP 执行层 + 端到端测试

**范围：**
- 创建 `src/pep/` 包
- `src/pep/executor.py` — 最小执行器（接收 envelope，根据 gate decision 判断是否执行，dry-run 模式下只记录 log）
- `src/pep/action_log.py` — 动作记录（将执行结果记录为结构化 JSON）
- `tests/test_e2e_flow.py` — 端到端测试：输入 → PDP → PEP → 验证完整链路
- 可选：delegation resolver（如果 Slice A 剩余时间充足可合并）

**不做：**
- 不实现真正的文件改写或 write-back
- 不创建 CLI 或 web 接口
- 不实现子 agent 实际调用

## 验证门

- [ ] `src/pdp/` 包可导入，无语法错误
- [ ] `pytest tests/` 全部通过
- [ ] PDP 输出的 envelope 能通过 `pdp-decision-envelope.schema.json` 校验
- [ ] PDP 输出的各子决策能通过对应独立 schema 校验
- [ ] `validate_doc_loop.py --target .` 通过
- [ ] 代码无外部 LLM 依赖

## 依赖

- `docs/core-model.md`（PDP/PEP 职责定义）
- `docs/governance-flow.md`（最小治理流转）
- `docs/specs/*.schema.json`（全部 9 个 schema）
- `docs/intent-classification.md`（11 个 intent 类型 + impact level）
- `docs/gate-decision.md`（gate-review 映射规则）

## 风险

- intent 分类器当前为规则匹配（无 LLM），覆盖范围有限。这是有意的——先验证骨架可工作，后续再引入 LLM。
- PEP 在 Slice B 中只做 dry-run，不产生真实副作用。真正的文件操作留给后续 Phase。
- `jsonschema` 库需要安装。建议在 `requirements.txt` 中声明。
