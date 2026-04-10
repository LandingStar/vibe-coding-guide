# Planning Gate Candidate — PEP + Subagent 接口与实现

- Status: **CLOSED**
- Phase: 8
- Date: 2026-04-10

## 问题陈述

PEP 和 Subagent 运行时相互制约：
- PEP 需要调用子 agent → 依赖子 agent 接口
- 子 agent 需要 Contract 来明确要求 → 依赖 PDP delegation 输出
- Report 收集需要回到 PEP → 依赖 PEP 的校验能力

直接推任一方都会产生另一方的未定义引用。

## 解法：接口先行 + 依赖反转

采用三切片解耦策略：

```
Slice A: 定义接口层（Protocol/ABC）
         ├── WorkerBackend protocol   ← PEP 依赖此接口
         ├── ContractFactory          ← 纯函数：hints → Contract
         └── ReportValidator          ← 纯函数：report → schema check

Slice B: 实现纯函数模块（无循环依赖）
         ├── contract_factory.py      ← delegation_decision.contract_hints → Subagent Contract
         ├── report_validator.py      ← report dict → schema validation result
         └── tests

Slice C: 集成 PEP 真实执行 + Stub Worker
         ├── PEP executor 进化       ← 调用 WorkerBackend.execute()
         ├── StubWorkerBackend        ← 最小可测实现（返回模拟 report）
         ├── 端到端测试              ← input → PDP → PEP → contract → stub worker → report → validate
         └── write-back
```

**为什么这样切：**
1. Slice A 只定义调用协议，不实现逻辑 → 两边都能编码
2. Slice B 实现纯函数（contract 生成 + report 校验）→ 无循环依赖
3. Slice C 把 PEP 和 Stub Worker 通过接口胶合 → 端到端可测

**子 agent 真实运行时留给后续 Phase：** 本阶段只到 StubWorkerBackend，真正的子 agent 调用（LLM / subprocess / 远程）是后续实现 WorkerBackend 的具体 adapter。

## 切片计划

### Slice A — 接口定义

**范围：**
- 创建 `src/interfaces.py`
  - `WorkerBackend` Protocol：`execute(contract: dict) -> dict`（接收 Contract，返回 Report）
  - `ContractFactory` Protocol：`build(delegation_decision: dict) -> dict`（hints → Contract）
  - `ReportValidator` Protocol：`validate(report: dict) -> dict`（report → validation result）
- 测试：接口可导入，类型检查通过

**不做：**
- 不实现任何逻辑

### Slice B — 纯函数模块

**范围：**
- 创建 `src/subagent/contract_factory.py`
  - 从 delegation_decision 的 `contract_hints` 生成完整 `Subagent Contract`
  - 输出符合 `subagent-contract.schema.json`
- 创建 `src/subagent/report_validator.py`
  - 校验 report dict 是否符合 `subagent-report.schema.json`
  - 返回结构化校验结果
- 测试：contract 生成 + report 校验

**不做：**
- 不涉及 PEP
- 不涉及 Worker 调用

### Slice C — PEP 集成 + Stub Worker

**范围：**
- 创建 `src/subagent/stub_worker.py` — 实现 `WorkerBackend`，返回模拟 report
- 更新 `src/pep/executor.py` — 当 envelope 包含 `delegation_decision.delegate=true` 时：
  1. 调用 ContractFactory 生成 contract
  2. 调用 WorkerBackend.execute(contract) 获取 report
  3. 调用 ReportValidator.validate(report) 校验
  4. 将结果记录到 action_log
- 创建 `tests/test_pep_delegation.py` — 端到端测试
- write-back

**不做：**
- 不实现真正的 LLM/subprocess worker
- 不实现 Handoff 落地（留给后续 Phase）
- 不实现升级路径的通知（留给后续 Phase）

## 验证门

- [x] `pytest tests/` 全部通过 — 71 passed
- [x] Contract Factory 输出通过 `subagent-contract.schema.json` 校验
- [x] Report Validator 能正确检测不合规 report
- [x] Stub Worker 返回通过 `subagent-report.schema.json` 校验的 report
- [x] 端到端：input → PDP (delegation) → PEP → contract → stub worker → report → validate
- [x] `validate_doc_loop.py --target .` 通过

## 依赖

- `src/pdp/delegation_resolver.py`（contract_hints 来源）
- `docs/specs/subagent-contract.schema.json`
- `docs/specs/subagent-report.schema.json`
- `docs/subagent-schemas.md`（不变量来源）

## 风险

- StubWorkerBackend 只返回固定模板，不能验证复杂场景。但足以证明接口可工作。
- 真正的 Worker 实现需要后续引入。当前阶段的价值是确认接口层无缺陷。
