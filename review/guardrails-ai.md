# Guardrails AI Research

## 产品定位

Guardrails AI 聚焦在 validator / guard 的扩展体系，而不是完整 agent workflow。

## 关键机制

- Validators 用于定义输出或输入是否有效，以及失败时的行为。
- Validators 可组合成 Input Guards 和 Output Guards。
- 支持 runtime metadata。
- 支持 custom validators。
- Hub 提供 validator 分发与安装。
- 提供：
  - `guardrails hub create-validator`
  - `guardrails hub submit`
  - `guardrails hub install`
- 对复杂 validator，还提供 `validator-template` 仓库。

## 对我们最有价值的点

- validator 应该是独立扩展件，不要和 pack 主体紧耦合。
- validator 既可以轻量创建，也可以有模板工程。
- input / output guard 的拦截点应分开。

## 与我们目标的差异

- Guardrails 不负责 workflow orchestration。
- 它对 docs / handoff / phase / subagent 不关心。
- 更像一层可插拔质量控制系统。

## 对子 agent 管理的启发

间接启发为主：

- 子 agent 的输入合同和输出报告都应可挂 validator
- validator 不应该和具体 handoff 机制耦死

## 我们可吸收的设计点

- validator hub / registry 概念
- input/output 分层拦截
- validator template
- metadata-driven validation

## 当前不应直接照搬的点

- 不应把 validator 系统误当成完整治理平台
- 不应让 validator 代替 human review 和 policy decision

## 主要来源

- https://guardrailsai.com/guardrails/docs/concepts/validators
- https://github.com/guardrails-ai/guardrails
