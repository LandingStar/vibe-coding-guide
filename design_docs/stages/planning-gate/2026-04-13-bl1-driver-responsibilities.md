# Planning Gate — BL-1 Driver 职责定义文档

## 元信息

| 字段 | 值 |
|------|-----|
| Gate ID | 2026-04-13-bl1-driver-responsibilities |
| Scope | BL-1 纯文档任务：梳理 driver 概念并形成权威设计概述 |
| Status | **COMPLETED** |
| 来源 | `design_docs/direction-candidates-after-phase-35.md` §BL-1 |
| 前置 | `docs/external-skill-interaction.md` 已固定 skill 侧 contract，`docs/subagent-management.md` 已固定 supervisor-worker 模型 |
| 测试基线 | 823 passed, 2 skipped |

## 问题陈述

当前 driver（主 agent 对 external skill 结果的消费逻辑）的职责分散在：
- `Pipeline.process()` — 意图分类 → PDP 决策 → PEP 执行
- `GovernanceTools` (MCP) — 工具调用面分发 + session state 管理
- `InstructionsGenerator` — 静态指令注入
- `docs/external-skill-interaction.md` — skill 侧 contract（driver 侧未对称定义）
- `docs/subagent-management.md` — supervisor/worker 角色定义

缺少一份统一的"driver 是什么、driver 负责什么、driver 不负责什么"的权威设计概述。

## 目标

**做**：
1. 创建 `docs/driver-responsibilities.md` 权威设计概述
2. 定义 driver 的职责边界：输入来源、决策分发、结果消费、write-back 控制
3. 与 `external-skill-interaction.md` 形成消费方-提供方对称
4. 与 `subagent-management.md` supervisor 角色对齐
5. 标清 driver 在 runtime（Pipeline/MCP）中的体现位置

**不做**：
- 不改代码
- 不新增 adapter 注册框架（BL-2）
- 不设计多协议转接（BL-3）

## 交付物

### `docs/driver-responsibilities.md`

## 验证门

- [x] 文档定义 driver 角色、职责边界、输入来源、结果分发路径
- [x] 与 `external-skill-interaction.md` 形成消费方-提供方对称引用 — 新增 §消费方 Contract
- [x] 与 `subagent-management.md` supervisor 角色定义一致 — §Driver 与 Supervisor 的关系
- [x] 标清 driver 在 Pipeline / MCP / Instructions 中的体现位置 — §当前 Runtime 中 Driver 的体现
- [x] 无代码改动
